"""移除收藏冗余字段与附件角色字段。

Revision ID: 20260412_00
Revises: 20260411_02
Create Date: 2026-04-12 11:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260412_00"
down_revision = "20260411_02"
branch_labels = None
depends_on = None


COLLECTION_SOURCE_TYPE_ENUM = postgresql.ENUM(
    "web",
    "wechat",
    "manual",
    "screenshot",
    name="collectionsourcetype",
    create_type=False,
)
COLLECTION_AI_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "running",
    "done",
    "failed",
    name="collectionaistatus",
    create_type=False,
)
COLLECTION_ASSET_ROLE_ENUM = postgresql.ENUM(
    "original",
    "cover",
    "attachment",
    "screenshot",
    name="collectionassetrole",
    create_type=False,
)


def upgrade() -> None:
    """升级数据库结构。"""
    op.drop_index("ix_collections_user_id_source_type_created_at", table_name="collections")
    op.drop_column("collections", "source_type")
    op.drop_column("collections", "ai_status")
    op.drop_column("collections", "ocr_text")
    op.drop_column("collections", "url")
    op.drop_column("collections", "site_name")
    op.drop_column("collections", "cover_url")
    op.drop_column("collections", "summary")
    op.drop_column("collection_assets", "asset_role")

    bind = op.get_bind()
    COLLECTION_SOURCE_TYPE_ENUM.drop(bind, checkfirst=True)
    COLLECTION_AI_STATUS_ENUM.drop(bind, checkfirst=True)
    COLLECTION_ASSET_ROLE_ENUM.drop(bind, checkfirst=True)


def downgrade() -> None:
    """回滚数据库结构。"""
    bind = op.get_bind()
    COLLECTION_SOURCE_TYPE_ENUM.create(bind, checkfirst=True)
    COLLECTION_AI_STATUS_ENUM.create(bind, checkfirst=True)
    COLLECTION_ASSET_ROLE_ENUM.create(bind, checkfirst=True)

    op.add_column("collections", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("collections", sa.Column("cover_url", sa.String(length=500), nullable=True))
    op.add_column("collections", sa.Column("site_name", sa.String(length=120), nullable=True))
    op.add_column("collections", sa.Column("url", sa.String(length=1000), nullable=True))
    op.add_column("collections", sa.Column("ocr_text", sa.Text(), nullable=True))
    op.add_column(
        "collections",
        sa.Column(
            "ai_status",
            COLLECTION_AI_STATUS_ENUM,
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "collections",
        sa.Column(
            "source_type",
            COLLECTION_SOURCE_TYPE_ENUM,
            nullable=False,
            server_default="manual",
        ),
    )
    op.add_column(
        "collection_assets",
        sa.Column(
            "asset_role",
            COLLECTION_ASSET_ROLE_ENUM,
            nullable=False,
            server_default="attachment",
        ),
    )
    op.create_index(
        "ix_collections_user_id_source_type_created_at",
        "collections",
        ["user_id", "source_type", "created_at"],
        unique=False,
    )
    op.alter_column("collections", "source_type", server_default=None)
    op.alter_column("collections", "ai_status", server_default=None)
    op.alter_column("collection_assets", "asset_role", server_default=None)
