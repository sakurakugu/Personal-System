"""统计服务兼容入口。"""

from app.modules.stats.service import (
    _BLOG_STATS_CACHE_KEY,
    _BLOG_STATS_CACHE_TTL,
    _构建待办完成历史响应,
    _构建最近访问趋势,
    _限制单个待办单日得分,
    get_blog_stats,
    get_dashboard_stats,
    get_todo_completion_history,
    hash_client_ip,
    invalidate_blog_stats_cache,
    iter_dates,
    record_pageview,
    待办完成聚合记录,
    近期访问聚合记录,
)

__all__ = [
    "_BLOG_STATS_CACHE_KEY",
    "_BLOG_STATS_CACHE_TTL",
    "_构建待办完成历史响应",
    "_构建最近访问趋势",
    "_限制单个待办单日得分",
    "get_blog_stats",
    "get_dashboard_stats",
    "get_todo_completion_history",
    "hash_client_ip",
    "invalidate_blog_stats_cache",
    "iter_dates",
    "record_pageview",
    "待办完成聚合记录",
    "近期访问聚合记录",
]
