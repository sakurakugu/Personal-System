"""备忘录模块相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.users.models import 用户


class 备忘录状态(str, enum.Enum):
    """备忘录整理状态。"""

    inbox = "inbox"
    processed = "processed"
    archived = "archived"
    dropped = "dropped"


class 备忘录来源(str, enum.Enum):
    """备忘录来源。"""

    manual = "manual"
    wechat = "wechat"
    web = "web"
    share = "share"
    unknown = "unknown"


class 备忘录(Base):
    """备忘录主体模型。"""

    __tablename__ = "memos"
    __table_args__ = (
        CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR (status <> 'archived' AND archived_at IS NULL)",
            name="ck_memos_archived_state",
        ),
        CheckConstraint(
            "(deleted_at IS NULL AND status <> 'dropped') OR deleted_at IS NOT NULL",
            name="ck_memos_deleted_state",
        ),
        CheckConstraint(
            "(converted_to_type IS NULL AND converted_to_id IS NULL) OR "
            "(converted_to_type IS NOT NULL AND converted_to_id IS NOT NULL)",
            name="ck_memos_converted_target",
        ),
        Index("ix_memos_user_id_deleted_at_status_updated_at", "user_id", "deleted_at", "status", "updated_at"),
        Index("ix_memos_user_id_converted_to_type", "user_id", "converted_to_type"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[备忘录状态] = mapped_column(
        Enum(备忘录状态, name="memostatus"),
        default=备忘录状态.inbox,
        nullable=False,
    )
    source: Mapped[备忘录来源] = mapped_column(
        Enum(备忘录来源, name="memosource"),
        default=备忘录来源.manual,
        nullable=False,
    )
    converted_to_type: Mapped[str | None] = mapped_column(String(50))
    converted_to_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["用户"] = relationship(back_populates="memos")
