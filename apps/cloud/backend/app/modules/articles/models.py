"""文章相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.users.models import 用户


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class 文章状态(str, enum.Enum):
    """文章状态枚举。"""

    private = "private"
    login_required = "login_required"
    public = "public"


class 分类(Base):
    """文章分类模型。"""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    article_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    articles: Mapped[list["文章"]] = relationship(back_populates="category")


class 标签(Base):
    """文章标签模型。"""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    articles: Mapped[list["文章"]] = relationship(secondary="article_tags", back_populates="tags")


class 文章标签(Base):
    """文章和标签的关联表。"""

    __tablename__ = "article_tags"
    __table_args__ = (
        Index("ix_article_tags_tag_id", "tag_id"),
    )

    article_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class 文章(Base):
    """文章模型。"""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_articles_deleted_state",
        ),
        Index("ix_articles_author_id_created_at", "author_id", "created_at"),
        Index("ix_articles_category_id", "category_id"),
        Index("ix_articles_author_id_is_deleted_created_at", "author_id", "is_deleted", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    excerpt: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(500))
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_edited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    author: Mapped["用户"] = relationship(back_populates="articles")
    category: Mapped["分类 | None"] = relationship(back_populates="articles")
    tags: Mapped[list["标签"]] = relationship(secondary="article_tags", back_populates="articles")
    images: Mapped[list["文章图片"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )
    blog: Mapped["博客发布 | None"] = relationship(back_populates="article", cascade="all, delete-orphan", uselist=False)

    @property
    def status(self) -> str:
        return self.blog.status if self.blog and self.blog.is_published else "private"

    @property
    def published_at(self) -> datetime | None:
        return self.blog.published_at if self.blog and self.blog.is_published else None

    @property
    def view_count(self) -> int:
        return self.blog.view_count if self.blog else 0

    @property
    def like_count(self) -> int:
        return self.blog.like_count if self.blog else 0

    @property
    def has_unpublished_changes(self) -> bool:
        return self.blog is None or self.revision != self.blog.source_revision


class 博客发布(Base):
    """保存最近一次发布的完整内容，撤下时保留快照和统计。"""

    __tablename__ = "blog_publications"
    __table_args__ = (
        CheckConstraint("status IN ('public', 'login_required')", name="ck_blog_visibility"),
        Index("ix_blog_published_at", "is_published", "published_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(500))
    category_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    tags_snapshot: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_edited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    article: Mapped[文章] = relationship(back_populates="blog")
    author: Mapped["用户"] = relationship()

    @property
    def category(self):
        return SimpleNamespace(**self.category_snapshot) if self.category_snapshot else None

    @property
    def tags(self):
        return [SimpleNamespace(**item) for item in self.tags_snapshot]

    @property
    def is_deleted(self) -> bool:
        return self.article.is_deleted


class 文章图片(Base):
    """文章图片模型。"""

    __tablename__ = "article_images"
    __table_args__ = (
        Index("ix_article_images_article_id_created_at", "article_id", "created_at"),
        Index("ix_article_images_storage_key", "storage_key"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    article_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    article: Mapped["文章"] = relationship(back_populates="images")
