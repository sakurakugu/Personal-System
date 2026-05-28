"""移除旧版独立小工具设备凭证。"""

from __future__ import annotations

from alembic import op


revision = "20260528_00"
down_revision = "20260527_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.execute("DELETE FROM user_device_sessions WHERE device_type = 'widget' OR scope = 'widget_basic'")
    op.execute("ALTER TYPE devicesessiontype RENAME TO devicesessiontype_old")
    op.execute("CREATE TYPE devicesessiontype AS ENUM ('desktop', 'phone', 'other')")
    op.execute(
        """
        ALTER TABLE user_device_sessions
        ALTER COLUMN device_type TYPE devicesessiontype
        USING device_type::text::devicesessiontype
        """
    )
    op.execute("DROP TYPE devicesessiontype_old")

    op.execute("ALTER TYPE devicesessionscope RENAME TO devicesessionscope_old")
    op.execute("CREATE TYPE devicesessionscope AS ENUM ('full_client')")
    op.execute(
        """
        ALTER TABLE user_device_sessions
        ALTER COLUMN scope TYPE devicesessionscope
        USING scope::text::devicesessionscope
        """
    )
    op.execute("DROP TYPE devicesessionscope_old")


def downgrade() -> None:
    """回滚数据库结构。"""
    op.execute("ALTER TYPE devicesessiontype RENAME TO devicesessiontype_old")
    op.execute("CREATE TYPE devicesessiontype AS ENUM ('desktop', 'widget', 'phone', 'other')")
    op.execute(
        """
        ALTER TABLE user_device_sessions
        ALTER COLUMN device_type TYPE devicesessiontype
        USING device_type::text::devicesessiontype
        """
    )
    op.execute("DROP TYPE devicesessiontype_old")

    op.execute("ALTER TYPE devicesessionscope RENAME TO devicesessionscope_old")
    op.execute("CREATE TYPE devicesessionscope AS ENUM ('full_client', 'widget_basic')")
    op.execute(
        """
        ALTER TABLE user_device_sessions
        ALTER COLUMN scope TYPE devicesessionscope
        USING scope::text::devicesessionscope
        """
    )
    op.execute("DROP TYPE devicesessionscope_old")
