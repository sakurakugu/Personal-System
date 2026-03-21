"""FastAPI 应用入口。

此模块是应用的入口文件，负责：
- 创建 FastAPI 应用实例
- 配置中间件（CORS、限流）
- 注册路由
- 管理应用生命周期（启动/关闭）
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Awaitable, Callable, cast

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

# ── 导入路由 ──────────────────────────────────────────────
from app.api.v1.admin import router as admin_router
from app.api.v1.announcements import router as announcements_router
from app.api.v1.links import router as links_router
from app.api.v1.moments import router as moments_router
from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories_tags import router as cat_tag_router
from app.api.v1.comments import router as comments_router
from app.api.v1.files import router as files_router
from app.api.v1.stats import router as stats_router
from app.api.v1.todos import router as todos_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.database import async_session_factory, engine, Base
from app.core.redis import close_redis
from app.services.seed import seed_super_admin

# 导入所有模型以填充 Base.metadata（用于自动创建表）
from app import models as models

# ── 限流器 ────────────────────────────────────────────────
# 使用客户端 IP 作为限流键，默认限制 120 请求/分钟
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器。

    处理应用启动和关闭时的初始化和清理工作：
    - 启动：创建数据库表、执行兼容性迁移、创建超级管理员
    - 关闭：释放数据库连接池和 Redis 连接

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 启动：创建表（开发方便 – 生产环境使用 Alembic）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "postgresql":
            # PostgreSQL 兼容性迁移：添加 super_admin 角色值
            await conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        ALTER TYPE userrole ADD VALUE 'super_admin';
                    EXCEPTION
                        WHEN duplicate_object THEN NULL;
                    END $$;
                    """
                )
            )
            # 添加 nickname 列（如果不存在）
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50);")
            )
            # 为现有用户设置默认昵称
            await conn.execute(
                text("UPDATE users SET nickname = username WHERE nickname IS NULL OR nickname = '';")
            )
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
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# ── 注册路由 ──────────────────────────────────────────────
API_V1 = "/api/v1"
app.include_router(auth_router, prefix=API_V1)
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
app.include_router(moments_router, prefix=API_V1)
