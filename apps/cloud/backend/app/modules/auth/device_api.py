"""设备认证路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import UserDeviceSession
from app.modules.auth.device_schemas import (
    DeviceLoginRequest,
    DeviceLoginResponse,
    DeviceSessionRead,
    DeviceSessionListItemRead,
)
from app.modules.auth.device_service import (
    create_device_session,
    list_user_device_sessions,
    revoke_device_session,
    revoke_device_session_by_id,
)
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import login_user
from app.modules.users.models import User
from app.modules.users.schemas import UserRead
from app.shared.auth.deps import get_current_user
from app.shared.auth.device_deps import get_current_device_session, get_current_device_session_optional
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_device(
    _response: Response,
    current_session: UserDeviceSession = Depends(get_current_device_session),
):
    """当前设备登出。"""
    await revoke_device_session(current_session)


@router.get("/sessions", response_model=list[DeviceSessionListItemRead])
async def list_device_sessions(
    current_user: User = Depends(get_current_user),
    current_session: UserDeviceSession | None = Depends(get_current_device_session_optional),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的设备会话。"""
    sessions = await list_user_device_sessions(db, user_id=current_user.id)
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
async def delete_device_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """吊销指定设备会话。"""
    await revoke_device_session_by_id(
        db,
        target_session_id=session_id,
        current_user=current_user,
    )
