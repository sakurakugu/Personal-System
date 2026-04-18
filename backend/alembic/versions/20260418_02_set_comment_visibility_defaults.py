"""将评论区默认设置调整为隐藏且关闭。

Revision ID: 20260418_02
Revises: 20260418_01
Create Date: 2026-04-18 20:55:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260418_02"
down_revision = "20260418_01"
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
            ON CONFLICT (key) DO UPDATE
            SET bool_value = EXCLUDED.bool_value,
                str_value = NULL,
                updated_at = TIMEZONE('utc', NOW())
            """
        )
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.execute(
        sa.text(
            """
            UPDATE system_settings
            SET bool_value = CASE
                WHEN key = 'comments_enabled' THEN TRUE
                WHEN key = 'comments_hidden' THEN FALSE
                ELSE bool_value
            END,
            str_value = NULL,
            updated_at = TIMEZONE('utc', NOW())
            WHERE key IN ('comments_enabled', 'comments_hidden')
            """
        )
    )
