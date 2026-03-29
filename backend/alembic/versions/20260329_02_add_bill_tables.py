"""新增账单模块数据表。

Revision ID: 20260329_02
Revises: 20260329_01
Create Date: 2026-03-29 01:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260329_02"
down_revision = "20260329_01"
branch_labels = None
depends_on = None


BILL_ACCOUNT_TYPE_ENUM = postgresql.ENUM(
    "cash",
    "debit_card",
    "credit_card",
    "wechat",
    "alipay",
    "other",
    name="billaccounttype",
    create_type=False,
)
BILL_CATEGORY_TYPE_ENUM = postgresql.ENUM(
    "expense",
    "income",
    name="billcategorytype",
    create_type=False,
)
BILL_RECORD_TYPE_ENUM = postgresql.ENUM(
    "expense",
    "income",
    "transfer",
    name="billrecordtype",
    create_type=False,
)


def upgrade() -> None:
    """升级数据库结构。"""
    bind = op.get_bind()
    BILL_ACCOUNT_TYPE_ENUM.create(bind, checkfirst=True)
    BILL_CATEGORY_TYPE_ENUM.create(bind, checkfirst=True)
    BILL_RECORD_TYPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "bill_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("type", BILL_ACCOUNT_TYPE_ENUM, nullable=False),
        sa.Column("initial_balance_cent", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_bill_accounts_user_id_name"),
    )
    op.create_index(
        "ix_bill_accounts_user_id_created_at",
        "bill_accounts",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "bill_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", BILL_CATEGORY_TYPE_ENUM, nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.Column("icon", sa.String(length=40), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "type", "name", name="uq_bill_categories_user_id_type_name"),
    )
    op.create_index(
        "ix_bill_categories_user_id_type_sort_order",
        "bill_categories",
        ["user_id", "type", "sort_order"],
        unique=False,
    )

    op.create_table(
        "bill_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", BILL_RECORD_TYPE_ENUM, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_cent", sa.Integer(), nullable=False),
        sa.Column("merchant", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_cent > 0", name="ck_bill_records_amount_cent_positive"),
        sa.CheckConstraint(
            "target_account_id IS NULL OR target_account_id <> account_id",
            name="ck_bill_records_target_account_not_same",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["bill_accounts.id"]),
        sa.ForeignKeyConstraint(["target_account_id"], ["bill_accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["bill_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bill_records_user_id_occurred_at",
        "bill_records",
        ["user_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_bill_records_account_id_occurred_at",
        "bill_records",
        ["account_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_bill_records_category_id_occurred_at",
        "bill_records",
        ["category_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("ix_bill_records_category_id_occurred_at", table_name="bill_records")
    op.drop_index("ix_bill_records_account_id_occurred_at", table_name="bill_records")
    op.drop_index("ix_bill_records_user_id_occurred_at", table_name="bill_records")
    op.drop_table("bill_records")
    op.drop_index("ix_bill_categories_user_id_type_sort_order", table_name="bill_categories")
    op.drop_table("bill_categories")
    op.drop_index("ix_bill_accounts_user_id_created_at", table_name="bill_accounts")
    op.drop_table("bill_accounts")

    bind = op.get_bind()
    BILL_RECORD_TYPE_ENUM.drop(bind, checkfirst=True)
    BILL_CATEGORY_TYPE_ENUM.drop(bind, checkfirst=True)
    BILL_ACCOUNT_TYPE_ENUM.drop(bind, checkfirst=True)
