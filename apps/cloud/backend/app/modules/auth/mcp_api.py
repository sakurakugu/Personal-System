"""MCP 令牌签发路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import 设备会话类型
from app.modules.auth.device_schemas import MCP令牌创建请求, MCP令牌创建响应, 设备会话信息
from app.modules.auth.device_service import 创建设备会话
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth/mcp", tags=["auth"])


@router.post("/token", response_model=MCP令牌创建响应, status_code=status.HTTP_201_CREATED)
async def 创建MCP令牌(
    body: MCP令牌创建请求,
    request: Request,
    current_user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
) -> MCP令牌创建响应:
    """为当前用户创建 MCP Bearer Token。"""
    result = await 创建设备会话(
        db,
        user_id=current_user.id,
        device_name=body.device_name,
        device_type=设备会话类型.mcp,
        scope=body.scope,
        client_version=body.client_version,
        platform=body.platform,
        last_ip=request.client.host if request.client else None,
        last_user_agent=request.headers.get("user-agent"),
    )
    return MCP令牌创建响应(
        token=result.token,
        expires_at=result.session.expires_at,
        session=设备会话信息.model_validate(result.session),
    )

