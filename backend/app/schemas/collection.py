"""收藏模块相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.file import FileRead


def _normalize_optional_text(value: str | None) -> str | None:
    """规范化可选文本字段。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class CollectionAssetInput(BaseModel):
    """收藏附件写入参数。"""

    file_id: UUID
    asset_role: str = "attachment"
    sort_order: int = Field(default=0, ge=0, le=9999)

    @field_validator("asset_role")
    @classmethod
    def validate_asset_role(cls, value: str) -> str:
        """校验附件角色。"""
        allowed = {"original", "cover", "attachment", "screenshot"}
        if value not in allowed:
            raise ValueError("附件角色不合法")
        return value


class CollectionCreate(BaseModel):
    """创建收藏请求。"""

    type: str = "link"
    source_type: str = "manual"
    title: str | None = Field(default=None, max_length=300)
    url: str | None = Field(default=None, max_length=1000)
    site_name: str | None = Field(default=None, max_length=120)
    cover_url: str | None = Field(default=None, max_length=500)
    content_text: str | None = None
    ocr_text: str | None = None
    summary: str | None = None
    note: str | None = None
    status: str = "inbox"
    ai_status: str = "pending"
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

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        """校验收藏来源。"""
        allowed = {"web", "wechat", "manual", "screenshot"}
        if value not in allowed:
            raise ValueError("收藏来源不合法")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """校验收藏状态。"""
        allowed = {"inbox", "processing", "ready", "archived", "dropped"}
        if value not in allowed:
            raise ValueError("收藏状态不合法")
        return value

    @field_validator("ai_status")
    @classmethod
    def validate_ai_status(cls, value: str) -> str:
        """校验 AI 状态。"""
        allowed = {"pending", "running", "done", "failed"}
        if value not in allowed:
            raise ValueError("AI 状态不合法")
        return value

    @field_validator("title", "url", "site_name", "cover_url", "content_text", "ocr_text", "summary", "note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _normalize_optional_text(value)

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
        if self.type == "link" and not self.url:
            raise ValueError("链接收藏必须填写 URL")
        if self.type in {"image", "file"} and not self.assets:
            raise ValueError("图片或文件收藏至少需要一个附件")
        if not any([self.title, self.url, self.content_text, self.ocr_text, self.summary, self.note, self.assets]):
            raise ValueError("收藏内容不能为空")
        return self


class CollectionUpdate(BaseModel):
    """更新收藏请求。"""

    type: str | None = None
    source_type: str | None = None
    title: str | None = Field(default=None, max_length=300)
    url: str | None = Field(default=None, max_length=1000)
    site_name: str | None = Field(default=None, max_length=120)
    cover_url: str | None = Field(default=None, max_length=500)
    content_text: str | None = None
    ocr_text: str | None = None
    summary: str | None = None
    note: str | None = None
    status: str | None = None
    ai_status: str | None = None
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

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        """校验收藏来源。"""
        if value is None:
            return None
        allowed = {"web", "wechat", "manual", "screenshot"}
        if value not in allowed:
            raise ValueError("收藏来源不合法")
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

    @field_validator("ai_status")
    @classmethod
    def validate_ai_status(cls, value: str | None) -> str | None:
        """校验 AI 状态。"""
        if value is None:
            return None
        allowed = {"pending", "running", "done", "failed"}
        if value not in allowed:
            raise ValueError("AI 状态不合法")
        return value

    @field_validator("title", "url", "site_name", "cover_url", "content_text", "ocr_text", "summary", "note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """统一去除首尾空白。"""
        return _normalize_optional_text(value)

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
    asset_role: str
    sort_order: int
    created_at: datetime
    file: FileRead


class CollectionRead(BaseModel):
    """收藏详情响应。"""

    id: UUID
    type: str
    source_type: str
    title: str | None = None
    url: str | None = None
    site_name: str | None = None
    cover_url: str | None = None
    content_text: str | None = None
    ocr_text: str | None = None
    summary: str | None = None
    note: str | None = None
    status: str
    ai_status: str
    tags: list[str] | None = None
    assets: list[CollectionAssetRead] = Field(default_factory=list)
    archived_at: datetime | None = None
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
