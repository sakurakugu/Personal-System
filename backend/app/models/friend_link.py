"""友链模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.common import utcnow
from app.utils.uuid import generate_uuid7


class FriendLinkStatus(str, enum.Enum):
    """友链状态枚举。"""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class FriendLink(Base):
    """友情链接模型。"""

    __tablename__ = "friend_links"
    __table_args__ = (Index("ix_friend_links_status_created_at", "status", "created_at"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(50), index=True)
    status: Mapped[FriendLinkStatus] = mapped_column(
        Enum(FriendLinkStatus, name="linkstatus"),
        default=FriendLinkStatus.pending,
        nullable=False,
    )
    is_auto_exchange: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
