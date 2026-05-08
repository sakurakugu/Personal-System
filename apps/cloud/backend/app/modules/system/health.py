"""系统健康检查服务。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import text

from app.core.redis import get_redis
from app.modules.system.schemas import HealthCheckRead, HealthComponentStatus
from app.shared.db.session import engine
from app.shared.storage.client import StorageBucketMissingError, 检查存储健康


def _健康组件() -> HealthComponentStatus:
    """返回正常组件状态。"""
    return HealthComponentStatus(status="healthy")


def _异常组件(detail: str) -> HealthComponentStatus:
    """返回异常组件状态。"""
    return HealthComponentStatus(status="unhealthy", detail=detail)


async def _检查数据库健康() -> HealthComponentStatus:
    """检查数据库连通性。"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return _异常组件("数据库连接失败")
    return _健康组件()


async def _检查Redis健康() -> HealthComponentStatus:
    """检查 Redis 连通性。"""
    try:
        redis_client = await get_redis()
        ping_result = redis_client.ping()
        if isinstance(ping_result, bool):
            return _健康组件()
        await ping_result
    except Exception:
        return _异常组件("Redis 连接失败")
    return _健康组件()


async def _检查Minio健康() -> HealthComponentStatus:
    """在线程池中检查 MinIO，避免阻塞事件循环。"""
    try:
        await asyncio.to_thread(检查存储健康)
    except StorageBucketMissingError as exc:
        return _异常组件(str(exc))
    except Exception:
        return _异常组件("MinIO 连接失败")
    return _健康组件()


async def 获取健康检查() -> tuple[int, HealthCheckRead]:
    """获取系统健康检查结果。"""
    database, redis, minio = await asyncio.gather(
        _检查数据库健康(),
        _检查Redis健康(),
        _检查Minio健康(),
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
