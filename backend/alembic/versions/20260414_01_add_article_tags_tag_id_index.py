"""为文章标签关联表新增 tag_id 索引。

Revision ID: 20260414_01
Revises: 20260414_00
Create Date: 2026-04-14 19:40:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260414_01"
down_revision = "20260414_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_index("ix_article_tags_tag_id", "article_tags", ["tag_id"])


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_article_tags_tag_id", table_name="article_tags")
