"""新增动态图片表。

Revision ID: 20260504_00
Revises: 20260503_00
Create Date: 2026-05-04 11:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260504_00"
down_revision = "20260503_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "moment_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("moment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["moment_id"], ["moments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_moment_images_moment_id_sort_order_created_at",
        "moment_images",
        ["moment_id", "sort_order", "created_at"],
        unique=False,
    )
    op.create_index("ix_moment_images_storage_key", "moment_images", ["storage_key"], unique=False)
    op.alter_column("moment_images", "sort_order", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_moment_images_storage_key", table_name="moment_images")
    op.drop_index("ix_moment_images_moment_id_sort_order_created_at", table_name="moment_images")
    op.drop_table("moment_images")
