"""动态相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class MomentCreate(BaseModel):
    """发布动态请求。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentDraftSave(BaseModel):
    """保存草稿请求。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentRead(BaseModel):
    """动态数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    is_published: bool
    user_id: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MomentPublicRead(BaseModel):
    """公开的动态信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    published_at: datetime
    user: UserRead


class MomentDraftRead(BaseModel):
    """草稿信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    updated_at: datetime
