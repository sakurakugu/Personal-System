"""应用健康检查路由。"""

from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import JSONResponse

from app.schemas.system import HealthCheckRead
from app.services.health_service import get_health_check

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckRead)
async def health_check():
    """
    获取应用健康状态。

    检查数据库、Redis 与 MinIO 连通性：
    - 全部正常时返回 200
    - 任一依赖异常时返回 503

    Returns:
        HealthCheckRead: 健康检查结果
    """
    status_code, payload = await get_health_check()
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
