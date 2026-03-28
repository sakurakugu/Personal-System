"""新增首页 Feed 条目表。

Revision ID: 20260329_00
Revises: 20260328_00
Create Date: 2026-03-29 00:00:00
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260329_00"
down_revision = "20260328_00"
branch_labels = None
depends_on = None


FEED_ITEM_TYPE_ENUM = postgresql.ENUM("article", "moment", name="feeditemtype", create_type=False)


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()
    FEED_ITEM_TYPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "feed_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", FEED_ITEM_TYPE_ENUM, nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feed_items_is_visible_published_at",
        "feed_items",
        ["is_visible", "published_at"],
        unique=False,
    )
    op.create_index(
        "ix_feed_items_author_id_published_at",
        "feed_items",
        ["author_id", "published_at"],
        unique=False,
    )
    op.create_index(
        "uq_feed_items_type_source_id",
        "feed_items",
        ["type", "source_id"],
        unique=True,
    )

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
            SELECT id, author_id, published_at
            FROM articles
            WHERE status = 'published' AND published_at IS NOT NULL
            """
        )
    ).mappings().all()
    moment_rows = bind.execute(
        sa.text(
            """
            SELECT id, user_id AS author_id, published_at
            FROM moments
            WHERE is_published = TRUE AND published_at IS NOT NULL
            """
        )
    ).mappings().all()

    backfill_rows = [
        {
            "id": uuid4(),
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
    backfill_rows.extend(
        {
            "id": uuid4(),
            "type": "moment",
            "source_id": row["id"],
            "author_id": row["author_id"],
            "is_visible": True,
            "published_at": row["published_at"],
            "created_at": row["published_at"],
            "updated_at": row["published_at"],
        }
        for row in moment_rows
    )

    if backfill_rows:
        op.bulk_insert(feed_items_table, backfill_rows)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("uq_feed_items_type_source_id", table_name="feed_items")
    op.drop_index("ix_feed_items_author_id_published_at", table_name="feed_items")
    op.drop_index("ix_feed_items_is_visible_published_at", table_name="feed_items")
    op.drop_table("feed_items")

    bind = op.get_bind()
    FEED_ITEM_TYPE_ENUM.drop(bind, checkfirst=True)
