"""共享认证依赖。"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.cookies import get_session_id_from_request
from app.modules.auth.sessions import get_session
from app.modules.users.models import User, UserRole
from app.shared.auth.device_deps import get_current_user_from_device_token_optional
from app.shared.db.session import get_db


async def get_user_from_session_id(session_id: str, db: AsyncSession) -> User:
    """根据 Session ID 解析当前用户。"""
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")

    try:
        user_id = UUID(session.user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的会话")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def get_user_from_session_id_optional(session_id: str | None, db: AsyncSession) -> User | None:
    """根据 Session ID 解析当前用户，失败时返回空。"""
    if not session_id:
        return None
    try:
        return await get_user_from_session_id(session_id, db)
    except HTTPException:
        return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Session Cookie 或设备令牌中提取当前登录用户。"""
    session_id = get_session_id_from_request(request)
    if session_id is not None:
        return await get_user_from_session_id(session_id, db)

    device_user = await get_current_user_from_device_token_optional(request, db)
    if device_user is not None:
        return device_user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """可选的当前用户获取，兼容 Session Cookie 与设备令牌。"""
    session_id = get_session_id_from_request(request)
    if session_id is not None:
        try:
            return await get_user_from_session_id(session_id, db)
        except HTTPException:
            return None

    return await get_current_user_from_device_token_optional(request, db)


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求用户具有管理员或以上权限。"""
    if user.role not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


async def require_minimum_role(min_role: UserRole):
    """创建一个依赖，要求用户至少具有指定的角色等级。"""
    role_hierarchy = {UserRole.user: 1, UserRole.admin: 2, UserRole.super_admin: 3}
    min_level = role_hierarchy[min_role]

    async def checker(user: User = Depends(get_current_user)) -> User:
        if role_hierarchy.get(user.role, 0) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {min_role.value} 权限",
            )
        return user

    return checker


async def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """要求用户具有超级管理员权限。"""
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return user
