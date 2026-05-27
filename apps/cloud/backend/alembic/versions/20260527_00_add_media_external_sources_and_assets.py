"""新增文娱外部来源与资源表。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260527_00"
down_revision = "20260526_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("external_url", sa.String(length=1000), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("source_provider", sa.String(length=64), nullable=True),
        sa.Column("source_asset_id", sa.String(length=200), nullable=True),
        sa.Column("original_name", sa.String(length=300), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.Column("license", sa.String(length=300), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "asset_type IN ('cover', 'backdrop', 'screenshot', 'logo', 'other')",
            name="ck_media_assets_asset_type",
        ),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(
        "ix_media_assets_media_item_id_asset_type_is_primary",
        "media_assets",
        ["media_item_id", "asset_type", "is_primary"],
    )
    op.create_index("ix_media_assets_storage_key", "media_assets", ["storage_key"])
    op.create_index("ix_media_assets_user_id_media_item_id", "media_assets", ["user_id", "media_item_id"])

    op.create_table(
        "media_external_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("external_url", sa.String(length=1000), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_item_id", "provider", "external_id", name="uq_media_external_sources_item_provider_id"),
    )
    op.create_index(
        "ix_media_external_sources_media_item_id",
        "media_external_sources",
        ["media_item_id"],
    )
    op.create_index(
        "ix_media_external_sources_provider_external_id",
        "media_external_sources",
        ["provider", "external_id"],
    )

    op.add_column("media_items", sa.Column("release_date", sa.Date(), nullable=True))
    op.add_column("media_items", sa.Column("primary_cover_asset_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_media_items_primary_cover_asset_id_media_assets",
        "media_items",
        "media_assets",
        ["primary_cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("media_items_cover_file_id_fkey", "media_items", type_="foreignkey")
    op.drop_column("media_items", "cover_file_id")

    op.alter_column("media_assets", "is_primary", server_default=None)
    op.alter_column("media_assets", "sort_order", server_default=None)
    op.alter_column("media_assets", "created_at", server_default=None)
    op.alter_column("media_assets", "updated_at", server_default=None)
    op.alter_column("media_external_sources", "fetched_at", server_default=None)
    op.alter_column("media_external_sources", "created_at", server_default=None)
    op.alter_column("media_external_sources", "updated_at", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.add_column("media_items", sa.Column("cover_file_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "media_items_cover_file_id_fkey",
        "media_items",
        "files",
        ["cover_file_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_media_items_primary_cover_asset_id_media_assets", "media_items", type_="foreignkey")
    op.drop_column("media_items", "primary_cover_asset_id")
    op.drop_column("media_items", "release_date")

    op.drop_index("ix_media_external_sources_provider_external_id", table_name="media_external_sources")
    op.drop_index("ix_media_external_sources_media_item_id", table_name="media_external_sources")
    op.drop_table("media_external_sources")

    op.drop_index("ix_media_assets_user_id_media_item_id", table_name="media_assets")
    op.drop_index("ix_media_assets_storage_key", table_name="media_assets")
    op.drop_index("ix_media_assets_media_item_id_asset_type_is_primary", table_name="media_assets")
    op.drop_table("media_assets")
