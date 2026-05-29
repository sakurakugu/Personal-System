"""为文娱、公告和友链新增软删除字段。"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260529_01"
down_revision = "20260529_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "media_items",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("media_items", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("media_items", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_media_items_deleted_state",
        "media_items",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.drop_index("ix_media_items_user_id_media_type_status_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_status_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_rating_created_at", table_name="media_items")
    op.create_index(
        "ix_media_items_user_id_is_deleted_media_type_status_created_at",
        "media_items",
        ["user_id", "is_deleted", "media_type", "status", "created_at"],
    )
    op.create_index(
        "ix_media_items_user_id_is_deleted_status_created_at",
        "media_items",
        ["user_id", "is_deleted", "status", "created_at"],
    )
    op.create_index(
        "ix_media_items_user_id_is_deleted_rating_created_at",
        "media_items",
        ["user_id", "is_deleted", "rating", "created_at"],
    )

    op.add_column(
        "announcements",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("announcements", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("announcements", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_announcements_deleted_state",
        "announcements",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.drop_index("ix_announcements_is_active_created_at", table_name="announcements")
    op.drop_index("ix_announcements_created_by_created_at", table_name="announcements")
    op.create_index(
        "ix_announcements_is_deleted_is_active_created_at",
        "announcements",
        ["is_deleted", "is_active", "created_at"],
    )
    op.create_index(
        "ix_announcements_created_by_is_deleted_created_at",
        "announcements",
        ["created_by", "is_deleted", "created_at"],
    )

    op.add_column(
        "friend_links",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("friend_links", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("friend_links", "is_deleted", server_default=None)
    op.create_check_constraint(
        "ck_friend_links_deleted_state",
        "friend_links",
        "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
    )
    op.drop_constraint("friend_links_url_key", "friend_links", type_="unique")
    op.drop_index("ix_friend_links_status_created_at", table_name="friend_links")
    op.create_index(
        "ix_friend_links_is_deleted_status_created_at",
        "friend_links",
        ["is_deleted", "status", "created_at"],
    )
    op.create_index(
        "ux_friend_links_url_active",
        "friend_links",
        ["url"],
        unique=True,
        postgresql_where=sa.text("is_deleted = FALSE"),
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ux_friend_links_url_active", table_name="friend_links")
    op.drop_index("ix_friend_links_is_deleted_status_created_at", table_name="friend_links")
    op.create_index("ix_friend_links_status_created_at", "friend_links", ["status", "created_at"])
    op.create_unique_constraint("friend_links_url_key", "friend_links", ["url"])
    op.drop_constraint("ck_friend_links_deleted_state", "friend_links", type_="check")
    op.drop_column("friend_links", "deleted_at")
    op.drop_column("friend_links", "is_deleted")

    op.drop_index("ix_announcements_created_by_is_deleted_created_at", table_name="announcements")
    op.drop_index("ix_announcements_is_deleted_is_active_created_at", table_name="announcements")
    op.create_index("ix_announcements_created_by_created_at", "announcements", ["created_by", "created_at"])
    op.create_index("ix_announcements_is_active_created_at", "announcements", ["is_active", "created_at"])
    op.drop_constraint("ck_announcements_deleted_state", "announcements", type_="check")
    op.drop_column("announcements", "deleted_at")
    op.drop_column("announcements", "is_deleted")

    op.drop_index("ix_media_items_user_id_is_deleted_rating_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_is_deleted_status_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_is_deleted_media_type_status_created_at", table_name="media_items")
    op.create_index(
        "ix_media_items_user_id_rating_created_at",
        "media_items",
        ["user_id", "rating", "created_at"],
    )
    op.create_index(
        "ix_media_items_user_id_status_created_at",
        "media_items",
        ["user_id", "status", "created_at"],
    )
    op.create_index(
        "ix_media_items_user_id_media_type_status_created_at",
        "media_items",
        ["user_id", "media_type", "status", "created_at"],
    )
    op.drop_constraint("ck_media_items_deleted_state", "media_items", type_="check")
    op.drop_column("media_items", "deleted_at")
    op.drop_column("media_items", "is_deleted")
