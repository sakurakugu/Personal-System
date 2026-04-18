"""RSS 生成服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from app.core.config import settings
from app.modules.feed.schemas import FeedItemRead


def _format_rfc822(dt: datetime) -> str:
    """将 datetime 格式化为 RSS 标准的 RFC 822 时间字符串。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def build_rss_xml(
    items: list[FeedItemRead],
    *,
    title: str = "Sakurakuguの小窝",
    description: str = "动态流",
) -> str:
    """根据 Feed 条目构建 RSS 2.0 XML。"""
    site_url = settings.SITE_URL.rstrip("/")
    now = _format_rfc822(datetime.now(timezone.utc))

    channel_items: list[str] = []
    for raw in items:
        item = FeedItemRead.model_validate(raw) if isinstance(raw, dict) else raw
        if item.type != "article" or item.article is None:
            continue

        article = item.article
        link = f"{site_url}/blog/{article.slug}"
        pub_date = _format_rfc822(item.published_at)
        title_text = escape(article.title)
        desc_text = escape(article.excerpt or "")

        channel_items.append(
            f"""    <item>
      <title>{title_text}</title>
      <link>{link}</link>
      <description>{desc_text}</description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="true">{link}</guid>
    </item>"""
        )

    items_xml = "\n".join(channel_items)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{escape(title)}</title>
    <link>{site_url}</link>
    <description>{escape(description)}</description>
    <lastBuildDate>{now}</lastBuildDate>
    <language>zh-CN</language>
{items_xml}
  </channel>
</rss>
"""
