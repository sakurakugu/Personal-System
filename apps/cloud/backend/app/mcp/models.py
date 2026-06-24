"""MCP 数据库模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7


class MCP操作状态(str, enum.Enum):
    """MCP 操作状态。"""

    success = "success"
    failed = "failed"
    undone = "undone"


class MCP操作日志(Base):
    """MCP 工具调用操作日志。"""

    __tablename__ = "mcp_operation_logs"
    __table_args__ = (
        Index("ix_mcp_operation_logs_user_created_at", "user_id", "created_at"),
        Index("ix_mcp_operation_logs_session_created_at", "device_session_id", "created_at"),
        Index("ix_mcp_operation_logs_tool_created_at", "tool_name", "created_at"),
        Index("ix_mcp_operation_logs_target", "target_type", "target_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_device_sessions.id", ondelete="SET NULL"),
    )
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[MCP操作状态] = mapped_column(
        Enum(MCP操作状态, name="mcpoperationstatus"),
        nullable=False,
        default=MCP操作状态.success,
    )
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[str | None] = mapped_column(String(80))
    args_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_undoable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    undo_tool_name: Mapped[str | None] = mapped_column(String(120))
    undoable_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    undone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    undone_by_operation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("mcp_operation_logs.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
