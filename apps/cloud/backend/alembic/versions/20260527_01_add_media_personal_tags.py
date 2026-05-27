"""新增文娱个人标签字段。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260527_01"
down_revision = "20260527_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "media_items",
        sa.Column("personal_tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
    )
    op.alter_column("media_items", "personal_tags", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("media_items", "personal_tags")
