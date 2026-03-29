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

# ── 导入路由 ──────────────────────────────────────────────
from app.api.health import router as health_router
from app.api.v1.admin import router as admin_router
from app.api.v1.announcements import router as announcements_router
from app.api.v1.links import router as links_router
from app.api.v1.feed import router as feed_router
from app.api.v1.moments import router as moments_router
from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.categories_tags import router as cat_tag_router
from app.api.v1.comments import router as comments_router
from app.api.v1.files import router as files_router
from app.api.v1.stats import router as stats_router
from app.api.v1.todos import router as todos_router
from app.api.v1.users import router as users_router
from app.core.database import async_session_factory, engine
from app.core.redis import close_redis
from app.services.seed import seed_super_admin
from app.core.validation import request_validation_exception_handler

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

# ── 注册路由 ──────────────────────────────────────────────
app.include_router(health_router, prefix="/api")
API_V1 = "/api/v1"
app.include_router(health_router, prefix=API_V1)
app.include_router(auth_router, prefix=API_V1)
app.include_router(calendar_router, prefix=API_V1)
app.include_router(users_router, prefix=API_V1)
app.include_router(articles_router, prefix=API_V1)
app.include_router(cat_tag_router, prefix=API_V1)
app.include_router(comments_router, prefix=API_V1)
app.include_router(todos_router, prefix=API_V1)
app.include_router(files_router, prefix=API_V1)
app.include_router(stats_router, prefix=API_V1)
app.include_router(admin_router, prefix=API_V1)
app.include_router(announcements_router, prefix=API_V1)
app.include_router(links_router, prefix=API_V1)
app.include_router(feed_router, prefix=API_V1)
app.include_router(moments_router, prefix=API_V1)

if settings.APP_DEBUG or settings.APP_ENV == "development":
    from app.api.v1.auth_dev import router as auth_dev_router

    app.include_router(auth_dev_router, prefix=API_V1)
