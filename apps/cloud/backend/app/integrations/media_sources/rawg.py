# mypy: ignore-errors
"""RAWG 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本
from app.shared.kernel.config import settings


class RAWG数据源(外部文娱数据源):
    """RAWG 游戏数据源。"""

    provider = "rawg"
    base_url = "https://api.rawg.io/api"

    @property
    def available(self) -> bool:
        """是否配置 RAWG API key。"""
        return bool(settings.MEDIA_RAWG_API_KEY.strip())

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索游戏。"""
        if media_type and media_type != "game":
            return []
        response = await self.client.get(
            f"{self.base_url}/games",
            params={"key": settings.MEDIA_RAWG_API_KEY.strip(), "search": keyword, "page_size": 12},
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else []
        return [self._映射条目(item) for item in results if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取游戏详情。"""
        response = await self.client.get(
            f"{self.base_url}/games/{external_id}",
            params={"key": settings.MEDIA_RAWG_API_KEY.strip()},
        )
        response.raise_for_status()
        data = response.json()
        return self._映射条目(data if isinstance(data, dict) else {})

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 RAWG 条目。"""
        genres = item.get("genres") if isinstance(item.get("genres"), list) else []
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        developers = item.get("developers") if isinstance(item.get("developers"), list) else []
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id") or item.get("slug")),
            title=规范化文本(item.get("name")) or str(item.get("id")),
            media_type="game",
            creators=[str(dev.get("name")) for dev in developers if isinstance(dev, dict) and dev.get("name")],
            summary=规范化文本(item.get("description_raw")),
            genres=[str(genre.get("name")) for genre in genres if isinstance(genre, dict) and genre.get("name")],
            tags=[str(tag.get("name")) for tag in tags[:10] if isinstance(tag, dict) and tag.get("name")],
            release_date=解析日期(item.get("released")),
            cover_url=规范化文本(item.get("background_image")),
            thumbnail_url=规范化文本(item.get("background_image")),
            external_url=规范化文本(item.get("website")) or f"https://rawg.io/games/{item.get('slug')}",
            raw=item,
        )
