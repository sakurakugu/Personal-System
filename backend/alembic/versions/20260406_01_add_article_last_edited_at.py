"""为文章新增最后编辑时间。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260406_01"
down_revision = "20260406_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "articles",
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
            UPDATE articles
            SET last_edited_at = created_at
            """
        )
    )
    op.alter_column("articles", "last_edited_at", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("articles", "last_edited_at")
