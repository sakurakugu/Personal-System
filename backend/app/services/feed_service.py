"""Feed 服务兼容入口。"""

from app.core.redis import get_redis
from app.modules.feed.service import (
    _build_feed_home_cache_key,
    _normalize_feed_cache_version,
    article_feed_source_query,
    build_article_feed_item,
    build_feed_visible_article_clause,
    build_moment_feed_item,
    delete_feed_item,
    ensure_article_feed_items,
    get_feed_item,
    list_feed_items,
    load_feed_articles,
    load_feed_moments,
    moment_feed_source_query,
    sync_article_feed_item,
    sync_moment_feed_item,
)


async def _get_feed_home_cache_version() -> str:
    """获取当前首页 Feed 缓存版本。"""
    redis = await get_redis()
    version = await redis.get("feed:home:version")
    return _normalize_feed_cache_version(version if isinstance(version, str) else None)


async def invalidate_feed_home_cache() -> None:
    """清除首页 Feed 缓存。"""
    redis = await get_redis()
    await redis.incr("feed:home:version")


__all__ = [
    "_build_feed_home_cache_key",
    "_get_feed_home_cache_version",
    "_normalize_feed_cache_version",
    "article_feed_source_query",
    "build_article_feed_item",
    "build_feed_visible_article_clause",
    "build_moment_feed_item",
    "delete_feed_item",
    "ensure_article_feed_items",
    "get_feed_item",
    "get_redis",
    "invalidate_feed_home_cache",
    "list_feed_items",
    "load_feed_articles",
    "load_feed_moments",
    "moment_feed_source_query",
    "sync_article_feed_item",
    "sync_moment_feed_item",
]
