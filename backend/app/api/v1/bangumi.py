"""Bangumi 路由兼容入口。"""

from app.integrations.bangumi.api import proxy_bangumi_collections, router

__all__ = ["proxy_bangumi_collections", "router"]
