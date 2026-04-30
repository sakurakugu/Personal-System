"""为用户新增首页显示私有文章设置。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_00"
down_revision = "20260329_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.add_column(
        "users",
        sa.Column(
            "show_private_articles_on_home",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("users", "show_private_articles_on_home", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("users", "show_private_articles_on_home")
