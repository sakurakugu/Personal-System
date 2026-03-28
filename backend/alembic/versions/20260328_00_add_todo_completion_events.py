"""新增待办完成历史事件表。

Revision ID: 20260328_00
Revises: 20260326_00
Create Date: 2026-03-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260328_00"
down_revision = "20260326_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "todo_completion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("todo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("todo_title_snapshot", sa.String(length=300), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("delta <> 0", name="ck_todo_completion_events_delta_nonzero"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_todo_completion_events_user_id_occurred_on",
        "todo_completion_events",
        ["user_id", "occurred_on"],
        unique=False,
    )
    op.create_index(
        "ix_todo_completion_events_todo_id_occurred_on",
        "todo_completion_events",
        ["todo_id", "occurred_on"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_todo_completion_events_todo_id_occurred_on", table_name="todo_completion_events")
    op.drop_index("ix_todo_completion_events_user_id_occurred_on", table_name="todo_completion_events")
    op.drop_table("todo_completion_events")
