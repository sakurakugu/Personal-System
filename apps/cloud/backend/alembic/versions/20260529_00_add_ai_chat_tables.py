"""新增 AI 对话配置与调用日志。"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260529_00"
down_revision = "20260528_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("access_policy", sa.String(length=32), nullable=False, server_default="login"),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="openai_compatible"),
        sa.Column("base_url", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("timeout_seconds", sa.Float(), nullable=False, server_default="30"),
        sa.Column("system_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("allow_attachments", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_attachment_size_mb", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("daily_limit_per_user", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("secret_ciphertext", sa.Text(), nullable=True),
        sa.Column("secret_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attachment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_type", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_call_logs_user_id_created_at", "ai_call_logs", ["user_id", "created_at"])
    op.create_index("ix_ai_call_logs_status_created_at", "ai_call_logs", ["status", "created_at"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_ai_call_logs_status_created_at", table_name="ai_call_logs")
    op.drop_index("ix_ai_call_logs_user_id_created_at", table_name="ai_call_logs")
    op.drop_table("ai_call_logs")
    op.drop_table("ai_settings")
