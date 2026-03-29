"""开发环境认证路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import TokenResponse
from app.services.auth_service import login_dev_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login/{role}", response_model=TokenResponse)
async def dev_login(role: Literal["super_admin", "admin", "user"], db: AsyncSession = Depends(get_db)):
    """
    开发模式下按角色一键创建并登录账号。

    Args:
        role: 目标角色
        db: 数据库会话

    Returns:
        TokenResponse: 访问令牌和刷新令牌
    """
    return await login_dev_user(db, role)
