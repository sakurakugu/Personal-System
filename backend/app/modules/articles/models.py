"""文章相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.users.models import User


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class ArticleStatus(str, enum.Enum):
    """文章状态枚举。"""

    private = "private"
    login_required = "login_required"
    public = "public"


class Category(Base):
    """文章分类模型。"""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    article_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    articles: Mapped[list["Article"]] = relationship(back_populates="category")


class Tag(Base):
    """文章标签模型。"""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    articles: Mapped[list["Article"]] = relationship(secondary="article_tags", back_populates="tags")


class ArticleTag(Base):
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


class Article(Base):
    """文章模型。"""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "(status = 'private' AND published_at IS NULL) OR "
            "(status IN ('login_required', 'public') AND published_at IS NOT NULL)",
            name="ck_articles_status_published_at",
        ),
        Index("ix_articles_status_published_at", "status", "published_at"),
        Index("ix_articles_author_id_created_at", "author_id", "created_at"),
        Index("ix_articles_category_id", "category_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    excerpt: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), default=ArticleStatus.private, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_edited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    author: Mapped["User"] = relationship(back_populates="articles")
    category: Mapped["Category | None"] = relationship(back_populates="articles")
    tags: Mapped[list["Tag"]] = relationship(secondary="article_tags", back_populates="articles")
    images: Mapped[list["ArticleImage"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )


class ArticleImage(Base):
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

    article: Mapped["Article"] = relationship(back_populates="images")
