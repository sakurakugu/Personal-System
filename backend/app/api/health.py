"""应用健康检查路由。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, status
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.core.database import engine
from app.core.redis import get_redis
from app.schemas.system import HealthCheckRead, HealthComponentStatus

# 创建路由器，前缀为 /health，标签为 health
router = APIRouter(prefix="/health", tags=["health"])


def _healthy_component() -> HealthComponentStatus:
    """返回健康组件状态。"""
    return HealthComponentStatus(status="healthy")


def _unhealthy_component(exc: Exception) -> HealthComponentStatus:
    """返回异常组件状态。"""
    return HealthComponentStatus(status="unhealthy", detail=type(exc).__name__)


@router.get("", response_model=HealthCheckRead)
async def health_check():
    """
    获取应用健康状态。

    检查数据库与 Redis 连通性：
    - 全部正常时返回 200
    - 任一依赖异常时返回 503

    Returns:
        HealthCheckRead: 健康检查结果
    """
    database = _healthy_component()
    redis = _healthy_component()

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        database = _unhealthy_component(exc)

    try:
        redis_client = await get_redis()
        await redis_client.ping()
    except Exception as exc:
        redis = _unhealthy_component(exc)

    overall_status = "healthy"
    status_code = status.HTTP_200_OK
    if database.status != "healthy" or redis.status != "healthy":
        overall_status = "degraded"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    payload = HealthCheckRead(
        status=overall_status,
        checked_at=datetime.now(timezone.utc),
        database=database,
        redis=redis,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
