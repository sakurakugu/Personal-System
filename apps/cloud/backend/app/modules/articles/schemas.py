"""文章相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.users.schemas import 用户信息


class 分类创建(BaseModel):
    """创建分类请求。"""

    name: str = Field(max_length=100)
    description: str | None = None


class 分类信息(BaseModel):
    """分类数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    article_count: int = 0
    created_at: datetime


class 标签创建(BaseModel):
    """创建标签请求。"""

    name: str = Field(max_length=60)


class 标签信息(BaseModel):
    """标签数据响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class 文章创建(BaseModel):
    """创建文章请求。"""

    title: str = Field(max_length=300)
    content: str = ""
    excerpt: str | None = None
    cover_url: str | None = None
    status: str = "private"
    category_id: UUID | None = None
    tag_ids: list[UUID] = []


class 文章草稿创建(BaseModel):
    """创建文章草稿请求。"""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class 文章更新(BaseModel):
    """更新文章请求。"""

    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class 文章图片信息(BaseModel):
    """文章图片响应。"""

    id: UUID
    original_name: str
    url: str
    preview_url: str
    thumbnail_url: str | None = None
    size: int
    mime_type: str
    created_at: datetime


class 文章信息(BaseModel):
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
    like_count: int
    liked: bool = False
    word_count: int
    author: 用户信息
    category: 分类信息 | None = None
    tags: list[标签信息] = []
    is_deleted: bool = False
    deleted_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    last_edited_at: datetime
    updated_at: datetime # 这个如果观看次数+1也会变，因此新增了 last_edited_at 字段来专门记录内容修改时间


class 文章列表项(BaseModel):
    """文章列表项响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    excerpt: str | None = None
    cover_url: str | None = None
    status: str
    view_count: int
    like_count: int
    word_count: int
    author: 用户信息
    category: 分类信息 | None = None
    tags: list[标签信息] = []
    is_deleted: bool = False
    deleted_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    last_edited_at: datetime


class 文章元数据信息(BaseModel):
    """文章最小元数据响应（用于日历、归档等场景）。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    published_at: datetime | None = None
    view_count: int = 0
    like_count: int = 0
    author: 用户信息
    tags: list[标签信息] = []
    category: 分类信息 | None = None


class 文章点赞信息(BaseModel):
    """文章点赞操作响应。"""

    like_count: int
    changed: bool
    liked: bool


class 文章导航信息(BaseModel):
    """文章邻接导航响应。"""

    model_config = ConfigDict(from_attributes=True)

    title: str
    slug: str


class 文章相关响应(BaseModel):
    """文章相关推荐响应。"""

    prev: 文章导航信息 | None = None
    next: 文章导航信息 | None = None
    related: list[文章元数据信息]
    random: list[文章元数据信息]
