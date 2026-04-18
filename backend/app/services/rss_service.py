"""RSS 服务兼容入口。"""

from app.integrations.rss.service import _format_rfc822, build_rss_xml

__all__ = ["_format_rfc822", "build_rss_xml"]
