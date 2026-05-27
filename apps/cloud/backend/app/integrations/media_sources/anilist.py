# mypy: ignore-errors
"""AniList 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本

搜索查询 = """
query ($search: String, $type: MediaType) {
  Page(page: 1, perPage: 12) {
    media(search: $search, type: $type) {
      id
      title { romaji english native }
      type
      description(asHtml: false)
      genres
      tags { name rank }
      startDate { year month day }
      coverImage { extraLarge large medium }
      siteUrl
      staff(sort: RELEVANCE, perPage: 5) {
        nodes { name { full } }
      }
    }
  }
}
"""

详情查询 = """
query ($id: Int) {
  Media(id: $id) {
    id
    title { romaji english native }
    type
    description(asHtml: false)
    genres
    tags { name rank }
    startDate { year month day }
    coverImage { extraLarge large medium }
    siteUrl
    staff(sort: RELEVANCE, perPage: 8) {
      nodes { name { full } }
    }
  }
}
"""


class AniList数据源(外部文娱数据源):
    """AniList 数据源。"""

    provider = "anilist"
    base_url = "https://graphql.anilist.co"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索 AniList 作品。"""
        if media_type and media_type not in {"anime", "comic"}:
            return []
        variables = {
            "search": keyword,
            "type": "MANGA" if media_type == "comic" else "ANIME",
        }
        response = await self.client.post(self.base_url, json={"query": 搜索查询, "variables": variables})
        response.raise_for_status()
        data = response.json()
        items = (((data.get("data") or {}).get("Page") or {}).get("media") or []) if isinstance(data, dict) else []
        return [self._映射条目(item) for item in items if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取 AniList 详情。"""
        response = await self.client.post(self.base_url, json={"query": 详情查询, "variables": {"id": int(external_id)}})
        response.raise_for_status()
        data = response.json()
        item = ((data.get("data") or {}).get("Media") or {}) if isinstance(data, dict) else {}
        return self._映射条目(item)

    def _映射日期(self, value: object):
        """映射 AniList 分段日期。"""
        if not isinstance(value, dict) or not value.get("year"):
            return None
        year = int(value["year"])
        month = int(value.get("month") or 1)
        day = int(value.get("day") or 1)
        return 解析日期(f"{year:04d}-{month:02d}-{day:02d}")

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 AniList 条目。"""
        title_info = item.get("title") if isinstance(item.get("title"), dict) else {}
        cover = item.get("coverImage") if isinstance(item.get("coverImage"), dict) else {}
        staff = (((item.get("staff") or {}).get("nodes")) or []) if isinstance(item.get("staff"), dict) else []
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        title = 规范化文本(title_info.get("english")) or 规范化文本(title_info.get("romaji")) or str(item.get("id"))
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id")),
            title=title,
            original_title=规范化文本(title_info.get("native")) or 规范化文本(title_info.get("romaji")),
            media_type="comic" if item.get("type") == "MANGA" else "anime",
            creators=[node["name"]["full"] for node in staff if isinstance(node, dict) and (node.get("name") or {}).get("full")],
            summary=规范化文本(item.get("description")),
            genres=[str(genre) for genre in item.get("genres", []) if isinstance(genre, str)],
            tags=[str(tag.get("name")) for tag in tags[:8] if isinstance(tag, dict) and tag.get("name")],
            release_date=self._映射日期(item.get("startDate")),
            cover_url=规范化文本(cover.get("extraLarge")) or 规范化文本(cover.get("large")),
            thumbnail_url=规范化文本(cover.get("medium")) or 规范化文本(cover.get("large")),
            external_url=规范化文本(item.get("siteUrl")),
            raw=item,
        )
