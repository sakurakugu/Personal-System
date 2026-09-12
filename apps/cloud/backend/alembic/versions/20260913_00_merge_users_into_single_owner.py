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

    # 先合并按用户维度带唯一约束的实体，避免改 user_id 时触发冲突。
    # 账单账户：按名称复用 owner 账户，并重映射流水和模板引用。
    bind.execute(sa.text("""
        UPDATE bill_records r SET account_id = a_owner.id
        FROM bill_accounts a_old
        JOIN bill_accounts a_owner ON a_owner.user_id = :owner AND a_owner.name = a_old.name
        WHERE r.account_id = a_old.id AND a_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("""
        UPDATE bill_records r SET target_account_id = a_owner.id
        FROM bill_accounts a_old
        JOIN bill_accounts a_owner ON a_owner.user_id = :owner AND a_owner.name = a_old.name
        WHERE r.target_account_id = a_old.id AND a_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("""
        UPDATE bill_templates t SET account_id = a_owner.id
        FROM bill_accounts a_old
        JOIN bill_accounts a_owner ON a_owner.user_id = :owner AND a_owner.name = a_old.name
        WHERE t.account_id = a_old.id AND a_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("""
        UPDATE bill_templates t SET target_account_id = a_owner.id
        FROM bill_accounts a_old
        JOIN bill_accounts a_owner ON a_owner.user_id = :owner AND a_owner.name = a_old.name
        WHERE t.target_account_id = a_old.id AND a_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("DELETE FROM bill_accounts WHERE user_id <> :owner"), {"owner": owner})

    # 账单分类：按类型和名称复用 owner 分类，并重映射引用。
    for table in ("bill_records", "bill_templates"):
        bind.execute(sa.text(f"""
            UPDATE {table} r SET category_id = c_owner.id
            FROM bill_categories c_old
            JOIN bill_categories c_owner
              ON c_owner.user_id = :owner AND c_owner.type = c_old.type AND c_owner.name = c_old.name
            WHERE r.category_id = c_old.id AND c_old.user_id <> :owner
        """), {"owner": owner})
    bind.execute(sa.text("DELETE FROM bill_categories WHERE user_id <> :owner"), {"owner": owner})

    # 资料/待办标签：关联表先改到 owner 同名标签，再删除旧标签。
    bind.execute(sa.text("""
        DELETE FROM material_tag_relations r
        USING material_tag_relations r_owner, material_tags t_old, material_tags t_owner
        WHERE r.tag_id = t_old.id AND t_old.user_id <> :owner
          AND t_owner.user_id = :owner AND t_owner.name = t_old.name
          AND r_owner.material_id = r.material_id AND r_owner.tag_id = t_owner.id
    """), {"owner": owner})
    bind.execute(sa.text("""
        UPDATE material_tag_relations r SET tag_id = t_owner.id
        FROM material_tags t_old
        JOIN material_tags t_owner ON t_owner.user_id = :owner AND t_owner.name = t_old.name
        WHERE r.tag_id = t_old.id AND t_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("DELETE FROM material_tags WHERE user_id <> :owner"), {"owner": owner})
    bind.execute(sa.text("""
        DELETE FROM todo_tag_relations r
        USING todo_tag_relations r_owner, todo_tags t_old, todo_tags t_owner
        WHERE r.tag_id = t_old.id AND t_old.user_id <> :owner
          AND t_owner.user_id = :owner AND t_owner.name = t_old.name
          AND r_owner.todo_id = r.todo_id AND r_owner.tag_id = t_owner.id
    """), {"owner": owner})
    bind.execute(sa.text("""
        UPDATE todo_tag_relations r SET tag_id = t_owner.id
        FROM todo_tags t_old
        JOIN todo_tags t_owner ON t_owner.user_id = :owner AND t_owner.name = t_old.name
        WHERE r.tag_id = t_old.id AND t_old.user_id <> :owner
    """), {"owner": owner})
    bind.execute(sa.text("DELETE FROM todo_tags WHERE user_id <> :owner"), {"owner": owner})

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
