"""设备令牌鉴权依赖。"""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import DeviceSessionScope, UserDeviceSession
from app.modules.auth.device_service import 按令牌获取设备会话, 获取设备会话用户
from app.modules.users.models import User
from app.shared.db.session import get_db


def 从请求获取Bearer令牌(request: Request) -> str | None:
    """从请求头提取 Bearer Token。"""
    authorization = request.headers.get("authorization")
    if not authorization:
        return None

    prefix = "bearer "
    if not authorization.lower().startswith(prefix):
        return None

    token = authorization[len(prefix):].strip()
    return token or None


async def 解析设备会话可选(
    request: Request,
    db: AsyncSession,
) -> UserDeviceSession | None:
    """解析当前设备会话，失败时返回空。"""
    token = 从请求获取Bearer令牌(request)
    if token is None:
        return None

    try:
        return await 按令牌获取设备会话(db, token)
    except HTTPException:
        return None


async def 获取当前设备会话(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserDeviceSession:
    """获取当前设备会话。"""
    session = await 解析设备会话可选(request, db)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供设备登录凭证")
    return session


async def 获取当前设备会话可选(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserDeviceSession | None:
    """可选获取当前设备会话。"""
    return await 解析设备会话可选(request, db)


async def 从设备令牌获取当前用户(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """从设备令牌中提取当前用户。"""
    session = await 获取当前设备会话(request, db)
    return await 获取设备会话用户(db, session)


async def 从设备令牌可选获取当前用户(
    request: Request,
    db: AsyncSession,
) -> User | None:
    """可选地从设备令牌中提取当前用户。"""
    session = await 解析设备会话可选(request, db)
    if session is None:
        return None
    return await 获取设备会话用户(db, session)


def 要求设备权限范围(*allowed_scopes: DeviceSessionScope):
    """要求当前设备会话拥有指定权限范围。"""
    allowed_scope_set = set(allowed_scopes)

    async def checker(
        current_session: UserDeviceSession = Depends(获取当前设备会话),
    ) -> UserDeviceSession:
        if current_session.scope not in allowed_scope_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前设备权限不足")
        return current_session

    return checker


def 具有任一设备权限范围(
    current_session: UserDeviceSession,
    allowed_scopes: Iterable[DeviceSessionScope],
) -> bool:
    """判断设备会话是否具有任一允许范围。"""
    return current_session.scope in set(allowed_scopes)
