"""为文章和动态新增软删除字段。

Revision ID: 20260504_01
Revises: 20260504_00
Create Date: 2026-05-04 14:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260504_01"
down_revision = "20260504_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "articles",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "articles",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("articles", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_articles_deleted_state",
        "articles",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.create_index(
        "ix_articles_author_id_is_deleted_created_at",
        "articles",
        ["author_id", "is_deleted", "created_at"],
        unique=False,
    )

    op.add_column(
        "moments",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "moments",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("moments", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_moments_deleted_state",
        "moments",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.create_index(
        "ix_moments_user_id_is_deleted_created_at",
        "moments",
        ["user_id", "is_deleted", "created_at"],
        unique=False,
    )
    op.drop_index("ux_moments_single_draft_per_user", table_name="moments")
    op.create_index(
        "ux_moments_single_draft_per_user",
        "moments",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_published = FALSE AND is_deleted = FALSE"),
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ux_moments_single_draft_per_user", table_name="moments")
    op.create_index(
        "ux_moments_single_draft_per_user",
        "moments",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_published = FALSE"),
    )
    op.drop_index("ix_moments_user_id_is_deleted_created_at", table_name="moments")
    op.drop_constraint("ck_moments_deleted_state", "moments", type_="check")
    op.drop_column("moments", "deleted_at")
    op.drop_column("moments", "is_deleted")

    op.drop_index("ix_articles_author_id_is_deleted_created_at", table_name="articles")
    op.drop_constraint("ck_articles_deleted_state", "articles", type_="check")
    op.drop_column("articles", "deleted_at")
    op.drop_column("articles", "is_deleted")
