"""新增文章图片表并迁移历史文章图片。

Revision ID: 20260407_01
Revises: 20260407_00
Create Date: 2026-04-07 22:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260407_01"
down_revision = "20260407_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "article_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_article_images_article_id_created_at",
        "article_images",
        ["article_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_article_images_storage_key", "article_images", ["storage_key"], unique=False)

    op.execute(
        sa.text(
            """
            WITH matched_article_images AS (
                SELECT DISTINCT ON (files.id)
                    files.id AS file_id,
                    articles.id AS article_id
                FROM files
                JOIN articles
                  ON files.purpose = 'article_image'
                 AND (
                    articles.content LIKE '%' || '/files/' || files.storage_key || '%'
                    OR COALESCE(articles.cover_url, '') LIKE '%' || '/files/' || files.storage_key || '%'
                 )
                ORDER BY files.id, articles.created_at ASC
            )
            INSERT INTO article_images (
                id,
                article_id,
                original_name,
                storage_key,
                size,
                mime_type,
                created_at
            )
            SELECT
                files.id,
                matched_article_images.article_id,
                files.original_name,
                files.storage_key,
                files.size,
                files.mime_type,
                files.created_at
            FROM files
            JOIN matched_article_images
              ON matched_article_images.file_id = files.id
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM files
            WHERE id IN (
                SELECT article_images.id
                FROM article_images
            )
            """
        )
    )
    op.execute(sa.text("UPDATE files SET purpose = 'file' WHERE purpose = 'article_image'"))


def downgrade() -> None:
    """回滚数据库结构。"""
    op.execute(
        sa.text(
            """
            INSERT INTO files (
                id,
                user_id,
                purpose,
                original_name,
                storage_key,
                url,
                size,
                mime_type,
                created_at
            )
            SELECT
                article_images.id,
                articles.author_id,
                'article_image',
                article_images.original_name,
                article_images.storage_key,
                '/files/' || article_images.storage_key,
                article_images.size,
                article_images.mime_type,
                article_images.created_at
            FROM article_images
            JOIN articles
              ON articles.id = article_images.article_id
            """
        )
    )

    op.drop_index("ix_article_images_storage_key", table_name="article_images")
    op.drop_index("ix_article_images_article_id_created_at", table_name="article_images")
    op.drop_table("article_images")
