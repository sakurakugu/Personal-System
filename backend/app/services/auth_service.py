"""认证服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.system import SYSTEM_SETTING_REGISTER_ENABLED, SystemSetting
from app.models.user import User, UserRole
from app.models.user_settings import build_default_user_settings
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

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
    exists = await db.execute(select(User).where((User.username == username) | (User.email == email)))
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被使用")


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """按用户名查询用户。"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """按邮箱查询用户。"""
    result = await db.execute(select(User).where(User.email == email))
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


async def login_user(db: AsyncSession, body: LoginRequest) -> TokenResponse:
    """用户登录。"""
    user = await _get_user_by_username(db, body.username)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    return TokenResponse(
        access_token=create_access_token(str(user.id), extra={"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


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


async def login_dev_user(db: AsyncSession, role: DevLoginRole) -> TokenResponse:
    """开发模式下按角色一键登录。"""
    user = await ensure_dev_login_user(db, role)

    return TokenResponse(
        access_token=create_access_token(str(user.id), extra={"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


def build_blacklist_ttl_seconds(expire_at: datetime | None, fallback_seconds: int) -> int:
    """根据过期时间计算黑名单 TTL。"""
    if expire_at is None:
        return fallback_seconds
    remaining = int((expire_at - datetime.now(timezone.utc)).total_seconds())
    return max(1, remaining)


def _read_expire_at(payload: dict) -> datetime | None:
    """从 JWT 载荷中提取过期时间。"""
    expire_at = payload.get("exp")
    if isinstance(expire_at, (int, float)):
        return datetime.fromtimestamp(expire_at, tz=timezone.utc)
    return None


async def is_token_blacklisted(token: str) -> bool:
    """判断令牌是否已进入黑名单。"""
    redis = await get_redis()
    return bool(await redis.get(f"bl:{token}"))


async def blacklist_token(
    token: str | None,
    *,
    expected_type: Literal["access", "refresh"],
) -> None:
    """将指定类型的令牌加入黑名单。"""
    if not token:
        return

    try:
        payload = decode_token(token)
    except JWTError:
        return

    if payload.get("type") != expected_type:
        return

    fallback_seconds = (
        settings.JWT_ACCESS_EXPIRE_MINUTES * 60
        if expected_type == "access"
        else settings.JWT_REFRESH_EXPIRE_DAYS * 86400
    )
    redis = await get_redis()
    ttl = build_blacklist_ttl_seconds(_read_expire_at(payload), fallback_seconds)
    await redis.setex(f"bl:{token}", ttl, "1")


async def refresh_tokens(db: AsyncSession, body: RefreshRequest) -> TokenResponse:
    """刷新访问令牌。"""
    refresh_token = body.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    if await is_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="刷新令牌已失效")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="无效的令牌类型")
        user_id = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    await blacklist_token(refresh_token, expected_type="refresh")

    return TokenResponse(
        access_token=create_access_token(str(user.id), extra={"role": user.role.value}),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def logout(access_token: str | None, refresh_token: str | None) -> None:
    """将当前会话的 access token 和 refresh token 加入黑名单。"""
    await blacklist_token(access_token, expected_type="access")
    await blacklist_token(refresh_token, expected_type="refresh")
