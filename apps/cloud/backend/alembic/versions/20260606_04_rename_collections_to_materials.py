"""将收藏模块改名为资料库并收敛状态。

Revision ID: 20260606_04
Revises: 20260606_03
Create Date: 2026-06-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260606_04"
down_revision = "20260606_03"
branch_labels = None
depends_on = None


OLD_STATUS_ENUM = postgresql.ENUM(
    "inbox",
    "processing",
    "ready",
    "archived",
    "dropped",
    name="collectionstatus",
)
NEW_STATUS_ENUM = postgresql.ENUM("active", "archived", name="materialstatus")
OLD_TYPE_ENUM = postgresql.ENUM("link", "text", "image", "file", name="collectiontype")
NEW_TYPE_ENUM = postgresql.ENUM("link", "text", "image", "file", name="materialtype")


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()

    NEW_STATUS_ENUM.create(bind, checkfirst=True)
    NEW_TYPE_ENUM.create(bind, checkfirst=True)

    op.execute("DELETE FROM collection_assets WHERE collection_id IN (SELECT id FROM collections WHERE status = 'dropped')")
    op.execute(
        "DELETE FROM collection_tag_relations WHERE collection_id IN (SELECT id FROM collections WHERE status = 'dropped')"
    )
    op.execute("DELETE FROM collections WHERE status = 'dropped'")

    op.drop_index("ix_collection_assets_collection_id_sort_order", table_name="collection_assets")
    op.drop_index("ix_collection_tags_user_id_name", table_name="collection_tags")
    op.drop_index("ix_collections_user_id_is_deleted_status_created_at", table_name="collections")
    op.drop_index("ix_collections_user_id_is_deleted_type_created_at", table_name="collections")
    op.drop_constraint("ck_collections_deleted_state", "collections", type_="check")
    op.drop_constraint("uq_collection_tags_user_id_name", "collection_tags", type_="unique")

    op.alter_column(
        "collections",
        "status",
        existing_type=OLD_STATUS_ENUM,
        type_=NEW_STATUS_ENUM,
        existing_nullable=False,
        postgresql_using=(
            "CASE WHEN status::text IN ('inbox', 'processing', 'ready') "
            "THEN 'active' ELSE status::text END::materialstatus"
        ),
    )
    op.alter_column(
        "collections",
        "type",
        existing_type=OLD_TYPE_ENUM,
        type_=NEW_TYPE_ENUM,
        existing_nullable=False,
        postgresql_using="type::text::materialtype",
    )

    op.rename_table("collection_tag_relations", "material_tag_relations")
    op.rename_table("collection_tags", "material_tags")
    op.rename_table("collection_assets", "material_assets")
    op.rename_table("collections", "materials")
    op.alter_column("material_assets", "collection_id", new_column_name="material_id")
    op.alter_column("material_tag_relations", "collection_id", new_column_name="material_id")

    op.create_check_constraint(
        "ck_materials_deleted_state",
        "materials",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.create_index(
        "ix_materials_user_id_is_deleted_status_created_at",
        "materials",
        ["user_id", "is_deleted", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_materials_user_id_is_deleted_type_created_at",
        "materials",
        ["user_id", "is_deleted", "type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_material_assets_material_id_sort_order",
        "material_assets",
        ["material_id", "sort_order"],
        unique=False,
    )
    op.create_unique_constraint("uq_material_tags_user_id_name", "material_tags", ["user_id", "name"])
    op.create_index("ix_material_tags_user_id_name", "material_tags", ["user_id", "name"], unique=False)

    OLD_STATUS_ENUM.drop(bind, checkfirst=True)
    OLD_TYPE_ENUM.drop(bind, checkfirst=True)


def downgrade() -> None:
    """回滚数据库结构。"""
    bind = op.get_bind()

    OLD_STATUS_ENUM.create(bind, checkfirst=True)
    OLD_TYPE_ENUM.create(bind, checkfirst=True)

    op.drop_index("ix_material_tags_user_id_name", table_name="material_tags")
    op.drop_constraint("uq_material_tags_user_id_name", "material_tags", type_="unique")
    op.drop_index("ix_material_assets_material_id_sort_order", table_name="material_assets")
    op.drop_index("ix_materials_user_id_is_deleted_type_created_at", table_name="materials")
    op.drop_index("ix_materials_user_id_is_deleted_status_created_at", table_name="materials")
    op.drop_constraint("ck_materials_deleted_state", "materials", type_="check")

    op.alter_column("material_tag_relations", "material_id", new_column_name="collection_id")
    op.alter_column("material_assets", "material_id", new_column_name="collection_id")
    op.rename_table("materials", "collections")
    op.rename_table("material_assets", "collection_assets")
    op.rename_table("material_tags", "collection_tags")
    op.rename_table("material_tag_relations", "collection_tag_relations")

    op.alter_column(
        "collections",
        "type",
        existing_type=NEW_TYPE_ENUM,
        type_=OLD_TYPE_ENUM,
        existing_nullable=False,
        postgresql_using="type::text::collectiontype",
    )
    op.alter_column(
        "collections",
        "status",
        existing_type=NEW_STATUS_ENUM,
        type_=OLD_STATUS_ENUM,
        existing_nullable=False,
        postgresql_using="CASE WHEN status::text = 'active' THEN 'ready' ELSE status::text END::collectionstatus",
    )

    op.create_unique_constraint("uq_collection_tags_user_id_name", "collection_tags", ["user_id", "name"])
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
    op.create_index(
        "ix_collection_assets_collection_id_sort_order",
        "collection_assets",
        ["collection_id", "sort_order"],
        unique=False,
    )
    op.create_index("ix_collection_tags_user_id_name", "collection_tags", ["user_id", "name"], unique=False)

    NEW_STATUS_ENUM.drop(bind, checkfirst=True)
    NEW_TYPE_ENUM.drop(bind, checkfirst=True)
