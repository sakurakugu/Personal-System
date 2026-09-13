"""将工具页面默认设置为关闭。"""

from alembic import op

revision = "20260914_00"
down_revision = "20260913_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 该记录由上一条迁移创建，更新为新的默认关闭状态。
    op.execute(
        "UPDATE system_settings SET bool_value = FALSE, updated_at = TIMEZONE('utc', NOW()) "
        "WHERE key = 'tools_enabled'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE system_settings SET bool_value = TRUE, updated_at = TIMEZONE('utc', NOW()) "
        "WHERE key = 'tools_enabled'"
    )
