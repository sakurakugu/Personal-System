"""为用户表增加邮箱判重键。

Revision ID: 20260411_00
Revises: 20260408_01
Create Date: 2026-04-11 22:30:00
"""

from __future__ import annotations

from collections import defaultdict

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260411_00"
down_revision = "20260408_01"
branch_labels = None
depends_on = None

谷歌邮箱域名集合 = frozenset({"gmail.com", "googlemail.com"})


def 构建邮箱身份(email: str) -> str:
    """生成用于判重的邮箱标识。"""
    normalized = email.strip()
    local_part, separator, domain_part = normalized.rpartition("@")
    if not separator:
        return normalized.lower()

    normalized_domain = domain_part.lower()
    if normalized_domain not in 谷歌邮箱域名集合:
        return f"{local_part}@{normalized_domain}"

    normalized_local = local_part.lower()
    plus_index = normalized_local.find("+")
    if plus_index >= 0:
        normalized_local = normalized_local[:plus_index]
    normalized_local = normalized_local.replace(".", "")
    return f"{normalized_local}@gmail.com"


def ensure_no_email_identity_conflicts(rows: list[sa.RowMapping]) -> None:
    """在创建唯一约束前检测冲突数据。"""
    grouped: dict[str, list[sa.RowMapping]] = defaultdict(list)
    for row in rows:
        grouped[构建邮箱身份(str(row["email"]))].append(row)

    conflicts = {key: items for key, items in grouped.items() if len(items) > 1}
    if not conflicts:
        return

    samples: list[str] = []
    for key, items in list(conflicts.items())[:5]:
        users = ", ".join(f'{item["username"]}<{item["email"]}>' for item in items)
        samples.append(f"{key}: {users}")
    raise RuntimeError("发现邮箱判重键冲突，无法自动迁移，请先手动处理：" + "；".join(samples))


def upgrade() -> None:
    """升级迁移。"""
    op.add_column("users", sa.Column("email_identity", sa.String(length=255), nullable=True))

    bind = op.get_bind()
    rows = list(
        bind.execute(sa.text("SELECT id, username, email FROM users ORDER BY created_at ASC, id ASC")).mappings()
    )
    ensure_no_email_identity_conflicts(rows)

    update_sql = sa.text("UPDATE users SET email_identity = :email_identity WHERE id = :id")
    for row in rows:
        bind.execute(
            update_sql,
            {
                "id": row["id"],
                "email_identity": 构建邮箱身份(str(row["email"])),
            },
        )

    op.alter_column("users", "email_identity", existing_type=sa.String(length=255), nullable=False)
    op.create_unique_constraint("uq_users_email_identity", "users", ["email_identity"])
    op.create_index("ix_users_email_identity", "users", ["email_identity"], unique=False)


def downgrade() -> None:
    """回滚迁移。"""
    op.drop_index("ix_users_email_identity", table_name="users")
    op.drop_constraint("uq_users_email_identity", "users", type_="unique")
    op.drop_column("users", "email_identity")
