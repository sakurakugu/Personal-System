"""应用生命周期管理。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy import text

from app.core.redis import close_redis
from app.modules.users.seed import seed_super_admin
from app.services.storage_service import ensure_storage_bucket_exists
from app.shared.db.session import async_session_factory, engine


@asynccontextmanager
async def lifespan(_app):
    """处理应用启动和关闭时的资源初始化与清理。"""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    ensure_storage_bucket_exists()

    async with async_session_factory() as session:
        await seed_super_admin(session)

    yield

    await engine.dispose()
    await close_redis()
