"""开发环境认证路由。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.cookies import 写入认证Cookie
from app.modules.auth.device_schemas import (
    设备开发者登录请求,
    设备登录响应,
    设备会话信息,
)
from app.modules.auth.device_service import 创建设备会话
from app.modules.auth.service import 开发用户登录
from app.modules.auth.sessions import 创建用户会话
from app.modules.users.schemas import 用户信息
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login/{role}", status_code=status.HTTP_204_NO_CONTENT)
async def dev_login(
    role: Literal["admin", "user"],
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """开发模式下按角色一键创建并登录账号。"""
    user = await 开发用户登录(db, role)
    session = await 创建用户会话(str(user.id))
    写入认证Cookie(response, session)


@router.post("/device/dev-login/{role}", response_model=设备登录响应, status_code=status.HTTP_201_CREATED)
async def 开发登录设备(
    role: Literal["admin", "user"],
    body: 设备开发者登录请求,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """开发模式下按角色一键创建并登录设备账号。"""
    user = await 开发用户登录(db, role)
    result = await 创建设备会话(
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
    return 设备登录响应(
        token=result.token,
        expires_at=result.session.expires_at,
        session=设备会话信息.model_validate(result.session),
        user=用户信息.model_validate(user),
    )
