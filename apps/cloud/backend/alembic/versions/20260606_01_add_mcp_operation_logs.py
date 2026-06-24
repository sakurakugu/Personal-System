"""新增 MCP 操作日志表。

Revision ID: 20260606_01
Revises: 20260606_00
Create Date: 2026-06-06 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260606_01"
down_revision = "20260606_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    status_enum = postgresql.ENUM("success", "failed", "undone", name="mcpoperationstatus", create_type=False)
    status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "mcp_operation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("args_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("is_undoable", sa.Boolean(), nullable=False),
        sa.Column("undo_tool_name", sa.String(length=120), nullable=True),
        sa.Column("undoable_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("undone_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("undone_by_operation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["device_session_id"], ["user_device_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["undone_by_operation_id"], ["mcp_operation_logs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_operation_logs_user_created_at", "mcp_operation_logs", ["user_id", "created_at"])
    op.create_index(
        "ix_mcp_operation_logs_session_created_at",
        "mcp_operation_logs",
        ["device_session_id", "created_at"],
    )
    op.create_index("ix_mcp_operation_logs_tool_created_at", "mcp_operation_logs", ["tool_name", "created_at"])
    op.create_index("ix_mcp_operation_logs_target", "mcp_operation_logs", ["target_type", "target_id"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_mcp_operation_logs_target", table_name="mcp_operation_logs")
    op.drop_index("ix_mcp_operation_logs_tool_created_at", table_name="mcp_operation_logs")
    op.drop_index("ix_mcp_operation_logs_session_created_at", table_name="mcp_operation_logs")
    op.drop_index("ix_mcp_operation_logs_user_created_at", table_name="mcp_operation_logs")
    op.drop_table("mcp_operation_logs")
    status_enum = postgresql.ENUM("success", "failed", "undone", name="mcpoperationstatus", create_type=False)
    status_enum.drop(op.get_bind(), checkfirst=True)
