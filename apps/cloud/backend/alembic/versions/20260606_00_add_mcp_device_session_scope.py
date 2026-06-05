"""新增 MCP 设备会话类型和权限范围。

Revision ID: 20260606_00
Revises: 20260601_00
Create Date: 2026-06-06 00:00:00
"""

from __future__ import annotations

from alembic import op


revision = "20260606_00"
down_revision = "20260601_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构。"""
    op.execute("ALTER TYPE devicesessiontype ADD VALUE IF NOT EXISTS 'mcp'")
    op.execute("ALTER TYPE devicesessionscope ADD VALUE IF NOT EXISTS 'mcp_readonly'")
    op.execute("ALTER TYPE devicesessionscope ADD VALUE IF NOT EXISTS 'mcp_full'")


def downgrade() -> None:
    """回滚数据库结构。

    PostgreSQL 不支持安全删除 enum value，这里保留枚举值。
    """

