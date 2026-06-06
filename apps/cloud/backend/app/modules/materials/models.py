"""资料库模块相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.files.models import File
    from app.modules.users.models import 用户


class 资料类型(str, enum.Enum):
    """资料库内容类型。"""

    link = "link"
    text = "text"
    image = "image"
    file = "file"


class 资料状态(str, enum.Enum):
    """资料库整理状态。"""

    active = "active"
    archived = "archived"


class 资料(Base):
    """资料库条目主体模型。"""

    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_materials_deleted_state",
        ),
        Index("ix_materials_user_id_is_deleted_status_created_at", "user_id", "is_deleted", "status", "created_at"),
        Index("ix_materials_user_id_is_deleted_type_created_at", "user_id", "is_deleted", "type", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[资料类型] = mapped_column(
        Enum(资料类型, name="materialtype"),
        default=资料类型.link,
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(300))
    content_text: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[资料状态] = mapped_column(
        Enum(资料状态, name="materialstatus"),
        default=资料状态.active,
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

    user: Mapped["用户"] = relationship(back_populates="materials")
    assets: Mapped[list["资料资产"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="资料资产.sort_order.asc(), 资料资产.created_at.asc()",
    )
    material_tags: Mapped[list["资料标签"]] = relationship(
        secondary="material_tag_relations",
        back_populates="materials",
    )

    @property
    def tags(self) -> list[str] | None:
        """返回资料库标签名列表。"""
        if not self.material_tags:
            return None
        return [tag.name for tag in self.material_tags]


class 资料资产(Base):
    """资料库条目与文件的关联模型。"""

    __tablename__ = "material_assets"
    __table_args__ = (
        Index("ix_material_assets_material_id_sort_order", "material_id", "sort_order"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    material: Mapped["资料"] = relationship(back_populates="assets")
    file: Mapped["File"] = relationship()


class 资料标签(Base):
    """资料库标签模型。"""

    __tablename__ = "material_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_material_tags_user_id_name"),
        Index("ix_material_tags_user_id_name", "user_id", "name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    materials: Mapped[list["资料"]] = relationship(
        secondary="material_tag_relations",
        back_populates="material_tags",
    )


class 资料标签关联(Base):
    """资料库条目与标签的关联表。"""

    __tablename__ = "material_tag_relations"

    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("material_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
