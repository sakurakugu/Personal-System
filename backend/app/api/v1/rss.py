"""RSS 路由兼容入口。"""

from app.integrations.rss.api import router, rss_feed

__all__ = ["router", "rss_feed"]
