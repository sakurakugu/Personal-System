"""作品推荐模块相关 Schema。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

文娱主分类 = Literal["game", "novel", "book", "anime", "comic", "movie", "tv", "music", "other"]
文娱状态 = Literal["planned", "doing", "done", "paused", "dropped"]
文娱资源类型 = Literal["cover", "backdrop", "screenshot", "logo", "other"]

允许的文娱主分类 = {"game", "novel", "book", "anime", "comic", "movie", "tv", "music", "other"}
允许的文娱状态 = {"planned", "doing", "done", "paused", "dropped"}


def _规范化可选文本(value: str | None) -> str | None:
    """规范化可选文本字段。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _规范化字符串数组(value: list[str] | str | None) -> list[str]:
    """规范化数组字段。"""
    if value is None:
        return []
    if isinstance(value, str):
        value = value.replace("，", ",").split(",")
    normalized = [item.strip() for item in value if item.strip()]
    return list(dict.fromkeys(normalized))


class 文娱条目创建(BaseModel):
    """创建文娱条目请求。"""

    title: str = Field(min_length=1, max_length=300)
    original_title: str | None = Field(default=None, max_length=300)
    media_type: 文娱主分类
    status: 文娱状态
    rating: int | None = Field(default=None, ge=1, le=15)
    creator: str | None = Field(default=None, max_length=200)
    summary: str | None = None
    description: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    personal_tags: list[str] | None = None
    release_date: date | None = None
    primary_cover_asset_id: UUID | None = None
    is_visible: bool = True

    @field_validator("title", "original_title", "creator", "summary", "description")
    @classmethod
    def 规范化文本(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("genres", "tags", "personal_tags")
    @classmethod
    def 规范化数组(cls, value: list[str] | str | None) -> list[str]:
        """统一规范化数组字段。"""
        return _规范化字符串数组(value)


class 文娱条目更新(BaseModel):
    """更新文娱条目请求。"""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    original_title: str | None = Field(default=None, max_length=300)
    media_type: 文娱主分类 | None = None
    status: 文娱状态 | None = None
    rating: int | None = Field(default=None, ge=1, le=15)
    creator: str | None = Field(default=None, max_length=200)
    summary: str | None = None
    description: str | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    personal_tags: list[str] | None = None
    release_date: date | None = None
    primary_cover_asset_id: UUID | None = None
    is_visible: bool | None = None

    @field_validator("title", "original_title", "creator", "summary", "description")
    @classmethod
    def 规范化文本(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("genres", "tags", "personal_tags")
    @classmethod
    def 规范化数组(cls, value: list[str] | str | None) -> list[str]:
        """统一规范化数组字段。"""
        return _规范化字符串数组(value)


class 文娱资源信息(BaseModel):
    """文娱资源响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    media_item_id: UUID
    asset_type: 文娱资源类型
    storage_key: str | None = None
    external_url: str | None = None
    thumbnail_url: str | None = None
    source_provider: str | None = None
    source_asset_id: str | None = None
    original_name: str | None = None
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    size: int | None = None
    attribution: str | None = None
    license: str | None = None
    is_primary: bool
    sort_order: int
    url: str | None = None
    preview_url: str | None = None
    created_at: datetime
    updated_at: datetime


class 文娱外部来源信息(BaseModel):
    """文娱外部来源响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    media_item_id: UUID
    provider: str
    external_id: str
    external_url: str | None = None
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime


class 文娱条目信息(BaseModel):
    """文娱条目响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_title: str | None = None
    media_type: 文娱主分类
    status: 文娱状态
    rating: int | None = None
    creator: str | None = None
    summary: str | None = None
    description: str | None = None
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    personal_tags: list[str] = Field(default_factory=list)
    release_date: date | None = None
    primary_cover_asset_id: UUID | None = None
    primary_cover_asset: 文娱资源信息 | None = None
    assets: list[文娱资源信息] = Field(default_factory=list)
    external_sources: list[文娱外部来源信息] = Field(default_factory=list)
    is_visible: bool
    created_at: datetime
    updated_at: datetime


class 文娱筛选项(BaseModel):
    """文娱筛选项统计。"""

    name: str
    count: int


class 文娱创作者建议(BaseModel):
    """文娱创作者建议项。"""

    name: str
    count: int


class 文娱列表响应(BaseModel):
    """文娱列表响应。"""

    items: list[文娱条目信息]
    total: int
    page: int
    page_size: int
    pages: int
    all_data_updated_at: datetime | None = None


class 外部文娱候选(BaseModel):
    """外部文娱搜索候选。"""

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
    raw: dict | None = None


class 外部文娱搜索响应(BaseModel):
    """外部文娱搜索响应。"""

    items: list[外部文娱候选]


class 外部文娱导入请求(BaseModel):
    """从外部来源导入文娱条目请求。"""

    provider: str = Field(min_length=1, max_length=64)
    external_id: str = Field(min_length=1, max_length=200)
    status: 文娱状态 = "planned"
    rating: int | None = Field(default=None, ge=1, le=15)
    is_visible: bool = True
    localize_cover: bool = True


class 外部封面导入请求(BaseModel):
    """从外部 URL 导入封面请求。"""

    external_url: str = Field(min_length=1, max_length=1000)
    source_provider: str | None = Field(default=None, max_length=64)
    source_asset_id: str | None = Field(default=None, max_length=200)
    original_name: str | None = Field(default=None, max_length=300)
    attribution: str | None = None
    license: str | None = Field(default=None, max_length=300)
    set_primary: bool = True

    @field_validator("source_provider", "source_asset_id", "original_name", "attribution", "license")
    @classmethod
    def 规范化封面文本(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)
