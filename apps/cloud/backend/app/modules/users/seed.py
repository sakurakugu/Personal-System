"""启动阶段的用户初始化。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码
from app.modules.users.models import 用户, 用户角色, 构建默认用户设置
from app.shared.kernel.config import settings


async def 首次创建管理员(db: AsyncSession) -> None:
    """首次启动时自动创建管理员用户。"""
    result = await db.execute(select(用户).where(用户.role == 用户角色.admin).limit(1))
    if result.scalar_one_or_none():
        return

    admin = 用户(
        username=settings.ADMIN_USERNAME,
        nickname=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=哈希密码(settings.ADMIN_PASSWORD),
        role=用户角色.admin,
        settings=构建默认用户设置(),
    )
    db.add(admin)
    await db.commit()
    print(f"[seed] Admin user '{settings.ADMIN_USERNAME}' created.")
