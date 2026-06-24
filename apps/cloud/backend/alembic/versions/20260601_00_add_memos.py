"""新增备忘录表。"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260601_00"
down_revision = "20260529_01"
branch_labels = None
depends_on = None


memo_status = postgresql.ENUM("inbox", "processed", "archived", "dropped", name="memostatus", create_type=False)
memo_source = postgresql.ENUM("manual", "wechat", "web", "share", "unknown", name="memosource", create_type=False)


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()
    memo_status.create(bind, checkfirst=True)
    memo_source.create(bind, checkfirst=True)

    op.create_table(
        "memos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", memo_status, nullable=False),
        sa.Column("source", memo_source, nullable=False),
        sa.Column("converted_to_type", sa.String(length=50), nullable=True),
        sa.Column("converted_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR (status <> 'archived' AND archived_at IS NULL)",
            name="ck_memos_archived_state",
        ),
        sa.CheckConstraint(
            "(deleted_at IS NULL AND status <> 'dropped') OR deleted_at IS NOT NULL",
            name="ck_memos_deleted_state",
        ),
        sa.CheckConstraint(
            "(converted_to_type IS NULL AND converted_to_id IS NULL) OR "
            "(converted_to_type IS NOT NULL AND converted_to_id IS NOT NULL)",
            name="ck_memos_converted_target",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memos_user_id_deleted_at_status_updated_at",
        "memos",
        ["user_id", "deleted_at", "status", "updated_at"],
    )
    op.create_index("ix_memos_user_id_converted_to_type", "memos", ["user_id", "converted_to_type"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_memos_user_id_converted_to_type", table_name="memos")
    op.drop_index("ix_memos_user_id_deleted_at_status_updated_at", table_name="memos")
    op.drop_table("memos")
    bind = op.get_bind()
    memo_source.drop(bind, checkfirst=True)
    memo_status.drop(bind, checkfirst=True)
