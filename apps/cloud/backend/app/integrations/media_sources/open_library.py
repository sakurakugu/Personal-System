# mypy: ignore-errors
"""Open Library 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本


class OpenLibrary数据源(外部文娱数据源):
    """Open Library 数据源。"""

    provider = "open_library"
    base_url = "https://openlibrary.org"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索 Open Library 作品。"""
        if media_type and media_type not in {"book", "novel", "comic"}:
            return []
        response = await self.client.get(f"{self.base_url}/search.json", params={"q": keyword, "limit": 12})
        response.raise_for_status()
        data = response.json()
        docs = data.get("docs") if isinstance(data, dict) else []
        return [self._映射搜索条目(item) for item in docs if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取 Open Library 详情。"""
        key = external_id if external_id.startswith("/works/") else f"/works/{external_id}"
        response = await self.client.get(f"{self.base_url}{key}.json")
        response.raise_for_status()
        data = response.json()
        return self._映射详情(key, data if isinstance(data, dict) else {})

    def _封面URL(self, cover_id: object) -> str | None:
        """构造封面 URL。"""
        if cover_id is None:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    def _映射搜索条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射搜索结果。"""
        key = str(item.get("key", ""))
        title = 规范化文本(item.get("title")) or key
        authors = item.get("author_name") if isinstance(item.get("author_name"), list) else []
        subjects = item.get("subject") if isinstance(item.get("subject"), list) else []
        return 外部作品候选(
            provider=self.provider,
            external_id=key.removeprefix("/works/"),
            title=title,
            media_type="book",
            creators=[str(item).strip() for item in authors[:6] if str(item).strip()],
            genres=[str(item).strip() for item in subjects[:8] if str(item).strip()],
            release_date=解析日期(str(item.get("first_publish_year")) if item.get("first_publish_year") else None),
            cover_url=self._封面URL(item.get("cover_i")),
            thumbnail_url=self._封面URL(item.get("cover_i")),
            external_url=f"{self.base_url}{key}" if key else None,
            raw=item,
        )

    def _映射详情(self, key: str, item: dict[str, Any]) -> 外部作品候选:
        """映射详情结果。"""
        description = item.get("description")
        if isinstance(description, dict):
            description = description.get("value")
        covers = item.get("covers") if isinstance(item.get("covers"), list) else []
        subjects = item.get("subjects") if isinstance(item.get("subjects"), list) else []
        return 外部作品候选(
            provider=self.provider,
            external_id=key.removeprefix("/works/"),
            title=规范化文本(item.get("title")) or key,
            media_type="book",
            creators=[],
            summary=规范化文本(description),
            genres=[str(item).strip() for item in subjects[:8] if str(item).strip()],
            release_date=解析日期(item.get("first_publish_date")),
            cover_url=self._封面URL(covers[0] if covers else None),
            thumbnail_url=self._封面URL(covers[0] if covers else None),
            external_url=f"{self.base_url}{key}",
            raw=item,
        )
