"""Pydantic v2 模式定义。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ═══════════════════════════════════════════════════════════
#  认证
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════════
#  用户
# ═══════════════════════════════════════════════════════════

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    email: str
    role: str
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    bio: str | None = None
    avatar_url: str | None = None


class UserCreateByAdmin(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool = True


class UserAdminUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    role: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None


class UserPasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


# ═══════════════════════════════════════════════════════════
#  分类
# ═══════════════════════════════════════════════════════════

class CategoryCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  标签
# ═══════════════════════════════════════════════════════════

class TagCreate(BaseModel):
    name: str = Field(max_length=60)


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  文章
# ═══════════════════════════════════════════════════════════

class ArticleCreate(BaseModel):
    title: str = Field(max_length=300)
    content: str = ""
    excerpt: str | None = None
    cover_url: str | None = None
    status: str = "draft"
    category_id: UUID | None = None
    tag_ids: list[UUID] = []


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class ArticleRead(BaseModel):
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
    updated_at: datetime


class ArticleListItem(BaseModel):
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


# ═══════════════════════════════════════════════════════════
#  评论
# ═══════════════════════════════════════════════════════════

class CommentCreate(BaseModel):
    article_id: UUID
    content: str = Field(min_length=1)
    parent_id: UUID | None = None
    guest_name: str | None = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    article_id: UUID
    user_id: UUID | None = None
    guest_name: str | None = None
    parent_id: UUID | None = None
    content: str
    status: str
    created_at: datetime
    user: UserRead | None = None
    replies: list["CommentRead"] = []


class CommentModerate(BaseModel):
    status: str  # approved / rejected


# ═══════════════════════════════════════════════════════════
#  待办事项
# ═══════════════════════════════════════════════════════════

class TodoCreate(BaseModel):
    title: str = Field(max_length=300)
    description: str | None = None
    priority: int = Field(default=2, ge=1, le=3)
    due_date: datetime | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    due_date: datetime | None = None


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None = None
    status: str
    priority: int
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
#  文件
# ═══════════════════════════════════════════════════════════

class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  统计 / 系统
# ═══════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_articles: int
    total_comments: int
    total_views: int
    total_todos: int
    recent_views: list[dict] = []  # [{date, count}, ...]


class SystemStatus(BaseModel):
    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    uptime_seconds: float


class SystemSettingsRead(BaseModel):
    comments_enabled: bool
    comments_stealth: bool


class SystemSettingsUpdate(BaseModel):
    comments_enabled: bool | None = None
    comments_stealth: bool | None = None


# ═══════════════════════════════════════════════════════════
#  分页响应
# ═══════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
