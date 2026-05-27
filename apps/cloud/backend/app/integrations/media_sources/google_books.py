# mypy: ignore-errors
"""Google Books 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本, 规范化文本列表


class GoogleBooks数据源(外部文娱数据源):
    """Google Books 数据源。"""

    provider = "google_books"
    base_url = "https://www.googleapis.com/books/v1"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索书籍。"""
        if media_type and media_type not in {"book", "novel", "comic"}:
            return []
        response = await self.client.get(f"{self.base_url}/volumes", params={"q": keyword, "maxResults": 12})
        response.raise_for_status()
        data = response.json()
        items = data.get("items") if isinstance(data, dict) else []
        return [self._映射条目(item) for item in items if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取书籍详情。"""
        response = await self.client.get(f"{self.base_url}/volumes/{external_id}")
        response.raise_for_status()
        data = response.json()
        return self._映射条目(data if isinstance(data, dict) else {})

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 Google Books 条目。"""
        volume = item.get("volumeInfo") if isinstance(item.get("volumeInfo"), dict) else {}
        images = volume.get("imageLinks") if isinstance(volume.get("imageLinks"), dict) else {}
        title = 规范化文本(volume.get("title")) or str(item.get("id"))
        authors = 规范化文本列表(volume.get("authors"))
        categories = 规范化文本列表(volume.get("categories"))
        cover_url = 规范化文本(images.get("extraLarge")) or 规范化文本(images.get("large")) or 规范化文本(images.get("thumbnail"))
        if cover_url:
            cover_url = cover_url.replace("http://", "https://")
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id")),
            title=title,
            original_title=规范化文本(volume.get("subtitle")),
            media_type="book",
            creators=authors,
            summary=规范化文本(volume.get("description")),
            genres=categories[:8],
            tags=[],
            release_date=解析日期(volume.get("publishedDate")),
            cover_url=cover_url,
            thumbnail_url=cover_url,
            external_url=规范化文本(volume.get("infoLink")),
            raw=item,
        )
