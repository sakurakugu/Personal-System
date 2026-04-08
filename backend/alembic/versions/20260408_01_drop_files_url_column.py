"""移除 files 表中的冗余 url 字段。

Revision ID: 20260408_01
Revises: 20260408_00
Create Date: 2026-04-08 17:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260408_01"
down_revision = "20260408_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级迁移。"""
    op.drop_column("files", "url")


def downgrade() -> None:
    """回滚迁移。"""
    op.add_column("files", sa.Column("url", sa.String(length=1000), nullable=True))
    op.execute(sa.text("UPDATE files SET url = '/files/' || storage_key"))
    op.alter_column("files", "url", nullable=False)
