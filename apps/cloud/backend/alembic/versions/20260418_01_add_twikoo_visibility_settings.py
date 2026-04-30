"""补充 Twikoo 评论区显示设置。

Revision ID: 20260418_01
Revises: 20260418_00
Create Date: 2026-04-18 20:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260418_01"
down_revision = "20260418_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.execute(
        sa.text(
            """
            INSERT INTO system_settings (key, bool_value, str_value, updated_at)
            VALUES
              ('comments_enabled', FALSE, NULL, TIMEZONE('utc', NOW())),
              ('comments_hidden', TRUE, NULL, TIMEZONE('utc', NOW()))
            ON CONFLICT (key) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.execute(
        sa.text("DELETE FROM system_settings WHERE key IN ('comments_enabled', 'comments_hidden')")
    )
