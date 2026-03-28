"""公告相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnnouncementCreate(BaseModel):
    """创建公告请求。"""

    title: str = Field(max_length=200)
    content: str = ""
    is_active: bool = True


class AnnouncementUpdate(BaseModel):
    """更新公告请求。"""

    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    is_active: bool | None = None


class AnnouncementRead(BaseModel):
    """公告数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class AnnouncementPublicRead(BaseModel):
    """公开可见的公告信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    created_at: datetime
