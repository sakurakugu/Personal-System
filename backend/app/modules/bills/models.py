"""账单相关模型。"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.common import utcnow
from app.shared.db.session import Base
from app.utils.uuid import generate_uuid7

if TYPE_CHECKING:
    from app.models.user import User


class BillAccountType(str, enum.Enum):
    """账单账户类型。"""

    cash = "cash"
    debit_card = "debit_card"
    credit_card = "credit_card"
    wechat = "wechat"
    alipay = "alipay"
    other = "other"


class BillCategoryType(str, enum.Enum):
    """账单分类类型。"""

    expense = "expense"
    income = "income"


class BillRecordType(str, enum.Enum):
    """账单流水类型。"""

    expense = "expense"
    income = "income"
    transfer = "transfer"


class BillTemplate(Base):
    """固定账单模板。"""

    __tablename__ = "bill_templates"
    __table_args__ = (
        CheckConstraint("amount_cent > 0", name="ck_bill_templates_amount_cent_positive"),
        CheckConstraint("day_of_month >= 1 AND day_of_month <= 31", name="ck_bill_templates_day_of_month_range"),
        CheckConstraint(
            "target_account_id IS NULL OR target_account_id <> account_id",
            name="ck_bill_templates_target_account_not_same",
        ),
        Index("ix_bill_templates_user_id_is_active_created_at", "user_id", "is_active", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[BillRecordType] = mapped_column(Enum(BillRecordType), nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_accounts.id"),
        nullable=False,
    )
    target_account_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_accounts.id"),
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_categories.id"),
    )
    amount_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="bill_templates")
    account: Mapped["BillAccount"] = relationship(foreign_keys=[account_id])
    target_account: Mapped["BillAccount | None"] = relationship(foreign_keys=[target_account_id])
    category: Mapped["BillCategory | None"] = relationship(foreign_keys=[category_id])
    generated_records: Mapped[list["BillRecord"]] = relationship(back_populates="template")


class BillAccount(Base):
    """账单账户。"""

    __tablename__ = "bill_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_bill_accounts_user_id_name"),
        Index("ix_bill_accounts_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    type: Mapped[BillAccountType] = mapped_column(Enum(BillAccountType), nullable=False)
    initial_balance_cent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="bill_accounts")
    source_records: Mapped[list["BillRecord"]] = relationship(
        back_populates="account",
        foreign_keys="BillRecord.account_id",
    )
    target_records: Mapped[list["BillRecord"]] = relationship(
        back_populates="target_account",
        foreign_keys="BillRecord.target_account_id",
    )


class BillCategory(Base):
    """账单分类。"""

    __tablename__ = "bill_categories"
    __table_args__ = (
        UniqueConstraint("user_id", "type", "name", name="uq_bill_categories_user_id_type_name"),
        Index("ix_bill_categories_user_id_type_sort_order", "user_id", "type", "sort_order"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[BillCategoryType] = mapped_column(Enum(BillCategoryType), nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#94a3b8", nullable=False)
    icon: Mapped[str] = mapped_column(String(40), default="folder", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="bill_categories")
    records: Mapped[list["BillRecord"]] = relationship(back_populates="category")


class BillRecord(Base):
    """账单流水。"""

    __tablename__ = "bill_records"
    __table_args__ = (
        CheckConstraint("amount_cent > 0", name="ck_bill_records_amount_cent_positive"),
        CheckConstraint(
            "target_account_id IS NULL OR target_account_id <> account_id",
            name="ck_bill_records_target_account_not_same",
        ),
        Index("ix_bill_records_user_id_occurred_at", "user_id", "occurred_at"),
        Index("ix_bill_records_account_id_occurred_at", "account_id", "occurred_at"),
        Index("ix_bill_records_category_id_occurred_at", "category_id", "occurred_at"),
        Index("ix_bill_records_template_id_template_month", "template_id", "template_month"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[BillRecordType] = mapped_column(Enum(BillRecordType), nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_accounts.id"),
        nullable=False,
    )
    target_account_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_accounts.id"),
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_categories.id"),
    )
    template_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bill_templates.id", ondelete="SET NULL"),
    )
    template_month: Mapped[str | None] = mapped_column(String(7))
    amount_cent: Mapped[int] = mapped_column(Integer, nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="bill_records")
    account: Mapped["BillAccount"] = relationship(
        back_populates="source_records",
        foreign_keys=[account_id],
    )
    target_account: Mapped["BillAccount | None"] = relationship(
        back_populates="target_records",
        foreign_keys=[target_account_id],
    )
    category: Mapped["BillCategory | None"] = relationship(back_populates="records")
    template: Mapped["BillTemplate | None"] = relationship(back_populates="generated_records")
