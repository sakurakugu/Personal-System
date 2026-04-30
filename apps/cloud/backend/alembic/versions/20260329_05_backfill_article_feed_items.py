"""回填文章 Feed 条目。

Revision ID: 20260329_05
Revises: 20260329_04
Create Date: 2026-03-29 22:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.utils.uuid import generate_uuid7

# revision identifiers, used by Alembic.
revision = "20260329_05"
down_revision = "20260329_04"
branch_labels = None
depends_on = None


FEED_ITEM_TYPE_ENUM = postgresql.ENUM("article", "moment", name="feeditemtype", create_type=False)


def upgrade() -> None:
    """升级迁移。"""
    bind = op.get_bind()
    feed_items_table = sa.table(
        "feed_items",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("type", FEED_ITEM_TYPE_ENUM),
        sa.column("source_id", postgresql.UUID(as_uuid=True)),
        sa.column("author_id", postgresql.UUID(as_uuid=True)),
        sa.column("is_visible", sa.Boolean()),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    article_rows = bind.execute(
        sa.text(
            """
            SELECT a.id, a.author_id, a.published_at
            FROM articles a
            WHERE a.status IN ('public', 'login_required')
              AND a.published_at IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM feed_items f
                  WHERE f.type = 'article'
                    AND f.source_id = a.id
              )
            """
        )
    ).mappings().all()

    backfill_rows = [
        {
            "id": generate_uuid7(),
            "type": "article",
            "source_id": row["id"],
            "author_id": row["author_id"],
            "is_visible": True,
            "published_at": row["published_at"],
            "created_at": row["published_at"],
            "updated_at": row["published_at"],
        }
        for row in article_rows
    ]

    if backfill_rows:
        op.bulk_insert(feed_items_table, backfill_rows)


def downgrade() -> None:
    """回滚迁移。"""
    op.execute(
        sa.text(
            """
            DELETE FROM feed_items
            WHERE type = 'article'
              AND source_id IN (
                  SELECT a.id
                  FROM articles a
                  WHERE a.status = 'login_required'
                    AND a.published_at IS NOT NULL
              )
            """
        )
    )
