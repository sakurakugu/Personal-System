"""Seed the super admin user on first startup.

此模块提供数据库初始化功能，在应用首次启动时自动创建超级管理员账户。
如果已存在超级管理员，则跳过创建。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import User, UserRole


async def seed_super_admin(db: AsyncSession) -> None:
    """
    首次启动时自动创建超级管理员用户。

    检查数据库中是否已存在超级管理员，如果不存在则创建一个。
    使用配置文件中定义的 SUPER_ADMIN_* 配置项。

    Args:
        db: 数据库会话

    Returns:
        None

    Note:
        此函数在应用启动时通过 lifespan 上下文调用。
    """
    result = await db.execute(select(User).where(User.role == UserRole.super_admin).limit(1))
    if result.scalar_one_or_none():
        return
    super_admin = User(
        username=settings.SUPER_ADMIN_USERNAME,
        nickname=settings.SUPER_ADMIN_USERNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.super_admin,
    )
    db.add(super_admin)
    await db.commit()
    print(f"[seed] Super admin user '{settings.SUPER_ADMIN_USERNAME}' created.")
