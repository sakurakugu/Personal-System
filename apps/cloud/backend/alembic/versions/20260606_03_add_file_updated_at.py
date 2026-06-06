"""为普通文件新增更新时间字段。

Revision ID: 20260606_03
Revises: 20260606_02
Create Date: 2026-06-06 03:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260606_03"
down_revision = "20260606_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "files",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.alter_column("files", "updated_at", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("files", "updated_at")
