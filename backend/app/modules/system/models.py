"""系统设置模型与常量。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.session import Base

SYSTEM_SETTING_COMMENTS_ENABLED = "comments_enabled"
SYSTEM_SETTING_COMMENTS_STEALTH = "comments_stealth"
SYSTEM_SETTING_COMMENTS_MIN_ROLE = "comments_min_role"
SYSTEM_SETTING_REGISTER_ENABLED = "register_enabled"


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    from datetime import timezone

    return datetime.now(timezone.utc)


class SystemSetting(Base):
    """系统设置模型。"""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    bool_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    str_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
