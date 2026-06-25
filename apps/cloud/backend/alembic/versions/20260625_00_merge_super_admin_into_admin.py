"""合并超级管理员到管理员。

Revision ID: 20260625_00
Revises: 20260607_00
Create Date: 2026-06-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260625_00"
down_revision = "20260607_00"
branch_labels = None
depends_on = None


def _枚举包含值(enum_name: str, value: str) -> bool:
    """判断 PostgreSQL 枚举是否包含指定值。"""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = :enum_name AND e.enumlabel = :value
            LIMIT 1
            """
        ),
        {"enum_name": enum_name, "value": value},
    )
    return result.scalar_one_or_none() is not None


def upgrade() -> None:
    """升级数据库结构。"""
    op.execute("UPDATE ai_settings SET access_policy = 'admin' WHERE access_policy = 'super_admin'")
    if _枚举包含值("userrole", "super_admin"):
        op.execute("UPDATE users SET role = 'user'::userrole WHERE role = 'admin'")
        op.execute(
            """
            WITH ranked_super_admins AS (
                SELECT id, row_number() OVER (ORDER BY created_at ASC, id ASC) AS rank
                FROM users
                WHERE role = 'super_admin'
            )
            UPDATE users
            SET role = CASE
                WHEN ranked_super_admins.rank = 1 THEN 'admin'::userrole
                ELSE 'user'::userrole
            END
            FROM ranked_super_admins
            WHERE users.id = ranked_super_admins.id
            """
        )
        op.execute("ALTER TYPE userrole RENAME TO userrole_old")
        op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user')")
        op.execute(
            """
            ALTER TABLE users
            ALTER COLUMN role TYPE userrole
            USING role::text::userrole
            """
        )
        op.execute("DROP TYPE userrole_old")
    else:
        op.execute(
            """
            WITH ranked_admins AS (
                SELECT id, row_number() OVER (ORDER BY created_at ASC, id ASC) AS rank
                FROM users
                WHERE role = 'admin'
            )
            UPDATE users
            SET role = 'user'::userrole
            FROM ranked_admins
            WHERE users.id = ranked_admins.id AND ranked_admins.rank > 1
            """
        )
    op.create_index(
        "uq_users_single_admin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'admin'"),
        if_not_exists=True,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("uq_users_single_admin", table_name="users", if_exists=True)
    if not _枚举包含值("userrole", "super_admin"):
        op.execute("ALTER TYPE userrole RENAME TO userrole_old")
        op.execute("CREATE TYPE userrole AS ENUM ('super_admin', 'admin', 'user')")
        op.execute(
            """
            ALTER TABLE users
            ALTER COLUMN role TYPE userrole
            USING role::text::userrole
            """
        )
        op.execute("DROP TYPE userrole_old")
