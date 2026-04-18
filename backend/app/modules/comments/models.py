"""评论相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import utcnow
from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.user import User


class CommentStatus(str, enum.Enum):
    """评论状态枚举。"""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CommentLike(Base):
    """评论点赞关联表。"""

    __tablename__ = "comment_likes"

    comment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    comment: Mapped["Comment"] = relationship(back_populates="likes")
    user: Mapped["User"] = relationship(back_populates="liked_comments")


class Comment(Base):
    """评论模型。"""

    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_name IS NULL) OR (user_id IS NULL AND guest_name IS NOT NULL)",
            name="ck_comments_author_identity",
        ),
        Index("ix_comments_article_id_status_created_at", "article_id", "status", "created_at"),
        Index("ix_comments_status_created_at", "status", "created_at"),
        Index("ix_comments_parent_id_created_at", "parent_id", "created_at"),
        Index("ix_comments_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    article_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    guest_name: Mapped[str | None] = mapped_column(String(100))
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommentStatus] = mapped_column(Enum(CommentStatus), default=CommentStatus.pending, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    article: Mapped["Article"] = relationship(back_populates="comments")
    user: Mapped["User | None"] = relationship(back_populates="comments")
    parent: Mapped["Comment | None"] = relationship(remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    likes: Mapped[list["CommentLike"]] = relationship(back_populates="comment", cascade="all, delete-orphan")
