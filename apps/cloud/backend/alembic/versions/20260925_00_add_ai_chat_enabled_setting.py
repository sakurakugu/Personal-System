"""增加前台 AI 对话挂件显示开关。"""

from alembic import op

revision = "20260925_00"
down_revision = "20260914_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO system_settings (key, bool_value, str_value, updated_at) "
        "VALUES ('ai_chat_enabled', FALSE, NULL, TIMEZONE('utc', NOW())) "
        "ON CONFLICT (key) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key = 'ai_chat_enabled'")
