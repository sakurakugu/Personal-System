"""Redis 客户端单例。

此模块提供 Redis 连接管理：
- 懒加载 Redis 客户端
- 连接关闭处理

Redis 用于：
- Token 黑名单存储？这是是否已经不需要了
- 缓存（如需要）
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings

# 全局 Redis 客户端实例（懒加载）
redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """
    获取 Redis 客户端实例（单例模式）。

    首次调用时创建连接，后续调用返回同一实例。

    Returns:
        aioredis.Redis: Redis 异步客户端

    Example:
        redis = await get_redis()
        await redis.setex(f"bl:{token}", ttl, "1")
    """
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # 自动解码响应为字符串
        )
    return redis_client


async def close_redis() -> None:
    """
    关闭 Redis 连接。

    在应用关闭时调用，释放连接资源。
    """
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
