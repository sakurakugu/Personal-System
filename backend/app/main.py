"""FastAPI 应用入口。"""

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

# 导入所有模型以填充 Base.metadata
from app import models as models

# ── 限流器 ────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建表（开发方便 – 生产环境使用 Alembic）
    async with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
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
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50);")
            )
            await conn.execute(
                text("UPDATE users SET nickname = username WHERE nickname IS NULL OR nickname = '';")
            )
        await conn.run_sync(Base.metadata.create_all)
    # 播种超级管理员
    async with async_session_factory() as session:
        await seed_super_admin(session)
    yield
    # 关闭
    await engine.dispose()
    await close_redis()


app = FastAPI(
    title="Sakurakuguの小窝 API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 限流中间件 ────────────────────────────────────────────
app.state.limiter = limiter
rate_limit_handler = cast(
    Callable[[Request, Exception], Response | Awaitable[Response]],
    _rate_limit_exceeded_handler,
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

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

