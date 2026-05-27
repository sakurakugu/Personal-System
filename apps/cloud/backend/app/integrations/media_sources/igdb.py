# mypy: ignore-errors
"""IGDB 文娱数据源。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 规范化文本
from app.shared.kernel.config import settings


class IGDB数据源(外部文娱数据源):
    """IGDB 游戏数据源。"""

    provider = "igdb"
    base_url = "https://api.igdb.com/v4"

    @property
    def available(self) -> bool:
        """是否配置 IGDB 凭据。"""
        return bool(settings.MEDIA_IGDB_CLIENT_ID.strip() and settings.MEDIA_IGDB_ACCESS_TOKEN.strip())

    def _headers(self) -> dict[str, str]:
        return {
            "Client-ID": settings.MEDIA_IGDB_CLIENT_ID.strip(),
            "Authorization": f"Bearer {settings.MEDIA_IGDB_ACCESS_TOKEN.strip()}",
        }

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索游戏。"""
        if media_type and media_type != "game":
            return []
        query = (
            'search "{keyword}"; fields name,summary,first_release_date,cover.image_id,genres.name,involved_companies.company.name,url; limit 12;'
        ).format(keyword=keyword.replace('"', '\\"'))
        response = await self.client.post(f"{self.base_url}/games", content=query, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return [self._映射条目(item) for item in data if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取游戏详情。"""
        query = f"where id = {int(external_id)}; fields name,summary,first_release_date,cover.image_id,genres.name,involved_companies.company.name,url; limit 1;"
        response = await self.client.post(f"{self.base_url}/games", content=query, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return self._映射条目(data[0] if data else {"id": external_id})

    def _图片URL(self, image_id: object) -> str | None:
        """构造 IGDB 图片 URL。"""
        if not image_id:
            return None
        return f"https://images.igdb.com/igdb/image/upload/t_cover_big_2x/{image_id}.jpg"

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 IGDB 条目。"""
        genres = item.get("genres") if isinstance(item.get("genres"), list) else []
        companies = item.get("involved_companies") if isinstance(item.get("involved_companies"), list) else []
        cover = item.get("cover") if isinstance(item.get("cover"), dict) else {}
        release_date = None
        if isinstance(item.get("first_release_date"), int):
            release_date = datetime.fromtimestamp(item["first_release_date"], tz=timezone.utc).date()
        creators = []
        for company in companies:
            if isinstance(company, dict) and isinstance(company.get("company"), dict) and company["company"].get("name"):
                creators.append(str(company["company"]["name"]))
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id")),
            title=规范化文本(item.get("name")) or str(item.get("id")),
            media_type="game",
            creators=list(dict.fromkeys(creators)),
            summary=规范化文本(item.get("summary")),
            genres=[str(genre.get("name")) for genre in genres if isinstance(genre, dict) and genre.get("name")],
            release_date=release_date,
            cover_url=self._图片URL(cover.get("image_id")),
            thumbnail_url=self._图片URL(cover.get("image_id")),
            external_url=规范化文本(item.get("url")),
            raw=item,
        )
