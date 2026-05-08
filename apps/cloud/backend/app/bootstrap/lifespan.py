"""应用生命周期管理。"""

from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy import text

from app.core.redis import close_redis
from app.modules.system.service import 启动系统状态采样, 停止系统状态采样
from app.modules.users.seed import 首次创建超级管理员
from app.shared.db.session import async_session_factory, engine
from app.shared.storage.client import 确保存储桶存在


@asynccontextmanager
async def lifespan(_app):
    """处理应用启动和关闭时的资源初始化与清理。"""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    确保存储桶存在()

    async with async_session_factory() as session:
        await 首次创建超级管理员(session)

    await 启动系统状态采样()

    yield

    await 停止系统状态采样()
    await engine.dispose()
    await close_redis()
