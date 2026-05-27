# mypy: ignore-errors
"""VNDB 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本


class VNDB数据源(外部文娱数据源):
    """VNDB 数据源。"""

    provider = "vndb"
    base_url = "https://api.vndb.org/kana"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索视觉小说。"""
        if media_type and media_type not in {"game", "novel"}:
            return []
        payload = {
            "filters": ["search", "=", keyword],
            "fields": "title, alttitle, image.url, image.sexual, image.violence, released, tags.name",
            "results": 12,
        }
        response = await self.client.post(f"{self.base_url}/vn", json=payload)
        response.raise_for_status()
        data = response.json()
        items = data.get("results") if isinstance(data, dict) else []
        return [self._映射条目(item) for item in items if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取视觉小说详情。"""
        payload = {
            "filters": ["id", "=", external_id],
            "fields": "title, alttitle, image.url, image.sexual, image.violence, released, description, tags.name",
            "results": 1,
        }
        response = await self.client.post(f"{self.base_url}/vn", json=payload)
        response.raise_for_status()
        data = response.json()
        items = data.get("results") if isinstance(data, dict) else []
        return self._映射条目(items[0] if items else {"id": external_id})

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 VNDB 条目。"""
        image = item.get("image") if isinstance(item.get("image"), dict) else {}
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id")),
            title=规范化文本(item.get("title")) or str(item.get("id")),
            original_title=规范化文本(item.get("alttitle")),
            media_type="game",
            creators=[],
            summary=规范化文本(item.get("description")),
            tags=[str(tag.get("name")) for tag in tags[:10] if isinstance(tag, dict) and tag.get("name")],
            release_date=解析日期(item.get("released")),
            cover_url=规范化文本(image.get("url")),
            thumbnail_url=规范化文本(image.get("url")),
            external_url=f"https://vndb.org/{item.get('id')}",
            raw=item,
        )
