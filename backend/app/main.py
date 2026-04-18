"""FastAPI 应用入口。

此模块是应用的入口文件，负责：
- 创建 FastAPI 应用实例
- 配置中间件（CORS、限流）
- 注册路由
- 管理应用生命周期（启动/关闭）
"""

# ruff: noqa: E402

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Awaitable, Callable, cast

# 首先配置日志（必须在导入其他模块之前）
from app.core.logger import setup_logging
from app.core.config import settings

# 设置日志：应用日志和 SQLAlchemy 日志
# SQLAlchemy 日志级别根据 DEBUG 模式自动调整
app_logger, _ = setup_logging(
    app_name="web-system",
    level="DEBUG" if settings.APP_DEBUG else "INFO",
    sqlalchemy_level="INFO" if settings.APP_DEBUG else "WARNING",
)

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

from app.api.router import register_api_routers
from app.core.database import async_session_factory, engine
from app.core.redis import close_redis
from app.core.validation import request_validation_exception_handler
from app.services.auth_cookie_service import get_session_id_from_request
from app.services.seed import seed_super_admin
from app.services.storage_service import ensure_storage_bucket_exists
from app.services.system_monitor_service import SLOW_REQUEST_THRESHOLD_MS, record_request_event

# ── 限流器 ────────────────────────────────────────────────
# 使用客户端 IP 作为限流键，默认限制 120 请求/分钟
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器。

    处理应用启动和关闭时的初始化和清理工作：
    - 启动：检查数据库连接、创建超级管理员
    - 关闭：释放数据库连接池和 Redis 连接

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 启动：检查数据库连接，表结构统一通过 Alembic 管理
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    ensure_storage_bucket_exists()
    # 生成超级管理员（如果不存在）
    async with async_session_factory() as session:
        await seed_super_admin(session)
    yield
    # 关闭：释放资源
    await engine.dispose()
    await close_redis()


# 创建 FastAPI 应用实例
app = FastAPI(
    title="Sakurakuguの小窝 API",
    version="1.0.0",
    docs_url="/api/docs",  # API 文档路径
    openapi_url="/api/openapi.json",  # OpenAPI 规范路径
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────
# 配置跨域资源共享，允许前端应用访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # 允许的源列表
    # allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,  # 允许携带凭证（Cookie）
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

# ── 限流中间件 ────────────────────────────────────────────
# 注册限流器和异常处理器
app.state.limiter = limiter
rate_limit_handler = cast(
    Callable[[Request, Exception], Response | Awaitable[Response]],
    _rate_limit_exceeded_handler,
)
validation_exception_handler = cast(
    Callable[[Request, Exception], Response | Awaitable[Response]],
    request_validation_exception_handler,
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.middleware("http")
async def csrf_protect_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """对携带登录 Session 的写操作执行 CSRF 校验。"""
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return await call_next(request)

    if get_session_id_from_request(request) is None:
        return await call_next(request)

    csrf_cookie = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        return Response(status_code=403, content='{"detail":"CSRF 校验失败"}', media_type="application/json")

    return await call_next(request)


@app.middleware("http")
async def request_monitor_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """记录最近错误和慢请求摘要。"""
    started_at = perf_counter()
    happened_at = datetime.now(timezone.utc)

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((perf_counter() - started_at) * 1000, 1)
        detail: str | None = type(exc).__name__
        if str(exc):
            detail = f"{detail}: {exc}"
        await record_request_event(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
            happened_at=happened_at,
            detail=detail,
        )
        app_logger.exception(
            "接口异常 %s %s，耗时 %.1f ms",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = round((perf_counter() - started_at) * 1000, 1)
    detail = "服务器内部错误" if response.status_code >= 500 else None
    await record_request_event(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        happened_at=happened_at,
        detail=detail,
    )

    if response.status_code >= 500:
        app_logger.error(
            "接口返回异常状态 %s %s，状态码 %s，耗时 %.1f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
    elif duration_ms >= SLOW_REQUEST_THRESHOLD_MS:
        app_logger.warning(
            "慢请求 %s %s，状态码 %s，耗时 %.1f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

    return response

# ── 注册路由 ──────────────────────────────────────────────
register_api_routers(
    app,
    include_dev_auth=settings.APP_DEBUG or settings.APP_ENV == "development",
)
