# mypy: ignore-errors
"""Bangumi 文娱数据源。"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 解析日期, 规范化文本

Bangumi类型映射 = {
    1: "book",
    2: "anime",
    3: "music",
    4: "game",
    6: "other",
}

内部类型到Bangumi类型 = {
    "book": 1,
    "novel": 1,
    "comic": 1,
    "anime": 2,
    "music": 3,
    "game": 4,
}


class Bangumi数据源(外部文娱数据源):
    """Bangumi 数据源。"""

    provider = "bangumi"
    base_url = "https://api.bgm.tv"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索 Bangumi 条目。"""
        payload: dict[str, Any] = {
            "keyword": keyword,
            "filter": {},
        }
        if media_type in 内部类型到Bangumi类型:
            payload["filter"]["type"] = [内部类型到Bangumi类型[media_type]]
        response = await self.client.post(f"{self.base_url}/v0/search/subjects", json=payload, params={"limit": 12})
        response.raise_for_status()
        data = response.json()
        items = data.get("data") if isinstance(data, dict) else []
        return [self._映射条目(item) for item in items if isinstance(item, dict)]

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取 Bangumi 条目详情。"""
        response = await self.client.get(f"{self.base_url}/v0/subjects/{external_id}")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise httpx.HTTPStatusError("Bangumi 返回结构异常", request=response.request, response=response)
        return self._映射条目(data)

    def _映射条目(self, item: dict[str, Any]) -> 外部作品候选:
        """映射 Bangumi 条目。"""
        images = item.get("images") if isinstance(item.get("images"), dict) else {}
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        tag_names = [str(tag.get("name")).strip() for tag in tags if isinstance(tag, dict) and tag.get("name")]
        infobox = item.get("infobox") if isinstance(item.get("infobox"), list) else []
        creators: list[str] = []
        for info in infobox:
            if not isinstance(info, dict) or info.get("key") not in {"作者", "导演", "制作", "出版社", "开发"}:
                continue
            value = info.get("value")
            if isinstance(value, str):
                creators.append(value.strip())
            elif isinstance(value, list):
                creators.extend(str(v.get("v", "")).strip() for v in value if isinstance(v, dict))
        creators = list(dict.fromkeys(item for item in creators if item))
        title = 规范化文本(item.get("name_cn")) or 规范化文本(item.get("name")) or str(item.get("id"))
        media_type = Bangumi类型映射.get(item.get("type"), "other")
        return 外部作品候选(
            provider=self.provider,
            external_id=str(item.get("id")),
            title=title,
            original_title=规范化文本(item.get("name")),
            media_type=media_type,  # type: ignore[arg-type]
            creators=creators,
            summary=规范化文本(item.get("summary")),
            genres=[],
            tags=list(dict.fromkeys(tag_names[:12])),
            release_date=解析日期(item.get("date")),
            cover_url=规范化文本(images.get("large")) or 规范化文本(images.get("common")),
            thumbnail_url=规范化文本(images.get("medium")) or 规范化文本(images.get("small")),
            external_url=f"https://bgm.tv/subject/{item.get('id')}",
            raw=item,
        )
