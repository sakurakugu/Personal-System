"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth_cookie_service import (
    clear_auth_cookies,
    get_session_id_from_request,
    write_auth_cookies,
)
from app.services.auth_service import login_user, register_user
from app.services.session_service import create_user_session, delete_session

router = APIRouter(prefix="/auth", tags=["auth"])


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
    user = await login_user(db, body)
    session = await create_user_session(str(user.id))
    write_auth_cookies(response, session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_current_user(
    request: Request,
    response: Response,
):
    """
    当前用户登出。
    """
    await delete_session(get_session_id_from_request(request))
    clear_auth_cookies(response)
