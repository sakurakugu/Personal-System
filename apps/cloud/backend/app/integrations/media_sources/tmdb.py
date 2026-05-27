# mypy: ignore-errors
"""TMDB 文娱数据源。"""

from __future__ import annotations

from typing import Any

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本
from app.shared.kernel.config import settings


class TMDB数据源(外部文娱数据源):
    """TMDB 数据源。"""

    provider = "tmdb"
    base_url = "https://api.themoviedb.org/3"
    image_base_url = "https://image.tmdb.org/t/p"

    @property
    def available(self) -> bool:
        """是否配置 TMDB Token。"""
        return bool(settings.MEDIA_TMDB_TOKEN.strip())

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {settings.MEDIA_TMDB_TOKEN.strip()}"}

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索 TMDB 影视作品。"""
        if media_type and media_type not in {"movie", "tv"}:
            return []
        target_type = "tv" if media_type == "tv" else "movie"
        response = await self.client.get(
            f"{self.base_url}/search/{target_type}",
            params={"query": keyword, "language": "zh-CN", "include_adult": "false"},
            headers=self._headers(),
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") if isinstance(data, dict) else []
        return [self._映射条目(item, target_type) for item in results[:12] if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取 TMDB 详情。"""
        kind, _, item_id = external_id.partition(":")
        target_type = kind if kind in {"movie", "tv"} else "movie"
        target_id = item_id or external_id
        response = await self.client.get(
            f"{self.base_url}/{target_type}/{target_id}",
            params={"language": "zh-CN", "append_to_response": "credits"},
            headers=self._headers(),
        )
        response.raise_for_status()
        data = response.json()
        return self._映射条目(data if isinstance(data, dict) else {}, target_type)

    def _图片URL(self, path: object, size: str) -> str | None:
        """构造图片 URL。"""
        if not isinstance(path, str) or not path:
            return None
        return f"{self.image_base_url}/{size}{path}"

    def _映射条目(self, item: dict[str, Any], target_type: str) -> 外部作品候选:
        """映射 TMDB 条目。"""
        credits = item.get("credits") if isinstance(item.get("credits"), dict) else {}
        crew = credits.get("crew") if isinstance(credits.get("crew"), list) else []
        creators = [
            str(person.get("name")).strip()
            for person in crew
            if isinstance(person, dict) and person.get("job") in {"Director", "Creator"} and person.get("name")
        ]
        title = 规范化文本(item.get("title")) or 规范化文本(item.get("name")) or str(item.get("id"))
        original_title = 规范化文本(item.get("original_title")) or 规范化文本(item.get("original_name"))
        genres = item.get("genres") if isinstance(item.get("genres"), list) else []
        date_value = item.get("release_date") or item.get("first_air_date")
        return 外部作品候选(
            provider=self.provider,
            external_id=f"{target_type}:{item.get('id')}",
            title=title,
            original_title=original_title,
            media_type="tv" if target_type == "tv" else "movie",
            creators=list(dict.fromkeys(creators)),
            summary=规范化文本(item.get("overview")),
            genres=[str(genre.get("name")) for genre in genres if isinstance(genre, dict) and genre.get("name")],
            release_date=解析日期(date_value),
            cover_url=self._图片URL(item.get("poster_path"), "w780"),
            thumbnail_url=self._图片URL(item.get("poster_path"), "w342"),
            external_url=f"https://www.themoviedb.org/{target_type}/{item.get('id')}",
            raw=item,
        )
