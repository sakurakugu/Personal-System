"""FastAPI 依赖 – 从 JWT 提取当前用户。

此模块提供了一系列 FastAPI 依赖函数，用于：
- 验证 JWT Token 并提取当前用户
- 检查用户权限（管理员、超级管理员等）
- 处理可选的认证场景
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User, UserRole

# HTTP Bearer 认证方案，auto_error=False 表示认证失败时不自动抛出异常
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从请求头中提取并验证 JWT Token，返回当前登录用户。

    Args:
        creds: HTTP 认证凭证，包含 Bearer Token
        db: 数据库会话

    Returns:
        User: 当前登录用户对象

    Raises:
        HTTPException: 401 - 未登录或令牌无效
        HTTPException: 401 - 令牌已失效（在黑名单中）
    """
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    token = creds.credentials
    # 检查 Token 是否在黑名单中（用户已登出）
    redis = await get_redis()
    if await redis.get(f"bl:{token}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已失效")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌类型")
        user_id = UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


async def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    可选的当前用户获取。

    如果请求中包含有效的 Token，则返回用户；否则返回 None。
    适用于某些接口既支持登录用户也支持游客访问的场景。

    Args:
        creds: HTTP 认证凭证
        db: 数据库会话

    Returns:
        User | None: 当前用户或 None
    """
    if creds is None:
        return None
    try:
        return await get_current_user(creds=creds, db=db)
    except HTTPException:
        return None


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    要求用户具有管理员或以上权限。

    Args:
        user: 当前用户（由 get_current_user 注入）

    Returns:
        User: 管理员用户对象

    Raises:
        HTTPException: 403 - 需要管理员权限
    """
    if user.role not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


async def require_minimum_role(min_role: UserRole):
    """
    创建一个依赖，要求用户至少具有指定的角色等级。

    角色等级：user(1) < admin(2) < super_admin(3)

    Args:
        min_role: 最低要求的角色

    Returns:
        callable: FastAPI 依赖函数

    Example:
        @router.get("/data")
        async def get_data(user: User = Depends(require_minimum_role(UserRole.admin))):
            return data
    """
    role_hierarchy = {UserRole.user: 1, UserRole.admin: 2, UserRole.super_admin: 3}
    min_level = role_hierarchy[min_role]
    
    async def checker(user: User = Depends(get_current_user)) -> User:
        if role_hierarchy.get(user.role, 0) < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"需要 {min_role.value} 权限"
            )
        return user
    return checker


async def require_super_admin(user: User = Depends(get_current_user)) -> User:
    """
    要求用户具有超级管理员权限。

    Args:
        user: 当前用户（由 get_current_user 注入）

    Returns:
        User: 超级管理员用户对象

    Raises:
        HTTPException: 403 - 需要超级管理员权限
    """
    if user.role != UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return user
