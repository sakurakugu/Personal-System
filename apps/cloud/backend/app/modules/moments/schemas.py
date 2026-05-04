"""动态相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import UserRead


class MomentCreate(BaseModel):
    """发布动态请求。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentDraftSave(BaseModel):
    """保存草稿请求。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentImageRead(BaseModel):
    """动态图片响应。"""

    id: UUID
    original_name: str
    url: str
    preview_url: str
    thumbnail_url: str | None = None
    size: int
    mime_type: str
    sort_order: int
    created_at: datetime


class MomentImageOrderUpdate(BaseModel):
    """动态图片排序请求。"""

    image_ids: list[UUID] = Field(default_factory=list, max_length=20)


class MomentRead(BaseModel):
    """动态数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    is_published: bool
    view_count: int
    like_count: int
    liked: bool = False
    user_id: UUID
    images: list[MomentImageRead] = []
    is_deleted: bool = False
    deleted_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MomentPublicRead(BaseModel):
    """公开的动态信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    view_count: int
    like_count: int
    liked: bool = False
    images: list[MomentImageRead] = []
    published_at: datetime
    user: UserRead


class MomentDraftRead(BaseModel):
    """草稿信息响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    content: str
    images: list[MomentImageRead] = []
    is_deleted: bool = False
    deleted_at: datetime | None = None
    updated_at: datetime


class MomentLikeRead(BaseModel):
    """动态点赞操作响应。"""

    like_count: int
    changed: bool
    liked: bool


class MomentViewRead(BaseModel):
    """动态浏览操作响应。"""

    view_count: int
    changed: bool
