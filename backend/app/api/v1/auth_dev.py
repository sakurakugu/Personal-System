"""开发环境认证路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_cookie_service import write_auth_cookies
from app.services.auth_service import login_dev_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login/{role}", status_code=status.HTTP_204_NO_CONTENT)
async def dev_login(
    role: Literal["super_admin", "admin", "user"],
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    开发模式下按角色一键创建并登录账号。

    Args:
        role: 目标角色
        db: 数据库会话

    """
    tokens = await login_dev_user(db, role)
    write_auth_cookies(response, tokens)
