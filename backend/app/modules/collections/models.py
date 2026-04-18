"""收藏模块相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import utcnow
from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class CollectionType(str, enum.Enum):
    """收藏内容类型。"""

    link = "link"
    text = "text"
    image = "image"
    file = "file"


class CollectionStatus(str, enum.Enum):
    """收藏整理状态。"""

    inbox = "inbox"
    processing = "processing"
    ready = "ready"
    archived = "archived"
    dropped = "dropped"


class Collection(Base):
    """收藏主体模型。"""

    __tablename__ = "collections"
    __table_args__ = (
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_collections_deleted_state",
        ),
        Index("ix_collections_user_id_is_deleted_status_created_at", "user_id", "is_deleted", "status", "created_at"),
        Index("ix_collections_user_id_is_deleted_type_created_at", "user_id", "is_deleted", "type", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[CollectionType] = mapped_column(
        Enum(CollectionType, name="collectiontype"),
        default=CollectionType.link,
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(300))
    content_text: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CollectionStatus] = mapped_column(
        Enum(CollectionStatus, name="collectionstatus"),
        default=CollectionStatus.inbox,
        nullable=False,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="collections")
    assets: Mapped[list["CollectionAsset"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionAsset.sort_order.asc(), CollectionAsset.created_at.asc()",
    )
    collection_tags: Mapped[list["CollectionTag"]] = relationship(
        secondary="collection_tag_relations",
        back_populates="collections",
    )

    @property
    def tags(self) -> list[str] | None:
        """返回收藏标签名列表。"""
        if not self.collection_tags:
            return None
        return [tag.name for tag in self.collection_tags]


class CollectionAsset(Base):
    """收藏与文件的关联模型。"""

    __tablename__ = "collection_assets"
    __table_args__ = (
        Index("ix_collection_assets_collection_id_sort_order", "collection_id", "sort_order"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    collection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    collection: Mapped["Collection"] = relationship(back_populates="assets")
    file: Mapped["File"] = relationship()


class CollectionTag(Base):
    """收藏标签模型。"""

    __tablename__ = "collection_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_collection_tags_user_id_name"),
        Index("ix_collection_tags_user_id_name", "user_id", "name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    collections: Mapped[list["Collection"]] = relationship(
        secondary="collection_tag_relations",
        back_populates="collection_tags",
    )


class CollectionTagRelation(Base):
    """收藏与标签的关联表。"""

    __tablename__ = "collection_tag_relations"

    collection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("collection_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
