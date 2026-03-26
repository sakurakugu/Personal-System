"""初始数据库结构。

Revision ID: 20260326_00
Revises:
Create Date: 2026-03-26 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260326_00"
down_revision = None
branch_labels = None
depends_on = None


USER_ROLE_ENUM = postgresql.ENUM("super_admin", "admin", "user", name="userrole", create_type=False)
ARTICLE_STATUS_ENUM = postgresql.ENUM("draft", "published", name="articlestatus", create_type=False)
COMMENT_STATUS_ENUM = postgresql.ENUM("pending", "approved", "rejected", name="commentstatus", create_type=False)
TODO_STATUS_ENUM = postgresql.ENUM("todo", "done", name="todostatus", create_type=False)
LINK_STATUS_ENUM = postgresql.ENUM("pending", "approved", "rejected", name="linkstatus", create_type=False)


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()
    USER_ROLE_ENUM.create(bind, checkfirst=True)
    ARTICLE_STATUS_ENUM.create(bind, checkfirst=True)
    COMMENT_STATUS_ENUM.create(bind, checkfirst=True)
    TODO_STATUS_ENUM.create(bind, checkfirst=True)
    LINK_STATUS_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", USER_ROLE_ENUM, nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("bool_value", sa.Boolean(), nullable=True),
        sa.Column("str_value", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("status", LINK_STATUS_ENUM, nullable=False),
        sa.Column("is_auto_exchange", sa.Boolean(), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("slug", sa.String(length=350), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.String(length=500), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("status", ARTICLE_STATUS_ENUM, nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint(
            "(status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)",
            name="ck_articles_status_published_at",
        ),
    )

    op.create_table(
        "announcements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )

    op.create_table(
        "moments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(is_published = FALSE AND published_at IS NULL) OR (is_published = TRUE AND published_at IS NOT NULL)",
            name="ck_moments_publish_state",
        ),
    )

    op.create_table(
        "todo_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_todo_tags_user_id_name"),
    )

    op.create_table(
        "todos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", TODO_STATUS_ENUM, nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("urgency", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_type", sa.String(length=20), nullable=False),
        sa.Column("recurrence_interval", sa.Integer(), nullable=False),
        sa.Column("recurrence_count", sa.Integer(), nullable=False),
        sa.Column("times_per_interval", sa.Integer(), nullable=False),
        sa.Column("interval_progress", sa.Integer(), nullable=False),
        sa.Column("progress_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "importance >= 0 AND importance <= 100",
            name="ck_todos_importance_range",
        ),
        sa.CheckConstraint(
            "urgency >= 0 AND urgency <= 100",
            name="ck_todos_urgency_range",
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date >= start_date",
            name="ck_todos_date_range",
        ),
        sa.CheckConstraint(
            "(is_deleted = FALSE AND deleted_at IS NULL) OR (is_deleted = TRUE AND deleted_at IS NOT NULL)",
            name="ck_todos_deleted_state",
        ),
        sa.CheckConstraint(
            "recurrence_type IN ('none', 'daily', 'weekly', 'monthly', 'yearly', 'workday', 'weekend', 'holiday', 'custom')",
            name="ck_todos_recurrence_type"
        ),
        sa.CheckConstraint(
            "recurrence_count >= -1",
            name="ck_todos_recurrence_count_min",
        ),
        sa.CheckConstraint(
            "times_per_interval >= 1",
            name="ck_todos_times_per_interval_min",
        ),
        sa.CheckConstraint(
            "interval_progress >= 0 AND interval_progress <= times_per_interval",
            name="ck_todos_interval_progress_range"
        ),
    )

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

    op.create_table(
        "todo_tag_relations",
        sa.Column("todo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["todo_tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["todo_id"], ["todos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("todo_id", "tag_id"),
    )

    op.create_table(
        "page_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "article_tags",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "tag_id"),
    )

    op.create_table(
        "comment_likes",
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id", "user_id"),
    )

    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=False)
    op.create_index("ix_tags_slug", "tags", ["slug"], unique=False)
    op.create_index("ix_todo_tags_user_id_name", "todo_tags", ["user_id", "name"], unique=False)
    op.create_index("ix_articles_slug", "articles", ["slug"], unique=False)
    op.create_index("ix_articles_status_published_at", "articles", ["status", "published_at"], unique=False)
    op.create_index("ix_articles_author_id_created_at", "articles", ["author_id", "created_at"], unique=False)
    op.create_index("ix_articles_category_id", "articles", ["category_id"], unique=False)
    op.create_index("ix_announcements_is_active_created_at", "announcements", ["is_active", "created_at"], unique=False)
    op.create_index("ix_announcements_created_by_created_at", "announcements", ["created_by", "created_at"], unique=False)
    op.create_index("ix_files_user_id_created_at", "files", ["user_id", "created_at"], unique=False)
    op.create_index("ix_links_status_created_at", "links", ["status", "created_at"], unique=False)
    op.create_index("ix_moments_user_id_is_published_published_at", "moments", ["user_id", "is_published", "published_at"], unique=False)
    op.create_index(
        "ux_moments_single_draft_per_user",
        "moments",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_published = FALSE"),
    )
    op.create_index("ix_todos_user_id_is_deleted_is_pinned_created_at", "todos", ["user_id", "is_deleted", "is_pinned", "created_at"], unique=False)
    op.create_index("ix_todos_user_id_status", "todos", ["user_id", "status"], unique=False)
    op.create_index("ix_todos_progress_reset_at", "todos", ["progress_reset_at"], unique=False)
    op.create_index("ix_comments_article_id_status_created_at", "comments", ["article_id", "status", "created_at"], unique=False)
    op.create_index("ix_comments_status_created_at", "comments", ["status", "created_at"], unique=False)
    op.create_index("ix_comments_parent_id_created_at", "comments", ["parent_id", "created_at"], unique=False)
    op.create_index("ix_comments_user_id_created_at", "comments", ["user_id", "created_at"], unique=False)
    op.create_index("ix_page_views_article_id_created_at", "page_views", ["article_id", "created_at"], unique=False)
    op.create_index("ix_page_views_created_at", "page_views", ["created_at"], unique=False)
    op.create_index("ix_page_views_path", "page_views", ["path"], unique=False)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_page_views_article_id_created_at", table_name="page_views")
    op.drop_index("ix_page_views_path", table_name="page_views")
    op.drop_index("ix_page_views_created_at", table_name="page_views")
    op.drop_index("ix_comments_user_id_created_at", table_name="comments")
    op.drop_index("ix_comments_parent_id_created_at", table_name="comments")
    op.drop_index("ix_comments_status_created_at", table_name="comments")
    op.drop_index("ix_comments_article_id_status_created_at", table_name="comments")
    op.drop_index("ix_todo_tags_user_id_name", table_name="todo_tags")
    op.drop_index("ix_todos_progress_reset_at", table_name="todos")
    op.drop_index("ix_todos_user_id_status", table_name="todos")
    op.drop_index("ix_todos_user_id_is_deleted_is_pinned_created_at", table_name="todos")
    op.drop_index("ux_moments_single_draft_per_user", table_name="moments")
    op.drop_index("ix_moments_user_id_is_published_published_at", table_name="moments")
    op.drop_index("ix_links_status_created_at", table_name="links")
    op.drop_index("ix_files_user_id_created_at", table_name="files")
    op.drop_index("ix_announcements_created_by_created_at", table_name="announcements")
    op.drop_index("ix_announcements_is_active_created_at", table_name="announcements")
    op.drop_index("ix_articles_category_id", table_name="articles")
    op.drop_index("ix_articles_author_id_created_at", table_name="articles")
    op.drop_index("ix_articles_status_published_at", table_name="articles")
    op.drop_index("ix_articles_slug", table_name="articles")
    op.drop_index("ix_tags_slug", table_name="tags")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")

    op.drop_table("comment_likes")
    op.drop_table("article_tags")
    op.drop_table("page_views")
    op.drop_table("comments")
    op.drop_table("todo_tag_relations")
    op.drop_table("todos")
    op.drop_table("todo_tags")
    op.drop_table("moments")
    op.drop_table("files")
    op.drop_table("announcements")
    op.drop_table("articles")
    op.drop_table("links")
    op.drop_table("system_settings")
    op.drop_table("tags")
    op.drop_table("categories")
    op.drop_table("users")

    bind = op.get_bind()
    LINK_STATUS_ENUM.drop(bind, checkfirst=True)
    TODO_STATUS_ENUM.drop(bind, checkfirst=True)
    COMMENT_STATUS_ENUM.drop(bind, checkfirst=True)
    ARTICLE_STATUS_ENUM.drop(bind, checkfirst=True)
    USER_ROLE_ENUM.drop(bind, checkfirst=True)
