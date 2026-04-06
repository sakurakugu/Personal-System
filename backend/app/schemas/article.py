"""文章相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class CategoryCreate(BaseModel):
    """创建分类请求。"""

    name: str = Field(max_length=100)
    description: str | None = None


class CategoryRead(BaseModel):
    """分类数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime


class TagCreate(BaseModel):
    """创建标签请求。"""

    name: str = Field(max_length=60)


class TagRead(BaseModel):
    """标签数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class ArticleCreate(BaseModel):
    """创建文章请求。"""

    title: str = Field(max_length=300)
    content: str = ""
    excerpt: str | None = None
    cover_url: str | None = None
    status: str = "private"
    category_id: UUID | None = None
    tag_ids: list[UUID] = []


class ArticleUpdate(BaseModel):
    """更新文章请求。"""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class ArticleRead(BaseModel):
    """文章详情响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    content: str
    excerpt: str | None = None
    cover_url: str | None = None
    status: str
    view_count: int
    author: UserRead
    category: CategoryRead | None = None
    tags: list[TagRead] = []
    published_at: datetime | None = None
    created_at: datetime
    last_edited_at: datetime
    updated_at: datetime # 这个如果观看次数+1也会变，因此新增了 last_edited_at 字段来专门记录内容修改时间


class ArticleListItem(BaseModel):
    """文章列表项响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    excerpt: str | None = None
    cover_url: str | None = None
    status: str
    view_count: int
    author: UserRead
    category: CategoryRead | None = None
    tags: list[TagRead] = []
    published_at: datetime | None = None
    created_at: datetime
    last_edited_at: datetime
