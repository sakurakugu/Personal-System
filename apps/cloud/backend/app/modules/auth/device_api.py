"""设备认证路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import DeviceSessionScope, DeviceSessionType, UserDeviceSession
from app.modules.auth.device_schemas import (
    DeviceLoginRequest,
    DeviceLoginResponse,
    DeviceSessionRead,
    DeviceSessionListItemRead,
    WidgetTokenIssueRequest,
)
from app.modules.auth.device_service import (
    创建设备会话,
    列出用户设备会话,
    吊销全部用户设备会话,
    吊销设备会话,
    吊销设备会话_by_id,
    校验小工具令牌签发来源,
)
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import login_user
from app.modules.users.models import User
from app.modules.users.schemas import UserRead
from app.shared.auth.deps import 获取当前用户
from app.shared.auth.device_deps import 获取当前设备会话, 获取当前设备会话可选
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth/device", tags=["auth"])


@router.post("/login", response_model=DeviceLoginResponse, status_code=status.HTTP_201_CREATED)
async def login_device(
    body: DeviceLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """设备登录。"""
    user = await login_user(
        db,
        LoginRequest(username=body.username, password=body.password),
    )
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
    return DeviceLoginResponse(
        token=result.token,
        expires_at=result.session.expires_at,
        session=DeviceSessionRead.model_validate(result.session),
        user=UserRead.model_validate(user),
    )


@router.post("/widget-token", response_model=DeviceLoginResponse, status_code=status.HTTP_201_CREATED)
async def 签发小工具令牌(
    body: WidgetTokenIssueRequest,
    request: Request,
    current_user: User = Depends(获取当前用户),
    current_session: UserDeviceSession | None = Depends(获取当前设备会话可选),
    db: AsyncSession = Depends(get_db),
):
    """为当前用户签发桌面小工具凭证。"""
    校验小工具令牌签发来源(current_session)
    result = await 创建设备会话(
        db,
        user_id=current_user.id,
        device_name=body.device_name,
        device_type=DeviceSessionType.widget,
        scope=DeviceSessionScope.widget_basic,
        client_version=body.client_version,
        platform=body.platform,
        last_ip=request.client.host if request.client else None,
        last_user_agent=request.headers.get("user-agent"),
    )
    return DeviceLoginResponse(
        token=result.token,
        expires_at=result.session.expires_at,
        session=DeviceSessionRead.model_validate(result.session),
        user=UserRead.model_validate(current_user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_device(
    _response: Response,
    current_session: UserDeviceSession = Depends(获取当前设备会话),
):
    """当前设备登出。"""
    await 吊销设备会话(current_session)


@router.get("/sessions", response_model=list[DeviceSessionListItemRead])
async def 列出设备会话(
    current_user: User = Depends(获取当前用户),
    current_session: UserDeviceSession | None = Depends(获取当前设备会话可选),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的设备会话。"""
    sessions = await 列出用户设备会话(db, user_id=current_user.id)
    current_session_id = current_session.id if current_session is not None else None
    return [
        DeviceSessionListItemRead.model_validate(
            {
                **session.__dict__,
                "device_type": session.device_type.value,
                "scope": session.scope.value,
                "is_current": session.id == current_session_id,
            }
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除设备会话(
    session_id: UUID,
    current_user: User = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """吊销指定设备会话。"""
    await 吊销设备会话_by_id(
        db,
        target_session_id=session_id,
        current_user=current_user,
    )


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def 删除全部设备会话(
    current_user: User = Depends(获取当前用户),
    current_session: UserDeviceSession | None = Depends(获取当前设备会话可选),
    db: AsyncSession = Depends(get_db),
):
    """吊销当前用户的全部原生设备会话。"""
    await 吊销全部用户设备会话(
        db,
        current_user=current_user,
        exclude_session_id=current_session.id if current_session is not None else None,
    )
