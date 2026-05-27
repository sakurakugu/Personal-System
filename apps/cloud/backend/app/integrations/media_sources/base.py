"""文娱外部数据源基础能力。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.modules.media.schemas import 文娱主分类


class 外部作品候选(BaseModel):
    """统一的外部作品候选。"""

    provider: str
    external_id: str
    title: str
    original_title: str | None = None
    media_type: 文娱主分类
    creators: list[str] = Field(default_factory=list)
    summary: str | None = None
    description: str | None = None
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    release_date: date | None = None
    cover_url: str | None = None
    thumbnail_url: str | None = None
    external_url: str | None = None
    raw: dict[str, Any] | None = None


外部作品详情 = 外部作品候选


class 外部文娱数据源不可用(RuntimeError):
    """外部数据源缺少配置或临时不可用。"""


class 外部文娱数据源:
    """统一外部文娱数据源接口。"""

    provider: str

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    @property
    def available(self) -> bool:
        """当前数据源是否可用。"""
        return True

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索外部作品。"""
        raise NotImplementedError

    async def get_detail(self, external_id: str) -> 外部作品详情:
        """读取外部作品详情。"""
        raise NotImplementedError


def 规范化文本(value: object) -> str | None:
    """将外部文本值规范化为内部可用文本。"""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def 规范化文本列表(value: object) -> list[str]:
    """将外部数组值规范化为去重文本列表。"""
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str):
            normalized = item.strip()
            if normalized and normalized not in items:
                items.append(normalized)
    return items


def 解析日期(value: object) -> date | None:
    """解析外部日期字符串。"""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            if fmt == "%Y":
                return date(int(normalized[:4]), 1, 1)
            if fmt == "%Y-%m" and len(normalized) >= 7:
                year, month = normalized[:7].split("-")
                return date(int(year), int(month), 1)
            if fmt == "%Y-%m-%d" and len(normalized) >= 10:
                return date.fromisoformat(normalized[:10])
        except ValueError:
            continue
    return None


def 取嵌套值(data: Mapping[str, Any], path: str) -> Any:
    """按点号路径读取嵌套字段。"""
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current
