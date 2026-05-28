"""AI 对话模块 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

AI访问策略 = Literal["login", "admin", "super_admin"]
AI供应商 = Literal["openai", "openai_compatible", "local"]
AI消息角色 = Literal["system", "user", "assistant"]


class AI消息Part(BaseModel):
    """聊天消息片段。"""

    type: str = Field(default="text", max_length=50)
    text: str | None = None


class AI聊天消息(BaseModel):
    """聊天消息。"""

    id: str | None = Field(default=None, max_length=100)
    role: AI消息角色
    content: str = Field(default="", max_length=20000)
    parts: list[AI消息Part] | None = None

    @field_validator("content")
    @classmethod
    def 规范化内容(cls, value: str) -> str:
        """去除首尾空白。"""
        return value.strip()


class AI聊天请求(BaseModel):
    """AI 聊天请求。"""

    messages: list[AI聊天消息] = Field(min_length=1, max_length=40)


class AI设置读取(BaseModel):
    """AI 设置读取响应。"""

    enabled: bool
    access_policy: AI访问策略
    provider: str
    base_url: str
    model: str
    max_tokens: int
    timeout_seconds: float
    system_prompt: str
    allow_attachments: bool
    max_attachment_size_mb: int
    daily_limit_per_user: int
    has_secret: bool
    secret_updated_at: datetime | None = None
    updated_at: datetime | None = None


class AI设置更新(BaseModel):
    """AI 设置更新请求。"""

    enabled: bool | None = None
    access_policy: AI访问策略 | None = None
    provider: str | None = Field(default=None, max_length=64)
    base_url: str | None = Field(default=None, max_length=1000)
    model: str | None = Field(default=None, max_length=200)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    timeout_seconds: float | None = Field(default=None, ge=1, le=300)
    system_prompt: str | None = Field(default=None, max_length=20000)
    allow_attachments: bool | None = None
    max_attachment_size_mb: int | None = Field(default=None, ge=1, le=200)
    daily_limit_per_user: int | None = Field(default=None, ge=0, le=100000)


class AI密钥更新(BaseModel):
    """AI 密钥更新请求。"""

    secret: str = Field(min_length=1, max_length=10000)


class AI测试请求(BaseModel):
    """AI 测试请求。"""

    message: str = Field(min_length=1, max_length=4000)


class AI测试响应(BaseModel):
    """AI 测试响应。"""

    content: str
    duration_ms: int


class AI调用日志读取(BaseModel):
    """AI 调用日志读取响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    provider: str
    model: str
    status: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    duration_ms: int
    message_count: int
    attachment_count: int
    error_type: str | None
    error_message: str | None
    created_at: datetime


class AI调用日志列表(BaseModel):
    """AI 调用日志列表。"""

    items: list[AI调用日志读取]
    total: int
    page: int
    page_size: int
    pages: int
