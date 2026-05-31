"""备忘录模块相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _规范化正文(value: str) -> str:
    """规范化备忘录正文。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("备忘录内容不能为空")
    return normalized


class 备忘录创建(BaseModel):
    """创建备忘录请求。"""

    content: str = Field(min_length=1)
    source: str = "manual"

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        """去除正文首尾空白。"""
        return _规范化正文(value)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """校验备忘录来源。"""
        allowed = {"manual", "wechat", "web", "share", "unknown"}
        if value not in allowed:
            raise ValueError("备忘录来源不合法")
        return value


class 备忘录更新(BaseModel):
    """更新备忘录请求。"""

    content: str | None = None
    status: str | None = None
    source: str | None = None

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str | None) -> str | None:
        """去除正文首尾空白。"""
        if value is None:
            return None
        return _规范化正文(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        """校验备忘录状态。"""
        if value is None:
            return None
        allowed = {"inbox", "processed", "archived", "dropped"}
        if value not in allowed:
            raise ValueError("备忘录状态不合法")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str | None) -> str | None:
        """校验备忘录来源。"""
        if value is None:
            return None
        allowed = {"manual", "wechat", "web", "share", "unknown"}
        if value not in allowed:
            raise ValueError("备忘录来源不合法")
        return value


class 备忘录信息(BaseModel):
    """备忘录详情响应。"""

    id: UUID
    content: str
    status: str
    source: str
    converted_to_type: str | None = None
    converted_to_id: UUID | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class 备忘录转换结果(BaseModel):
    """备忘录转出结果。"""

    memo_id: UUID
    target_type: str
    target_id: UUID
    message: str
