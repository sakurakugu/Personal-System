"""将 AI 访问策略统一为登录用户。"""

from __future__ import annotations

from alembic import op


revision = "20260913_01"
down_revision = "20260913_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """清理单用户模式下不再适用的管理员策略。"""
    op.execute("UPDATE ai_settings SET access_policy = 'login' WHERE access_policy <> 'login'")


def downgrade() -> None:
    """策略统一不可逆，回滚不恢复管理员限制。"""
    pass
