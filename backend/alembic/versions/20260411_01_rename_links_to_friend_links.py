"""将友链表技术命名改为 friend_links。

Revision ID: 20260411_01
Revises: 20260411_00
Create Date: 2026-04-11 23:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260411_01"
down_revision = "20260411_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级迁移。"""
    op.rename_table("links", "friend_links")
    op.execute(sa.text("ALTER INDEX ix_links_status_created_at RENAME TO ix_friend_links_status_created_at"))
    op.execute(sa.text("ALTER TABLE friend_links RENAME CONSTRAINT links_pkey TO friend_links_pkey"))
    op.execute(sa.text("ALTER TABLE friend_links RENAME CONSTRAINT links_url_key TO friend_links_url_key"))


def downgrade() -> None:
    """回滚迁移。"""
    op.execute(sa.text("ALTER TABLE friend_links RENAME CONSTRAINT friend_links_url_key TO links_url_key"))
    op.execute(sa.text("ALTER TABLE friend_links RENAME CONSTRAINT friend_links_pkey TO links_pkey"))
    op.execute(sa.text("ALTER INDEX ix_friend_links_status_created_at RENAME TO ix_links_status_created_at"))
    op.rename_table("friend_links", "links")
