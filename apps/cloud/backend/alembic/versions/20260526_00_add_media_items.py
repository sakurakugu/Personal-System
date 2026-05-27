"""新增作品推荐表。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260526_00"
down_revision = "20260505_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "media_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("original_title", sa.String(length=300), nullable=True),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("creator", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("genres", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("cover_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 10)", name="ck_media_items_rating_range"),
        sa.CheckConstraint(
            "media_type IN ('game', 'novel', 'book', 'anime', 'comic', 'movie', 'tv', 'music', 'other')",
            name="ck_media_items_media_type",
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'doing', 'done', 'paused', 'dropped')",
            name="ck_media_items_status",
        ),
        sa.ForeignKeyConstraint(["cover_file_id"], ["files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_media_items_user_id_media_type_status_created_at",
        "media_items",
        ["user_id", "media_type", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_media_items_user_id_status_created_at",
        "media_items",
        ["user_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_media_items_user_id_rating_created_at",
        "media_items",
        ["user_id", "rating", "created_at"],
        unique=False,
    )
    op.alter_column("media_items", "genres", server_default=None)
    op.alter_column("media_items", "tags", server_default=None)
    op.alter_column("media_items", "is_visible", server_default=None)
    op.alter_column("media_items", "created_at", server_default=None)
    op.alter_column("media_items", "updated_at", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_media_items_user_id_rating_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_status_created_at", table_name="media_items")
    op.drop_index("ix_media_items_user_id_media_type_status_created_at", table_name="media_items")
    op.drop_table("media_items")
