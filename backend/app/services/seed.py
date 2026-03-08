"""Seed the admin user on first startup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.models import User, UserRole


async def seed_admin(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.role == UserRole.admin).limit(1))
    if result.scalar_one_or_none():
        return  # admin already exists
    admin = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.admin,
    )
    db.add(admin)
    await db.commit()
    print(f"[seed] Admin user '{settings.ADMIN_USERNAME}' created.")
