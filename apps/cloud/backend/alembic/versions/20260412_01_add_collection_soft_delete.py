"""为收藏模块新增软删除字段。

Revision ID: 20260412_01
Revises: 20260412_00
Create Date: 2026-04-12 13:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260412_01"
down_revision = "20260412_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "collections",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "collections",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("collections", "is_deleted", server_default=None)

    op.drop_index("ix_collections_user_id_status_created_at", table_name="collections")
    op.drop_index("ix_collections_user_id_type_created_at", table_name="collections")
    op.create_check_constraint(
        "ck_collections_deleted_state",
        "collections",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.create_index(
        "ix_collections_user_id_is_deleted_status_created_at",
        "collections",
        ["user_id", "is_deleted", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_collections_user_id_is_deleted_type_created_at",
        "collections",
        ["user_id", "is_deleted", "type", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_collections_user_id_is_deleted_type_created_at", table_name="collections")
    op.drop_index("ix_collections_user_id_is_deleted_status_created_at", table_name="collections")
    op.drop_constraint("ck_collections_deleted_state", "collections", type_="check")
    op.create_index(
        "ix_collections_user_id_type_created_at",
        "collections",
        ["user_id", "type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_collections_user_id_status_created_at",
        "collections",
        ["user_id", "status", "created_at"],
        unique=False,
    )
    op.drop_column("collections", "deleted_at")
    op.drop_column("collections", "is_deleted")
