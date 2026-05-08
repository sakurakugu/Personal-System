"""应用健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import JSONResponse

from app.modules.system.health import 获取健康检查
from app.modules.system.schemas import HealthCheckRead

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckRead)
async def health_check():
    """获取应用健康状态。"""
    status_code, payload = await 获取健康检查()
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
