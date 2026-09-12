"""将现有多用户数据合并到唯一拥有者账号。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260913_00"
down_revision = "20260625_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """保留最早的管理员账号，将其他账号的数据转移给它。"""
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM system_settings WHERE key = 'register_enabled'"))
    owner = bind.execute(
        sa.text(
            """
            SELECT id FROM users
            ORDER BY (role = 'admin') DESC, created_at ASC, id ASC
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    if owner is None:
        return

    # 唯一设置记录无法直接合并，保留拥有者的设置。
    bind.execute(sa.text("DELETE FROM user_settings WHERE user_id <> :owner"), {"owner": owner})

    # 从数据库元数据读取所有指向 users.id 的外键，覆盖业务表、设备会话和日志表。
    foreign_keys = bind.execute(
        sa.text(
            """
            SELECT DISTINCT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.constraint_schema = kcu.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.constraint_schema = ccu.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = current_schema()
              AND ccu.table_name = 'users'
              AND tc.table_name <> 'users'
            """
        )
    ).all()
    for table_name, column_name in foreign_keys:
        # 标识符来自 information_schema，转义双引号后再拼接 SQL。
        table = str(table_name).replace('"', '""')
        column = str(column_name).replace('"', '""')
        bind.execute(
            sa.text(
                f'UPDATE "{table}" SET "{column}" = :owner '
                f'WHERE "{column}" IS NOT NULL AND "{column}" <> :owner'
            ),
            {"owner": owner},
        )

    bind.execute(sa.text("DELETE FROM users WHERE id <> :owner"), {"owner": owner})


def downgrade() -> None:
    """单用户合并不可逆，数据恢复需使用部署前备份。"""
    pass
