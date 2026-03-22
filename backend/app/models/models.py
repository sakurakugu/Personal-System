"""SQLAlchemy ORM 模型 – 所有数据表定义在此。

此模块定义了所有数据库表的 ORM 模型，包括：
- 用户、角色管理
- 文章、分类、标签
- 评论（支持嵌套回复）
- 待办事项、文件管理
- 友链、公告、动态
- 系统设置、页面访问统计
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.utils.uuid import generate_uuid7


# ── 辅助函数 ──────────────────────────────────────────────

def _utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


# ── 枚举 ────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """用户角色枚举。"""
    super_admin = "super_admin"  # 超级管理员，拥有所有权限
    admin = "admin"  # 管理员
    user = "user"  # 普通用户


class ArticleStatus(str, enum.Enum):
    """文章状态枚举。"""
    draft = "draft"  # 草稿
    published = "published"  # 已发布


class CommentStatus(str, enum.Enum):
    """评论状态枚举。"""
    pending = "pending"  # 待审核
    approved = "approved"  # 已通过
    rejected = "rejected"  # 已拒绝


class TodoStatus(str, enum.Enum):
    """待办事项状态枚举。"""
    todo = "todo"  # 待办
    in_progress = "in_progress"  # 进行中
    done = "done"  # 已完成


# 系统设置键名常量
SYSTEM_SETTING_COMMENTS_ENABLED = "comments_enabled"  # 评论功能开关
SYSTEM_SETTING_COMMENTS_STEALTH = "comments_stealth"  # 评论隐身模式开关
SYSTEM_SETTING_COMMENTS_MIN_ROLE = "comments_min_role"  # 评论最低可见角色
SYSTEM_SETTING_REGISTER_ENABLED = "register_enabled"  # 注册开关


# ── 用户 ────────────────────────────────────────────────

class User(Base):
    """用户模型。"""
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(50))  # 显示昵称
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))  # 头像 URL
    bio: Mapped[str | None] = mapped_column(Text)  # 个人简介
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 账户是否激活
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # 关系：用户拥有的内容
    articles: Mapped[list["Article"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    todos: Mapped[list["Todo"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    moments: Mapped[list["Moment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    liked_comments: Mapped[list["CommentLike"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ── 分类 ────────────────────────────────────────────────

class Category(Base):
    """文章分类模型。"""
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)  # URL 友好的标识
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    articles: Mapped[list["Article"]] = relationship(back_populates="category")


# ── 标签 ────────────────────────────────────────────────

class Tag(Base):
    """文章标签模型。"""
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)  # URL 友好的标识
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    articles: Mapped[list["Article"]] = relationship(secondary="article_tags", back_populates="tags")


# ── 文章 - 标签关联表 ─────────────────────────────────────

class ArticleTag(Base):
    """文章和标签的多对多关联表。"""
    __tablename__ = "article_tags"
    __table_args__ = (
        UniqueConstraint("article_id", "tag_id"),  # 防止重复关联
    )

    article_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


# ── 文章 ────────────────────────────────────────────────

class Article(Base):
    """文章模型。"""
    __tablename__ = "articles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)  # URL 友好的唯一标识
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")  # Markdown 内容
    excerpt: Mapped[str | None] = mapped_column(String(500))  # 摘要
    cover_url: Mapped[str | None] = mapped_column(String(500))  # 封面图 URL
    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), default=ArticleStatus.draft, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 浏览次数
    author_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 发布时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    author: Mapped["User"] = relationship(back_populates="articles")
    category: Mapped["Category | None"] = relationship(back_populates="articles")
    tags: Mapped[list["Tag"]] = relationship(secondary="article_tags", back_populates="articles")
    comments: Mapped[list["Comment"]] = relationship(back_populates="article", cascade="all, delete-orphan")


# ── 评论 ────────────────────────────────────────────────

class CommentLike(Base):
    """评论点赞关联表。"""
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id"),  # 防止重复点赞
    )

    comment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    comment: Mapped["Comment"] = relationship(back_populates="likes")
    user: Mapped["User"] = relationship(back_populates="liked_comments")


class Comment(Base):
    """评论模型，支持嵌套回复和点赞。"""
    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    article_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))  # 游客评论为 None
    guest_name: Mapped[str | None] = mapped_column(String(100))  # 游客名称
    parent_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"))  # 回复的评论 ID
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommentStatus] = mapped_column(Enum(CommentStatus), default=CommentStatus.pending, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 点赞数缓存
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    article: Mapped["Article"] = relationship(back_populates="comments")
    user: Mapped["User | None"] = relationship(back_populates="comments")
    parent: Mapped["Comment | None"] = relationship(remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    likes: Mapped[list["CommentLike"]] = relationship(back_populates="comment", cascade="all, delete-orphan")


class SystemSetting(Base):
    """系统设置模型，键值对存储。"""
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)  # 设置项键名
    bool_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # 布尔值（可选）
    str_value: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 字符串值（可选）
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


# ── 待办事项 ──────────────────────────────────────────────

class Todo(Base):
    """待办事项模型。"""
    __tablename__ = "todos"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TodoStatus] = mapped_column(Enum(TodoStatus), default=TodoStatus.todo, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 1=高, 2=中, 3=低
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 截止日期
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="todos")


# ── 文件 ────────────────────────────────────────────────

class File(Base):
    """上传文件模型。"""
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)  # 原始文件名
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)  # MinIO 存储路径
    url: Mapped[str] = mapped_column(String(1000), nullable=False)  # 访问 URL
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # 文件大小（字节）
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME 类型
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="files")


# ── 页面访问（分析） ──────────────────────────────────────

class PageView(Base):
    """页面访问记录模型，用于统计分析。"""
    __tablename__ = "page_views"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)  # 访问路径
    article_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("articles.id", ondelete="SET NULL"))
    ip_hash: Mapped[str | None] = mapped_column(String(64))  # IP 地址哈希（隐私保护）
    user_agent: Mapped[str | None] = mapped_column(String(500))  # 用户代理字符串
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)


# ── 友链 ────────────────────────────────────────────────

class LinkStatus(str, enum.Enum):
    """友链状态枚举。"""
    pending = "pending"      # 待审核
    approved = "approved"    # 已通过
    rejected = "rejected"    # 已拒绝


class Link(Base):
    """友情链接模型。"""
    __tablename__ = "links"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 网站名称
    url: Mapped[str] = mapped_column(String(500), nullable=False)  # 网站 URL
    description: Mapped[str | None] = mapped_column(String(200))  # 描述
    logo_url: Mapped[str | None] = mapped_column(String(500))  # Logo URL
    status: Mapped[LinkStatus] = mapped_column(Enum(LinkStatus), default=LinkStatus.pending, nullable=False)
    is_auto_exchange: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 是否自动交换
    contact_email: Mapped[str | None] = mapped_column(String(255))  # 联系邮箱
    contact_name: Mapped[str | None] = mapped_column(String(100))  # 联系人
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


# ── 公告 ────────────────────────────────────────────────

class Announcement(Base):
    """公告模型。"""
    __tablename__ = "announcements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 支持 Markdown
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 是否生效
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    author: Mapped["User"] = relationship(foreign_keys=[created_by])


# ── 动态（短内容/Moments）────────────────────────────────────

class Moment(Base):
    """动态/短内容模型，支持 Markdown，最多1000字。

    每个用户只有一个草稿（is_published=False），
    发布后会保留历史记录。
    """

    __tablename__ = "moments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    title: Mapped[str | None] = mapped_column(String(100))  # 标题可选
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown 内容，最多1000字
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 是否已发布
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 发布时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="moments")
