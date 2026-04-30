"""为友链表添加分类字段。

Revision ID: 20260415_00
Revises: 20260414_02
Create Date: 2026-04-15 20:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260415_00"
down_revision = "20260414_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "friend_links",
        sa.Column("category", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_friend_links_category", "friend_links", ["category"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_friend_links_category", table_name="friend_links")
    op.drop_column("friend_links", "category")
