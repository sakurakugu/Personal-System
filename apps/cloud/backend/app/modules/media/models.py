"""作品推荐模块相关模型。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.files.models import File
    from app.modules.users.models import 用户


class 文娱条目(Base):
    """作品推荐条目模型。"""

    __tablename__ = "media_items"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 15)", name="ck_media_items_rating_range"),
        CheckConstraint(
            "media_type IN ('game', 'novel', 'book', 'anime', 'comic', 'movie', 'tv', 'music', 'other')",
            name="ck_media_items_media_type",
        ),
        CheckConstraint(
            "status IN ('planned', 'doing', 'done', 'paused', 'dropped')",
            name="ck_media_items_status",
        ),
        Index(
            "ix_media_items_user_id_media_type_status_created_at",
            "user_id",
            "media_type",
            "status",
            "created_at",
        ),
        Index("ix_media_items_user_id_status_created_at", "user_id", "status", "created_at"),
        Index("ix_media_items_user_id_rating_created_at", "user_id", "rating", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(300))
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer)
    creator: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    genres: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    cover_file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship(back_populates="media_items")
    cover_file: Mapped["File | None"] = relationship()
