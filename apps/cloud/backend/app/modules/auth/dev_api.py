"""开发环境认证路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.cookies import write_auth_cookies
from app.modules.auth.device_schemas import (
    DeviceDevLoginRequest,
    DeviceLoginResponse,
    DeviceSessionRead,
)
from app.modules.auth.device_service import create_device_session
from app.modules.auth.service import login_dev_user
from app.modules.auth.sessions import create_user_session
from app.modules.users.schemas import UserRead
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


@router.post("/device/dev-login/{role}", response_model=DeviceLoginResponse, status_code=status.HTTP_201_CREATED)
async def dev_login_device(
    role: Literal["super_admin", "admin", "user"],
    body: DeviceDevLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """开发模式下按角色一键创建并登录设备账号。"""
    user = await login_dev_user(db, role)
    result = await create_device_session(
        db,
        user_id=user.id,
        device_name=body.device_name,
        device_type=body.device_type,
        scope=body.scope,
        client_version=body.client_version,
        platform=body.platform,
        last_ip=request.client.host if request.client else None,
        last_user_agent=request.headers.get("user-agent"),
    )
    return DeviceLoginResponse(
        token=result.token,
        expires_at=result.session.expires_at,
        session=DeviceSessionRead.model_validate(result.session),
        user=UserRead.model_validate(user),
    )
