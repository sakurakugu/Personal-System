"""为文件增加用途字段并区分文章图片。

Revision ID: 20260407_00
Revises: 20260406_01
Create Date: 2026-04-07 20:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260407_00"
down_revision = "20260406_01"
branch_labels = None
depends_on = None

FILE_PURPOSE_ENUM = postgresql.ENUM("file", "article_image", name="filepurpose")


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()

    FILE_PURPOSE_ENUM.create(bind, checkfirst=False)
    op.add_column(
        "files",
        sa.Column("purpose", FILE_PURPOSE_ENUM, nullable=False, server_default="file"),
    )

    op.execute(
        sa.text(
            """
            UPDATE files
            SET purpose = 'article_image'
            WHERE EXISTS (
                SELECT 1
                FROM articles
                WHERE articles.content LIKE '%' || '/files/' || files.storage_key || '%'
                   OR COALESCE(articles.cover_url, '') LIKE '%' || '/files/' || files.storage_key || '%'
            )
            """
        )
    )

    op.alter_column("files", "purpose", server_default=None)
    op.drop_index("ix_files_user_id_created_at", table_name="files")
    op.create_index(
        "ix_files_user_id_purpose_created_at",
        "files",
        ["user_id", "purpose", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    bind = op.get_bind()

    op.drop_index("ix_files_user_id_purpose_created_at", table_name="files")
    op.create_index("ix_files_user_id_created_at", "files", ["user_id", "created_at"], unique=False)
    op.drop_column("files", "purpose")
    FILE_PURPOSE_ENUM.drop(bind, checkfirst=False)
