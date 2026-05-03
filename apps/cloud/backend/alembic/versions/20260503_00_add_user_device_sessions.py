"""新增用户设备会话表。

Revision ID: 20260503_00
Revises: 20260419_00
Create Date: 2026-05-03 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260503_00"
down_revision = "20260419_00"
branch_labels = None
depends_on = None


DEVICE_SESSION_TYPE_ENUM = postgresql.ENUM(
    "desktop",
    "widget",
    "phone",
    "other",
    name="devicesessiontype",
    create_type=False,
)
DEVICE_SESSION_SCOPE_ENUM = postgresql.ENUM(
    "full_client",
    "widget_basic",
    name="devicesessionscope",
    create_type=False,
)


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()
    DEVICE_SESSION_TYPE_ENUM.create(bind, checkfirst=True)
    DEVICE_SESSION_SCOPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "user_device_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=False),
        sa.Column("device_type", DEVICE_SESSION_TYPE_ENUM, nullable=False),
        sa.Column("scope", DEVICE_SESSION_SCOPE_ENUM, nullable=False),
        sa.Column("client_version", sa.String(length=50), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("last_ip", sa.String(length=64), nullable=True),
        sa.Column("last_user_agent", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_user_device_sessions_user_id",
        "user_device_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_device_sessions_user_id_revoked_at",
        "user_device_sessions",
        ["user_id", "revoked_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_device_sessions_expires_at",
        "user_device_sessions",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_user_device_sessions_expires_at", table_name="user_device_sessions")
    op.drop_index("ix_user_device_sessions_user_id_revoked_at", table_name="user_device_sessions")
    op.drop_index("ix_user_device_sessions_user_id", table_name="user_device_sessions")
    op.drop_table("user_device_sessions")

    bind = op.get_bind()
    DEVICE_SESSION_SCOPE_ENUM.drop(bind, checkfirst=True)
    DEVICE_SESSION_TYPE_ENUM.drop(bind, checkfirst=True)
