"""首页 Feed 流模型。"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.models.user import User


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class FeedItemType(str, enum.Enum):
    """Feed 条目类型。"""

    article = "article"
    moment = "moment"


class FeedItem(Base):
    """首页时间流条目。"""

    __tablename__ = "feed_items"
    __table_args__ = (
        Index("ix_feed_items_is_visible_published_at", "is_visible", "published_at"),
        Index("ix_feed_items_author_id_published_at", "author_id", "published_at"),
        Index("uq_feed_items_type_source_id", "type", "source_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    type: Mapped[FeedItemType] = mapped_column(Enum(FeedItemType), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    author: Mapped["User"] = relationship(foreign_keys=[author_id])
