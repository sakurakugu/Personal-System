"""资料库模块相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.files.schemas import FileRead

资料状态值 = {"active", "archived"}
资料类型值 = {"link", "text", "image", "file"}


def _规范化可选文本(value: str | None) -> str | None:
    """规范化可选文本字段。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class 资料资产输入(BaseModel):
    """资料库附件写入参数。"""

    file_id: UUID
    sort_order: int = Field(default=0, ge=0, le=9999)


class 资料创建(BaseModel):
    """创建资料库条目请求。"""

    type: str = "link"
    title: str | None = Field(default=None, max_length=300)
    content_text: str | None = None
    note: str | None = None
    status: str = "active"
    tags: list[str] | None = None
    assets: list[资料资产输入] | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验资料库类型。"""
        if value not in 资料类型值:
            raise ValueError("资料库类型不合法")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """校验资料库状态。"""
        if value not in 资料状态值:
            raise ValueError("资料库状态不合法")
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
    def validate_payload(self) -> "资料创建":
        """校验资料库条目主体内容。"""
        if self.type in {"image", "file"} and not self.assets:
            raise ValueError("图片或文件资料至少需要一个附件")
        if not any([self.title, self.content_text, self.note, self.assets]):
            raise ValueError("资料库内容不能为空")
        return self


class 资料更新(BaseModel):
    """更新资料库条目请求。"""

    type: str | None = None
    title: str | None = Field(default=None, max_length=300)
    content_text: str | None = None
    note: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    assets: list[资料资产输入] | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验资料库类型。"""
        if value is None:
            return None
        if value not in 资料类型值:
            raise ValueError("资料库类型不合法")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        """校验资料库状态。"""
        if value is None:
            return None
        if value not in 资料状态值:
            raise ValueError("资料库状态不合法")
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


class 资料资产信息(BaseModel):
    """资料库附件响应。"""

    id: UUID
    file_id: UUID
    sort_order: int
    created_at: datetime
    file: FileRead


class 资料信息(BaseModel):
    """资料库条目详情响应。"""

    id: UUID
    type: str
    title: str | None = None
    content_text: str | None = None
    note: str | None = None
    status: str
    tags: list[str] | None = None
    assets: list[资料资产信息] = Field(default_factory=list)
    archived_at: datetime | None = None
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class 资料标签信息(BaseModel):
    """资料库标签统计。"""

    name: str
    count: int


class 资料批量状态更新(BaseModel):
    """批量更新资料库状态请求。"""

    ids: list[UUID] = Field(min_length=1, max_length=200)
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """校验资料库状态。"""
        if value not in 资料状态值:
            raise ValueError("资料库状态不合法")
        return value
