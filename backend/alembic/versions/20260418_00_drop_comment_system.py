"""删除旧评论系统表和遗留设置。

Revision ID: 20260418_00
Revises: 20260415_00
Create Date: 2026-04-18 19:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260418_00"
down_revision = "20260415_00"
branch_labels = None
depends_on = None

COMMENT_STATUS_ENUM = postgresql.ENUM("pending", "approved", "rejected", name="commentstatus", create_type=False)


def upgrade() -> None:
    """升级数据库结构。"""
    op.execute(
        sa.text(
            "DELETE FROM system_settings WHERE key IN ('comments_enabled', 'comments_stealth', 'comments_min_role')"
        )
    )
    op.drop_table("comment_likes")
    op.drop_index("ix_comments_user_id_created_at", table_name="comments")
    op.drop_index("ix_comments_parent_id_created_at", table_name="comments")
    op.drop_index("ix_comments_status_created_at", table_name="comments")
    op.drop_index("ix_comments_article_id_status_created_at", table_name="comments")
    op.drop_table("comments")
    COMMENT_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """回滚数据库结构。"""
    COMMENT_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("guest_name", sa.String(length=100), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", COMMENT_STATUS_ENUM, nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND guest_name IS NULL) OR (user_id IS NULL AND guest_name IS NOT NULL)",
            name="ck_comments_author_identity",
        ),
    )
    op.create_index("ix_comments_article_id_status_created_at", "comments", ["article_id", "status", "created_at"], unique=False)
    op.create_index("ix_comments_status_created_at", "comments", ["status", "created_at"], unique=False)
    op.create_index("ix_comments_parent_id_created_at", "comments", ["parent_id", "created_at"], unique=False)
    op.create_index("ix_comments_user_id_created_at", "comments", ["user_id", "created_at"], unique=False)
    op.create_table(
        "comment_likes",
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id", "user_id"),
    )
