"""设备会话模型。"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class 设备会话类型(str, enum.Enum):
    """设备会话类型。"""

    desktop = "desktop"
    mcp = "mcp"
    phone = "phone"
    other = "other"


class 设备会话范围(str, enum.Enum):
    """设备会话权限范围。"""

    full_client = "full_client"
    mcp_readonly = "mcp_readonly"
    mcp_full = "mcp_full"


class 用户设备会话(Base):
    """用户设备会话。"""

    __tablename__ = "user_device_sessions"
    __table_args__ = (
        Index("ix_user_device_sessions_user_id_revoked_at", "user_id", "revoked_at"),
        Index("ix_user_device_sessions_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[设备会话类型] = mapped_column(
        Enum(设备会话类型, name="devicesessiontype"),
        nullable=False,
    )
    scope: Mapped[设备会话范围] = mapped_column(
        Enum(设备会话范围, name="devicesessionscope"),
        nullable=False,
    )
    client_version: Mapped[str | None] = mapped_column(String(50))
    platform: Mapped[str | None] = mapped_column(String(50))
    last_ip: Mapped[str | None] = mapped_column(String(64))
    last_user_agent: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
