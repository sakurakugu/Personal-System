"""设备令牌鉴权依赖。"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import DeviceSessionScope, UserDeviceSession
from app.modules.auth.device_service import get_device_session_by_token, get_device_session_user
from app.modules.users.models import User
from app.shared.db.session import get_db


def get_bearer_token_from_request(request: Request) -> str | None:
    """从请求头提取 Bearer Token。"""
    authorization = request.headers.get("authorization")
    if not authorization:
        return None

    prefix = "bearer "
    if not authorization.lower().startswith(prefix):
        return None

    token = authorization[len(prefix):].strip()
    return token or None


async def resolve_device_session_optional(
    request: Request,
    db: AsyncSession,
) -> UserDeviceSession | None:
    """解析当前设备会话，失败时返回空。"""
    token = get_bearer_token_from_request(request)
    if token is None:
        return None

    try:
        return await get_device_session_by_token(db, token)
    except HTTPException:
        return None


async def get_current_device_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserDeviceSession:
    """获取当前设备会话。"""
    session = await resolve_device_session_optional(request, db)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供设备登录凭证")
    return session


async def get_current_device_session_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserDeviceSession | None:
    """可选获取当前设备会话。"""
    return await resolve_device_session_optional(request, db)


async def get_current_user_from_device_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """从设备令牌中提取当前用户。"""
    session = await get_current_device_session(request, db)
    return await get_device_session_user(db, session)


async def get_current_user_from_device_token_optional(
    request: Request,
    db: AsyncSession,
) -> User | None:
    """可选地从设备令牌中提取当前用户。"""
    session = await resolve_device_session_optional(request, db)
    if session is None:
        return None
    return await get_device_session_user(db, session)


def require_device_scope(*allowed_scopes: DeviceSessionScope):
    """要求当前设备会话拥有指定权限范围。"""
    allowed_scope_set = set(allowed_scopes)

    async def checker(
        current_session: UserDeviceSession = Depends(get_current_device_session),
    ) -> UserDeviceSession:
        if current_session.scope not in allowed_scope_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前设备权限不足")
        return current_session

    return checker


def has_any_device_scope(
    current_session: UserDeviceSession,
    allowed_scopes: Iterable[DeviceSessionScope],
) -> bool:
    """判断设备会话是否具有任一允许范围。"""
    return current_session.scope in set(allowed_scopes)
