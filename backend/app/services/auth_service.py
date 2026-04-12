"""认证服务。"""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.system import SYSTEM_SETTING_REGISTER_ENABLED, SystemSetting
from app.models.user import User, UserRole
from app.models.user_settings import build_default_user_settings
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.email import build_email_identity

DevLoginRole = Literal["super_admin", "admin", "user"]


def build_user_nickname(username: str, nickname: str | None) -> str:
    """生成用户昵称。"""
    if nickname is None:
        return username
    normalized = nickname.strip()
    return normalized or username


def is_dev_login_enabled() -> bool:
    """判断是否启用开发环境一键登录。"""
    return settings.APP_DEBUG or settings.APP_ENV == "development"


def build_dev_account_config(role: DevLoginRole) -> tuple[str, str, str, UserRole]:
    """根据角色返回开发账号配置。"""
    if role == "super_admin":
        return (
            settings.SUPER_ADMIN_USERNAME,
            settings.SUPER_ADMIN_EMAIL,
            settings.SUPER_ADMIN_PASSWORD,
            UserRole.super_admin,
        )
    if role == "admin":
        return (
            settings.DEV_ADMIN_USERNAME,
            settings.DEV_ADMIN_EMAIL,
            settings.DEV_ADMIN_PASSWORD,
            UserRole.admin,
        )
    return (
        settings.DEV_USER_USERNAME,
        settings.DEV_USER_EMAIL,
        settings.DEV_USER_PASSWORD,
        UserRole.user,
    )


async def _ensure_register_enabled(db: AsyncSession) -> None:
    """校验当前是否允许注册。"""
    setting = await db.get(SystemSetting, SYSTEM_SETTING_REGISTER_ENABLED)
    if setting is not None and setting.bool_value is False:
        raise HTTPException(status_code=403, detail="注册已关闭")


async def _ensure_unique_identity(db: AsyncSession, username: str, email: str) -> None:
    """校验用户名和邮箱未被占用。"""
    email_identity = build_email_identity(email)
    exists = await db.execute(
        select(User).where((User.username == username) | (User.email_identity == email_identity))
    )
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """按用户名查询用户。"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """按邮箱判重键查询用户。"""
    result = await db.execute(select(User).where(User.email_identity == build_email_identity(email)))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, body: RegisterRequest) -> User:
    """注册用户。"""
    await _ensure_register_enabled(db)
    await _ensure_unique_identity(db, body.username, str(body.email))
    user = User(
        username=body.username,
        nickname=build_user_nickname(body.username, body.nickname),
        email=body.email,
        password_hash=hash_password(body.password),
        settings=build_default_user_settings(),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["settings"])
    return user


async def login_user(db: AsyncSession, body: LoginRequest) -> User:
    """用户登录。"""
    user = await _get_user_by_username(db, body.username)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


async def ensure_dev_login_user(db: AsyncSession, role: DevLoginRole) -> User:
    """确保开发模式快捷登录账号存在且可用。"""
    if not is_dev_login_enabled():
        raise HTTPException(status_code=404, detail="接口不存在")

    username, email, password, user_role = build_dev_account_config(role)
    user = await _get_user_by_username(db, username)
    if user is None:
        user = await _get_user_by_email(db, email)

    password_hash = hash_password(password)
    nickname = username
    if user is None:
        user = User(
            username=username,
            nickname=nickname,
            email=email,
            password_hash=password_hash,
            role=user_role,
            is_active=True,
            settings=build_default_user_settings(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user, ["settings"])
        return user

    user.username = username
    user.nickname = nickname
    user.email = email
    user.password_hash = password_hash
    user.role = user_role
    user.is_active = True
    user.ensure_settings()
    await db.commit()
    await db.refresh(user, ["settings"])
    return user


async def login_dev_user(db: AsyncSession, role: DevLoginRole) -> User:
    """开发模式下按角色一键登录。"""
    return await ensure_dev_login_user(db, role)
