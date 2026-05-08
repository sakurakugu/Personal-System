"""收藏模块相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.files.schemas import FileRead


def _规范化可选文本(value: str | None) -> str | None:
    """规范化可选文本字段。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class CollectionAssetInput(BaseModel):
    """收藏附件写入参数。"""

    file_id: UUID
    sort_order: int = Field(default=0, ge=0, le=9999)


class CollectionCreate(BaseModel):
    """创建收藏请求。"""

    type: str = "link"
    title: str | None = Field(default=None, max_length=300)
    content_text: str | None = None
    note: str | None = None
    status: str = "inbox"
    tags: list[str] | None = None
    assets: list[CollectionAssetInput] | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验收藏类型。"""
        allowed = {"link", "text", "image", "file"}
        if value not in allowed:
            raise ValueError("收藏类型不合法")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """校验收藏状态。"""
        allowed = {"inbox", "processing", "ready", "archived", "dropped"}
        if value not in allowed:
            raise ValueError("收藏状态不合法")
        return value

    @field_validator("title", "content_text", "note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """规范化标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None

    @model_validator(mode="after")
    def validate_payload(self) -> "CollectionCreate":
        """校验收藏主体内容。"""
        if self.type in {"image", "file"} and not self.assets:
            raise ValueError("图片或文件收藏至少需要一个附件")
        if not any([self.title, self.content_text, self.note, self.assets]):
            raise ValueError("收藏内容不能为空")
        return self


class CollectionUpdate(BaseModel):
    """更新收藏请求。"""

    type: str | None = None
    title: str | None = Field(default=None, max_length=300)
    content_text: str | None = None
    note: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    assets: list[CollectionAssetInput] | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验收藏类型。"""
        if value is None:
            return None
        allowed = {"link", "text", "image", "file"}
        if value not in allowed:
            raise ValueError("收藏类型不合法")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        """校验收藏状态。"""
        if value is None:
            return None
        allowed = {"inbox", "processing", "ready", "archived", "dropped"}
        if value not in allowed:
            raise ValueError("收藏状态不合法")
        return value

    @field_validator("title", "content_text", "note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _规范化可选文本(value)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """规范化标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None


class CollectionAssetRead(BaseModel):
    """收藏附件响应。"""

    id: UUID
    file_id: UUID
    sort_order: int
    created_at: datetime
    file: FileRead


class CollectionRead(BaseModel):
    """收藏详情响应。"""

    id: UUID
    type: str
    title: str | None = None
    content_text: str | None = None
    note: str | None = None
    status: str
    tags: list[str] | None = None
    assets: list[CollectionAssetRead] = Field(default_factory=list)
    archived_at: datetime | None = None
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CollectionTagRead(BaseModel):
    """收藏标签统计。"""

    name: str
    count: int


class CollectionBatchStatusUpdate(BaseModel):
    """批量更新收藏状态请求。"""

    ids: list[UUID] = Field(min_length=1, max_length=200)
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """校验收藏状态。"""
        allowed = {"inbox", "processing", "ready", "archived", "dropped"}
        if value not in allowed:
            raise ValueError("收藏状态不合法")
        return value


class CollectionConvertResult(BaseModel):
    """收藏转出结果。"""

    collection_id: UUID
    target_type: str
    target_id: UUID
    message: str
