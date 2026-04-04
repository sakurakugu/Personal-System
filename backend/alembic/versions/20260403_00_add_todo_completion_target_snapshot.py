"""为待办完成历史补充目标次数快照。

Revision ID: 20260403_00
Revises: 20260401_00
Create Date: 2026-04-03 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_00"
down_revision = "20260401_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "todo_completion_events",
        sa.Column(
            "target_count_snapshot",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.create_check_constraint(
        "ck_todo_completion_events_target_count_snapshot_min",
        "todo_completion_events",
        "target_count_snapshot >= 1",
    )
    op.alter_column("todo_completion_events", "target_count_snapshot", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_constraint(
        "ck_todo_completion_events_target_count_snapshot_min",
        "todo_completion_events",
        type_="check",
    )
    op.drop_column("todo_completion_events", "target_count_snapshot")
