"""系统健康检查服务。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import text

from app.core.redis import get_redis
from app.modules.system.schemas import HealthCheckRead, HealthComponentStatus
from app.services.storage_service import StorageBucketMissingError, check_storage_health
from app.shared.db.session import engine


def _healthy_component() -> HealthComponentStatus:
    """返回正常组件状态。"""
    return HealthComponentStatus(status="healthy")


def _unhealthy_component(detail: str) -> HealthComponentStatus:
    """返回异常组件状态。"""
    return HealthComponentStatus(status="unhealthy", detail=detail)


async def _check_database_health() -> HealthComponentStatus:
    """检查数据库连通性。"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return _unhealthy_component("数据库连接失败")
    return _healthy_component()


async def _check_redis_health() -> HealthComponentStatus:
    """检查 Redis 连通性。"""
    try:
        redis_client = await get_redis()
        ping_result = redis_client.ping()
        if isinstance(ping_result, bool):
            return _healthy_component()
        await ping_result
    except Exception:
        return _unhealthy_component("Redis 连接失败")
    return _healthy_component()


async def _check_minio_health() -> HealthComponentStatus:
    """在线程池中检查 MinIO，避免阻塞事件循环。"""
    try:
        await asyncio.to_thread(check_storage_health)
    except StorageBucketMissingError as exc:
        return _unhealthy_component(str(exc))
    except Exception:
        return _unhealthy_component("MinIO 连接失败")
    return _healthy_component()


async def get_health_check() -> tuple[int, HealthCheckRead]:
    """获取系统健康检查结果。"""
    database, redis, minio = await asyncio.gather(
        _check_database_health(),
        _check_redis_health(),
        _check_minio_health(),
    )

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
