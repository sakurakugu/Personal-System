"""文娱推荐模块相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.files.schemas import FileRead

文娱主分类 = Literal["game", "novel", "book", "anime", "comic", "movie", "tv", "music", "other"]
文娱状态 = Literal["planned", "doing", "done", "paused", "dropped"]

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
    cover_file_id: UUID | None = None
    is_visible: bool = True

    @field_validator("title", "original_title", "creator", "summary", "description")
    @classmethod
    def 规范化文本(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("genres", "tags")
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
    cover_file_id: UUID | None = None
    is_visible: bool | None = None

    @field_validator("title", "original_title", "creator", "summary", "description")
    @classmethod
    def 规范化文本(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("genres", "tags")
    @classmethod
    def 规范化数组(cls, value: list[str] | str | None) -> list[str]:
        """统一规范化数组字段。"""
        return _规范化字符串数组(value)


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
    cover_file_id: UUID | None = None
    cover_file: FileRead | None = None
    is_visible: bool
    created_at: datetime
    updated_at: datetime


class 文娱筛选项(BaseModel):
    """文娱筛选项统计。"""

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
