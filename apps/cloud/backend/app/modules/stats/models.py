"""统计模块模型。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class PageView(Base):
    """页面访问记录模型。"""

    __tablename__ = "page_views"
    __table_args__ = (Index("ix_page_views_article_id_created_at", "article_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    article_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
