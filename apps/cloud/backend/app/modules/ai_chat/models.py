"""AI 对话配置与调用日志模型。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.session import Base
from app.shared.db.timestamps import utcnow
from app.utils.uuid import generate_uuid7


class AI设置(Base):
    """AI 对话运行配置。"""

    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    access_policy: Mapped[str] = mapped_column(String(32), default="login", nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="openai_compatible", nullable=False)
    base_url: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    model: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(default=30.0, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    allow_attachments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_attachment_size_mb: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    daily_limit_per_user: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    secret_ciphertext: Mapped[str | None] = mapped_column(Text)
    secret_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class AI调用日志(Base):
    """AI 对话调用日志。"""

    __tablename__ = "ai_call_logs"
    __table_args__ = (
        Index("ix_ai_call_logs_user_id_created_at", "user_id", "created_at"),
        Index("ix_ai_call_logs_status_created_at", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attachment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
