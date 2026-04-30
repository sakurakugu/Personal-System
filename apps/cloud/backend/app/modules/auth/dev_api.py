"""开发环境认证路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.cookies import write_auth_cookies
from app.modules.auth.service import login_dev_user
from app.modules.auth.sessions import create_user_session
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login/{role}", status_code=status.HTTP_204_NO_CONTENT)
async def dev_login(
    role: Literal["super_admin", "admin", "user"],
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """开发模式下按角色一键创建并登录账号。"""
    user = await login_dev_user(db, role)
    session = await create_user_session(str(user.id))
    write_auth_cookies(response, session)
