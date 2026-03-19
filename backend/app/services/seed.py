"""Seed the super admin user on first startup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import User, UserRole


async def seed_super_admin(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.role == UserRole.super_admin).limit(1))
    if result.scalar_one_or_none():
        return
    super_admin = User(
        username=settings.SUPER_ADMIN_USERNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.super_admin,
    )
    db.add(super_admin)
    await db.commit()
    print(f"[seed] Super admin user '{settings.SUPER_ADMIN_USERNAME}' created.")
