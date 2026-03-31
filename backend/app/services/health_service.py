"""系统健康检查服务。"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import get_redis
from app.schemas.system import HealthCheckRead, HealthComponentStatus
from app.services.storage_service import StorageBucketMissingError, check_storage_health


def _healthy_component() -> HealthComponentStatus:
    """返回正常组件状态。"""
    return HealthComponentStatus(status="healthy")


def _unhealthy_component(detail: str) -> HealthComponentStatus:
    """返回异常组件状态。"""
    return HealthComponentStatus(status="unhealthy", detail=detail)


async def get_health_check() -> tuple[int, HealthCheckRead]:
    """获取系统健康检查结果。"""
    database = _healthy_component()
    redis = _healthy_component()
    minio = _healthy_component()

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        database = _unhealthy_component("数据库连接失败")

    try:
        redis_client = await get_redis()
        ping_result = redis_client.ping()
        if inspect.isawaitable(ping_result):
            await ping_result
    except Exception:
        redis = _unhealthy_component("Redis 连接失败")

    try:
        check_storage_health()
    except StorageBucketMissingError as exc:
        minio = _unhealthy_component(str(exc))
    except Exception:
        minio = _unhealthy_component("MinIO 连接失败")

    overall_status = "healthy"
    status_code = status.HTTP_200_OK
    if database.status != "healthy" or redis.status != "healthy" or minio.status != "healthy":
        overall_status = "degraded"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    payload = HealthCheckRead(
        status=overall_status,
        checked_at=datetime.now(timezone.utc),
        database=database,
        redis=redis,
        minio=minio,
    )
    return status_code, payload
