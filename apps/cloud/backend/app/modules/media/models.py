"""作品推荐模块相关模型。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
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
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_media_items_deleted_state",
        ),
        ForeignKeyConstraint(["primary_cover_asset_id"], ["media_assets.id"], ondelete="SET NULL", use_alter=True),
        Index(
            "ix_media_items_user_id_is_deleted_media_type_status_created_at",
            "user_id",
            "is_deleted",
            "media_type",
            "status",
            "created_at",
        ),
        Index("ix_media_items_user_id_is_deleted_status_created_at", "user_id", "is_deleted", "status", "created_at"),
        Index("ix_media_items_user_id_is_deleted_rating_created_at", "user_id", "is_deleted", "rating", "created_at"),
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
    personal_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    release_date: Mapped[date | None] = mapped_column(Date)
    primary_cover_asset_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship(back_populates="media_items")
    primary_cover_asset: Mapped["文娱资源 | None"] = relationship(
        foreign_keys="文娱条目.primary_cover_asset_id",
        post_update=True,
    )
    assets: Mapped[list["文娱资源"]] = relationship(
        back_populates="media_item",
        cascade="all, delete-orphan",
        foreign_keys="文娱资源.media_item_id",
    )
    external_sources: Mapped[list["文娱外部来源"]] = relationship(
        back_populates="media_item",
        cascade="all, delete-orphan",
    )


class 文娱外部来源(Base):
    """作品外部来源记录。"""

    __tablename__ = "media_external_sources"
    __table_args__ = (
        UniqueConstraint("media_item_id", "provider", "external_id", name="uq_media_external_sources_item_provider_id"),
        Index("ix_media_external_sources_provider_external_id", "provider", "external_id"),
        Index("ix_media_external_sources_media_item_id", "media_item_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    media_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(1000))
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    media_item: Mapped["文娱条目"] = relationship(back_populates="external_sources")


class 文娱资源(Base):
    """作品封面、横幅、截图等业务资源。"""

    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('cover', 'backdrop', 'screenshot', 'logo', 'other')",
            name="ck_media_assets_asset_type",
        ),
        Index("ix_media_assets_media_item_id_asset_type_is_primary", "media_item_id", "asset_type", "is_primary"),
        Index("ix_media_assets_user_id_media_item_id", "user_id", "media_item_id"),
        Index("ix_media_assets_storage_key", "storage_key"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    media_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500), unique=True)
    external_url: Mapped[str | None] = mapped_column(String(1000))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    source_provider: Mapped[str | None] = mapped_column(String(64))
    source_asset_id: Mapped[str | None] = mapped_column(String(200))
    original_name: Mapped[str | None] = mapped_column(String(300))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    size: Mapped[int | None] = mapped_column(Integer)
    attribution: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(String(300))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship()
    media_item: Mapped["文娱条目"] = relationship(
        back_populates="assets",
        foreign_keys=[media_item_id],
    )
