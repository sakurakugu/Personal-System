"""待办相关模型。"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import utcnow
from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.modules.users.models import User


class TodoStatus(str, enum.Enum):
    """待办状态枚举。"""

    todo = "todo"
    done = "done"


class RecurrenceType(str, enum.Enum):
    """循环类型枚举。"""

    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    workday = "workday"
    weekend = "weekend"
    holiday = "holiday"
    custom = "custom"


class Todo(Base):
    """待办事项模型。"""

    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint("importance >= 0 AND importance <= 100", name="ck_todos_importance_range"),
        CheckConstraint("urgency >= 0 AND urgency <= 100", name="ck_todos_urgency_range"),
        CheckConstraint("start_date IS NULL OR end_date IS NULL OR end_date >= start_date", name="ck_todos_date_range"),
        CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_todos_deleted_state",
        ),
        CheckConstraint(
            "recurrence_type IN ('none', 'daily', 'weekly', 'monthly', 'yearly', 'workday', 'weekend', 'holiday', 'custom')",
            name="ck_todos_recurrence_type",
        ),
        CheckConstraint("recurrence_count >= -1", name="ck_todos_recurrence_count_min"),
        CheckConstraint("times_per_interval >= 1", name="ck_todos_times_per_interval_min"),
        CheckConstraint(
            "interval_progress >= 0 AND interval_progress <= times_per_interval",
            name="ck_todos_interval_progress_range",
        ),
        Index("ix_todos_user_id_is_deleted_is_pinned_created_at", "user_id", "is_deleted", "is_pinned", "created_at"),
        Index("ix_todos_user_id_status", "user_id", "status"),
        Index("ix_todos_progress_reset_at", "progress_reset_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TodoStatus] = mapped_column(Enum(TodoStatus), default=TodoStatus.todo, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=33, nullable=False)
    urgency: Mapped[int] = mapped_column(Integer, default=33, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recurrence_type: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    recurrence_interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_per_interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    interval_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="todos")
    todo_tags: Mapped[list["TodoTag"]] = relationship(secondary="todo_tag_relations", back_populates="todos")

    @property
    def tags(self) -> list[str] | None:
        """返回待办的标签名列表。"""
        if not self.todo_tags:
            return None
        return [tag.name for tag in self.todo_tags]


class TodoTag(Base):
    """待办标签模型。"""

    __tablename__ = "todo_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_todo_tags_user_id_name"),
        Index("ix_todo_tags_user_id_name", "user_id", "name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    todos: Mapped[list["Todo"]] = relationship(secondary="todo_tag_relations", back_populates="todo_tags")


class TodoTagRelation(Base):
    """待办和标签的关联表。"""

    __tablename__ = "todo_tag_relations"

    todo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class TodoCompletionEvent(Base):
    """待办完成历史事件。"""

    __tablename__ = "todo_completion_events"
    __table_args__ = (
        CheckConstraint("delta <> 0", name="ck_todo_completion_events_delta_nonzero"),
        CheckConstraint("target_count_snapshot >= 1", name="ck_todo_completion_events_target_count_snapshot_min"),
        Index("ix_todo_completion_events_user_id_occurred_on", "user_id", "occurred_on"),
        Index("ix_todo_completion_events_todo_id_occurred_on", "todo_id", "occurred_on"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    todo_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    todo_title_snapshot: Mapped[str] = mapped_column(String(300), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    target_count_snapshot: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
