"""为文章和动态补充点赞与动态浏览统计字段。

Revision ID: 20260419_00
Revises: 20260418_02
Create Date: 2026-04-19 10:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260419_00"
down_revision = "20260418_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "articles",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "moments",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "moments",
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.alter_column("articles", "like_count", server_default=None)
    op.alter_column("moments", "view_count", server_default=None)
    op.alter_column("moments", "like_count", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("moments", "like_count")
    op.drop_column("moments", "view_count")
    op.drop_column("articles", "like_count")
