"""为分类表新增文章数量字段。

Revision ID: 20260414_00
Revises: 20260412_01
Create Date: 2026-04-14 19:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260414_00"
down_revision = "20260412_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "categories",
        sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        sa.text(
            """
            UPDATE categories
            SET article_count = (
                SELECT COUNT(*) FROM articles WHERE articles.category_id = categories.id
            )
            """
        )
    )
    op.alter_column("categories", "article_count", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("categories", "article_count")
