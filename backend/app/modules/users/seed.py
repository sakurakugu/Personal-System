"""启动阶段的用户初始化。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User, UserRole, build_default_user_settings
from app.shared.kernel.config import settings


async def seed_super_admin(db: AsyncSession) -> None:
    """首次启动时自动创建超级管理员用户。"""
    result = await db.execute(select(User).where(User.role == UserRole.super_admin).limit(1))
    if result.scalar_one_or_none():
        return

    super_admin = User(
        username=settings.SUPER_ADMIN_USERNAME,
        nickname=settings.SUPER_ADMIN_USERNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.super_admin,
        settings=build_default_user_settings(),
    )
    db.add(super_admin)
    await db.commit()
    print(f"[seed] Super admin user '{settings.SUPER_ADMIN_USERNAME}' created.")
