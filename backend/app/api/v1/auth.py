"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import login_user, logout, refresh_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    注册用户。

    Args:
        body: 注册请求体
        db: 数据库会话

    Returns:
        UserRead: 创建后的用户信息
    """
    return await register_user(db, body)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录。

    Args:
        body: 登录请求体
        db: 数据库会话

    Returns:
        TokenResponse: 访问令牌和刷新令牌
    """
    return await login_user(db, body)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    刷新令牌。

    Args:
        body: 刷新请求体
        db: 数据库会话

    Returns:
        TokenResponse: 新的访问令牌和刷新令牌
    """
    return await refresh_tokens(db, body)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_current_user(
    _user: User = Depends(get_current_user),
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    当前用户登出。

    Args:
        _user: 当前登录用户
        creds: 当前 Bearer 令牌
    """
    await logout(creds)
