"""为动态新增最后编辑时间。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260505_00"
down_revision = "20260504_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "moments",
        sa.Column(
            "last_edited_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE moments
            SET last_edited_at = COALESCE(published_at, created_at)
            """
        )
    )
    op.alter_column("moments", "last_edited_at", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("moments", "last_edited_at")
