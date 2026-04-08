"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth_cookie_service import (
    clear_auth_cookies,
    get_access_token_from_request,
    get_refresh_token_from_request,
    write_auth_cookies,
)
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


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录。

    Args:
        body: 登录请求体
        db: 数据库会话

    """
    tokens = await login_user(db, body)
    write_auth_cookies(response, tokens)


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    response: Response,
    request: Request,
    body: RefreshRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    刷新令牌。

    Args:
        body: 刷新请求体
        db: 数据库会话

    """
    resolved_body = RefreshRequest(
        refresh_token=(body.refresh_token if body is not None else None)
        or get_refresh_token_from_request(request)
    )
    tokens = await refresh_tokens(db, resolved_body)
    write_auth_cookies(response, tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_current_user(
    request: Request,
    response: Response,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    当前用户登出。

    Args:
        creds: 当前 Bearer 令牌
    """
    await logout(
        get_access_token_from_request(request, creds),
        get_refresh_token_from_request(request),
    )
    clear_auth_cookies(response)
