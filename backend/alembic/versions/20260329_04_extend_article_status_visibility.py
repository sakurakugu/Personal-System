"""扩展文章可见性状态。

Revision ID: 20260329_04
Revises: 20260329_03
Create Date: 2026-03-29 21:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260329_04"
down_revision = "20260329_03"
branch_labels = None
depends_on = None

旧文章状态枚举 = postgresql.ENUM("draft", "published", name="articlestatus_old")
新文章状态枚举 = postgresql.ENUM("private", "login_required", "public", name="articlestatus")


def upgrade() -> None:
    """升级迁移。"""
    bind = op.get_bind()

    op.drop_constraint("ck_articles_status_published_at", "articles", type_="check")
    op.execute("ALTER TYPE articlestatus RENAME TO articlestatus_old")
    新文章状态枚举.create(bind, checkfirst=False)

    op.execute(
        """
        ALTER TABLE articles
        ALTER COLUMN status TYPE articlestatus
        USING (
            CASE status::text
                WHEN 'draft' THEN 'private'
                WHEN 'published' THEN 'public'
            END
        )::articlestatus
        """
    )

    旧文章状态枚举.drop(bind, checkfirst=False)
    op.create_check_constraint(
        "ck_articles_status_published_at",
        "articles",
        "(status = 'private' AND published_at IS NULL) OR "
        "(status IN ('login_required', 'public') AND published_at IS NOT NULL)",
    )


def downgrade() -> None:
    """回滚迁移。"""
    bind = op.get_bind()

    op.execute("UPDATE articles SET status = 'public' WHERE status = 'login_required'")
    op.drop_constraint("ck_articles_status_published_at", "articles", type_="check")
    op.execute("ALTER TYPE articlestatus RENAME TO articlestatus_new")
    旧文章状态枚举.create(bind, checkfirst=False)

    op.execute(
        """
        ALTER TABLE articles
        ALTER COLUMN status TYPE articlestatus_old
        USING (
            CASE status::text
                WHEN 'private' THEN 'draft'
                WHEN 'public' THEN 'published'
            END
        )::articlestatus_old
        """
    )

    新文章状态枚举.drop(bind, checkfirst=False)
    op.execute("ALTER TYPE articlestatus_old RENAME TO articlestatus")
    op.create_check_constraint(
        "ck_articles_status_published_at",
        "articles",
        "(status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)",
    )
