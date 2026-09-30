"""为文章添加整理状态和派生内容关联。"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261001_02"
down_revision = "20261001_01"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """建立整理状态并恢复原备忘录整理信息。"""
    op.add_column("articles", sa.Column("organization_state", sa.String(20), nullable=False, server_default="organized"))
    op.add_column("articles", sa.Column("archived_at", sa.DateTime(timezone=True)))
    op.create_check_constraint("ck_articles_organization_state", "articles", "organization_state IN ('inbox', 'organized', 'archived')")
    op.create_index("ix_articles_author_organization", "articles", ["author_id", "organization_state", "last_edited_at"])
    op.execute(sa.text("""
        UPDATE articles SET
            organization_state = CASE import_metadata->>'status'
                WHEN 'inbox' THEN 'inbox'
                WHEN 'archived' THEN 'archived'
                ELSE 'organized'
            END,
            archived_at = CASE WHEN import_metadata->>'status' = 'archived'
                THEN (import_metadata->>'archived_at')::timestamptz ELSE NULL END
        WHERE import_metadata->>'kind' = 'memo'
    """))
    op.create_table(
        "article_conversions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_type IN ('todo', 'material')", name="ck_article_conversions_target_type"),
    )
    op.create_index("ix_article_conversions_article_id", "article_conversions", ["article_id"])
    op.create_index("ix_article_conversions_target", "article_conversions", ["target_type", "target_id"])
    op.execute(sa.text("""
        INSERT INTO article_conversions (id, article_id, target_type, target_id, created_at)
        SELECT gen_random_uuid(), id,
               CASE import_metadata->>'converted_to_type'
                   WHEN 'collection' THEN 'material'
                   ELSE import_metadata->>'converted_to_type' END,
               (import_metadata->>'converted_to_id')::uuid, created_at
        FROM articles
        WHERE import_metadata->>'kind' = 'memo'
          AND import_metadata->>'converted_to_type' IN ('todo', 'material', 'collection')
          AND import_metadata->>'converted_to_id' IS NOT NULL
    """))
    logger.info("文章整理状态与转换关联迁移完成")


def downgrade() -> None:
    """移除整理状态和派生关联。"""
    op.drop_index("ix_article_conversions_target", table_name="article_conversions")
    op.drop_index("ix_article_conversions_article_id", table_name="article_conversions")
    op.drop_table("article_conversions")
    op.drop_index("ix_articles_author_organization", table_name="articles")
    op.drop_constraint("ck_articles_organization_state", "articles", type_="check")
    op.drop_column("articles", "archived_at")
    op.drop_column("articles", "organization_state")
