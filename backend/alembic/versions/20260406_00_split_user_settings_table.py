"""拆分独立用户设置表。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260406_00"
down_revision = "20260403_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "user_settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("show_private_articles_on_home", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO user_settings (user_id, show_private_articles_on_home, created_at, updated_at)
            SELECT id, show_private_articles_on_home, created_at, updated_at
            FROM users
            """
        )
    )
    op.alter_column("user_settings", "show_private_articles_on_home", server_default=None)
    op.alter_column("user_settings", "created_at", server_default=None)
    op.alter_column("user_settings", "updated_at", server_default=None)
    op.drop_column("users", "show_private_articles_on_home")


def downgrade() -> None:
    """回滚数据库结构。"""
    op.add_column(
        "users",
        sa.Column(
            "show_private_articles_on_home",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE users AS u
            SET show_private_articles_on_home = s.show_private_articles_on_home
            FROM user_settings AS s
            WHERE s.user_id = u.id
            """
        )
    )
    op.alter_column("users", "show_private_articles_on_home", server_default=None)
    op.drop_table("user_settings")
