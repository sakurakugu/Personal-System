"""新增固定账单模板。

Revision ID: 20260329_03
Revises: 20260329_02
Create Date: 2026-03-29 19:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260329_03"
down_revision = "20260329_02"
branch_labels = None
depends_on = None


BILL_RECORD_TYPE_ENUM = postgresql.ENUM(
    "expense",
    "income",
    "transfer",
    name="billrecordtype",
    create_type=False,
)


def upgrade() -> None:
    """升级数据库结构。"""
    op.create_table(
        "bill_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("type", BILL_RECORD_TYPE_ENUM, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_cent", sa.Integer(), nullable=False),
        sa.Column("merchant", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_cent > 0", name="ck_bill_templates_amount_cent_positive"),
        sa.CheckConstraint("day_of_month >= 1 AND day_of_month <= 31", name="ck_bill_templates_day_of_month_range"),
        sa.CheckConstraint(
            "target_account_id IS NULL OR target_account_id <> account_id",
            name="ck_bill_templates_target_account_not_same",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["bill_accounts.id"]),
        sa.ForeignKeyConstraint(["target_account_id"], ["bill_accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["bill_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bill_templates_user_id_is_active_created_at",
        "bill_templates",
        ["user_id", "is_active", "created_at"],
        unique=False,
    )

    op.add_column("bill_records", sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("bill_records", sa.Column("template_month", sa.String(length=7), nullable=True))
    op.create_foreign_key(
        "fk_bill_records_template_id_bill_templates",
        "bill_records",
        "bill_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_bill_records_template_id_template_month",
        "bill_records",
        ["template_id", "template_month"],
        unique=False,
    )
    op.create_index(
        "uq_bill_records_template_id_template_month",
        "bill_records",
        ["template_id", "template_month"],
        unique=True,
        postgresql_where=sa.text("template_id IS NOT NULL AND template_month IS NOT NULL"),
    )


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_index("uq_bill_records_template_id_template_month", table_name="bill_records")
    op.drop_index("ix_bill_records_template_id_template_month", table_name="bill_records")
    op.drop_constraint("fk_bill_records_template_id_bill_templates", "bill_records", type_="foreignkey")
    op.drop_column("bill_records", "template_month")
    op.drop_column("bill_records", "template_id")

    op.drop_index("ix_bill_templates_user_id_is_active_created_at", table_name="bill_templates")
    op.drop_table("bill_templates")
