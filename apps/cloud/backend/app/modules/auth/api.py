"""认证路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.cookies import 清除认证Cookie, 从请求获取会话ID, 写入认证Cookie
from app.modules.auth.schemas import 登录请求, 注册请求
from app.modules.auth.service import login_user, register_user
from app.modules.auth.sessions import 创建用户会话, delete_session
from app.modules.users.schemas import 用户信息
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=用户信息, status_code=status.HTTP_201_CREATED)
async def register(body: 注册请求, db: AsyncSession = Depends(get_db)):
    """注册用户。"""
    return await register_user(db, body)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
    body: 登录请求,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """用户登录。"""
    user = await login_user(db, body)
    session = await 创建用户会话(str(user.id))
    写入认证Cookie(response, session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def 登出当前用户(
    request: Request,
    response: Response,
):
    """当前用户登出。"""
    await delete_session(从请求获取会话ID(request))
    清除认证Cookie(response)
