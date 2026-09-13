"""增加工具页面显示开关。"""

from alembic import op

revision = "20260913_02"
down_revision = "20260913_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO system_settings (key, bool_value, str_value, updated_at) "
        "VALUES ('tools_enabled', TRUE, NULL, TIMEZONE('utc', NOW())) "
        "ON CONFLICT (key) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key = 'tools_enabled'")
