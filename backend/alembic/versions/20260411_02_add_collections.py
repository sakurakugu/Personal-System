"""新增收藏模块相关表。

Revision ID: 20260411_02
Revises: 20260411_01
Create Date: 2026-04-11 23:59:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260411_02"
down_revision = "20260411_01"
branch_labels = None
depends_on = None


COLLECTION_TYPE_ENUM = postgresql.ENUM("link", "text", "image", "file", name="collectiontype", create_type=False)
COLLECTION_SOURCE_TYPE_ENUM = postgresql.ENUM(
    "web",
    "wechat",
    "manual",
    "screenshot",
    name="collectionsourcetype",
    create_type=False,
)
COLLECTION_STATUS_ENUM = postgresql.ENUM(
    "inbox",
    "processing",
    "ready",
    "archived",
    "dropped",
    name="collectionstatus",
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
    bind = op.get_bind()
    COLLECTION_TYPE_ENUM.create(bind, checkfirst=True)
    COLLECTION_SOURCE_TYPE_ENUM.create(bind, checkfirst=True)
    COLLECTION_STATUS_ENUM.create(bind, checkfirst=True)
    COLLECTION_AI_STATUS_ENUM.create(bind, checkfirst=True)
    COLLECTION_ASSET_ROLE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", COLLECTION_TYPE_ENUM, nullable=False),
        sa.Column("source_type", COLLECTION_SOURCE_TYPE_ENUM, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("site_name", sa.String(length=120), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", COLLECTION_STATUS_ENUM, nullable=False),
        sa.Column("ai_status", COLLECTION_AI_STATUS_ENUM, nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collections_user_id_status_created_at",
        "collections",
        ["user_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_collections_user_id_source_type_created_at",
        "collections",
        ["user_id", "source_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_collections_user_id_type_created_at",
        "collections",
        ["user_id", "type", "created_at"],
        unique=False,
    )

    op.create_table(
        "collection_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_collection_tags_user_id_name"),
    )
    op.create_index("ix_collection_tags_user_id_name", "collection_tags", ["user_id", "name"], unique=False)

    op.create_table(
        "collection_tag_relations",
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["collection_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("collection_id", "tag_id"),
    )

    op.create_table(
        "collection_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_role", COLLECTION_ASSET_ROLE_ENUM, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_assets_collection_id_sort_order",
        "collection_assets",
        ["collection_id", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_collection_assets_collection_id_sort_order", table_name="collection_assets")
    op.drop_table("collection_assets")
    op.drop_table("collection_tag_relations")
    op.drop_index("ix_collection_tags_user_id_name", table_name="collection_tags")
    op.drop_table("collection_tags")
    op.drop_index("ix_collections_user_id_type_created_at", table_name="collections")
    op.drop_index("ix_collections_user_id_source_type_created_at", table_name="collections")
    op.drop_index("ix_collections_user_id_status_created_at", table_name="collections")
    op.drop_table("collections")

    bind = op.get_bind()
    COLLECTION_ASSET_ROLE_ENUM.drop(bind, checkfirst=True)
    COLLECTION_AI_STATUS_ENUM.drop(bind, checkfirst=True)
    COLLECTION_STATUS_ENUM.drop(bind, checkfirst=True)
    COLLECTION_SOURCE_TYPE_ENUM.drop(bind, checkfirst=True)
    COLLECTION_TYPE_ENUM.drop(bind, checkfirst=True)
