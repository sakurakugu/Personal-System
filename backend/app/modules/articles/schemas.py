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
    article_count: int = 0
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


class ArticleDraftCreate(BaseModel):
    """创建文章草稿请求。"""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class ArticleUpdate(BaseModel):
    """更新文章请求。"""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class ArticleImageRead(BaseModel):
    """文章图片响应。"""

    id: UUID
    original_name: str
    url: str
    preview_url: str
    thumbnail_url: str | None = None
    size: int
    mime_type: str
    created_at: datetime


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
    word_count: int
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
    word_count: int
    author: UserRead
    category: CategoryRead | None = None
    tags: list[TagRead] = []
    published_at: datetime | None = None
    created_at: datetime
    last_edited_at: datetime


class ArticleMetaRead(BaseModel):
    """文章最小元数据响应（用于日历、归档等场景）。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    published_at: datetime | None = None
    view_count: int = 0
    tags: list[TagRead] = []
    category: CategoryRead | None = None


class ArticleNavigationRead(BaseModel):
    """文章邻接导航响应。"""

    model_config = ConfigDict(from_attributes=True)

    title: str
    slug: str


class ArticleRelatedResponse(BaseModel):
    """文章相关推荐响应。"""

    prev: ArticleNavigationRead | None = None
    next: ArticleNavigationRead | None = None
    related: list[ArticleMetaRead]
    random: list[ArticleMetaRead]
