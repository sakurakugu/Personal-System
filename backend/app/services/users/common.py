"""用户公共校验与数据处理。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.email import build_email_identity


def normalize_username_input(value: str) -> str:
    """规范化用户名输入。"""
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    return normalized


def normalize_nickname_input(value: str | None) -> str | None:
    """规范化昵称输入。"""
    if value is None:
        return None
    return value.strip() or None


def apply_settings_update(user: User, settings_data: object) -> None:
    """应用用户设置更新。"""
    if isinstance(settings_data, dict) and "show_private_articles_on_home" in settings_data:
        user.ensure_settings().show_private_articles_on_home = bool(settings_data["show_private_articles_on_home"])


async def get_user_or_404(db: AsyncSession, user_id: UUID) -> User:
    """按 ID 获取用户。"""
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return target


async def ensure_username_available(
    db: AsyncSession,
    username: str,
    *,
    exclude_user_id: UUID | None = None,
) -> None:
    """校验用户名是否可用。"""
    query = select(User).where(User.username == username)
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    exists = await db.execute(query)
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已被使用")


async def ensure_email_available(
    db: AsyncSession,
    email: object,
    *,
    current_email_identity: str | None = None,
    exclude_user_id: UUID | None = None,
) -> None:
    """校验邮箱是否可用。"""
    email_identity = build_email_identity(str(email))
    if current_email_identity is not None and email_identity == current_email_identity:
        return

    query = select(User).where(User.email_identity == email_identity)
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    exists = await db.execute(query)
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已被使用")


async def ensure_username_or_email_available_for_create(
    db: AsyncSession,
    *,
    username: str,
    email: object,
) -> None:
    """校验创建用户时用户名或邮箱是否冲突。"""
    exists = await db.execute(
        select(User).where(
            (User.username == username) | (User.email_identity == build_email_identity(str(email)))
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")
