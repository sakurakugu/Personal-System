"""账单服务单测。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

from sqlalchemy.dialects import postgresql

from app.modules.bills.common import (
    build_month_summary as _build_month_summary,
    calculate_account_record_deltas as _calculate_account_record_deltas,
    resolve_template_occurred_at as _resolve_template_occurred_at,
)
from app.modules.bills.service import ensure_default_bill_setup
from app.modules.users.models import User
from app.models.bill import BillAccount, BillAccountType, BillCategory, BillCategoryType, BillRecord, BillRecordType
from app.utils.uuid import generate_uuid7


LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc


def local_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造本地时区时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=LOCAL_TZ)


def build_account(name: str, account_type: BillAccountType) -> BillAccount:
    """构造测试账户。"""
    return BillAccount(
        id=generate_uuid7(),
        user_id=generate_uuid7(),
        name=name,
        type=account_type,
        initial_balance_cent=0,
        note=None,
        created_at=local_dt(2026, 3, 1),
        updated_at=local_dt(2026, 3, 1),
    )


def build_category(name: str, category_type: BillCategoryType, color: str) -> BillCategory:
    """构造测试分类。"""
    return BillCategory(
        id=generate_uuid7(),
        user_id=generate_uuid7(),
        type=category_type,
        name=name,
        color=color,
        icon="test",
        sort_order=0,
        created_at=local_dt(2026, 3, 1),
        updated_at=local_dt(2026, 3, 1),
    )


class BillServiceTest(unittest.TestCase):
    """账单服务逻辑测试。"""

    def test_账户余额增量会正确处理收入支出和转账(self) -> None:
        cash_account = build_account("现金", BillAccountType.cash)
        card_account = build_account("银行卡", BillAccountType.debit_card)

        records = [
            BillRecord(
                user_id=generate_uuid7(),
                type=BillRecordType.income,
                account_id=cash_account.id,
                amount_cent=5000,
                occurred_at=local_dt(2026, 3, 1, 9, 0),
            ),
            BillRecord(
                user_id=generate_uuid7(),
                type=BillRecordType.expense,
                account_id=cash_account.id,
                amount_cent=1200,
                occurred_at=local_dt(2026, 3, 1, 12, 0),
            ),
            BillRecord(
                user_id=generate_uuid7(),
                type=BillRecordType.transfer,
                account_id=cash_account.id,
                target_account_id=card_account.id,
                amount_cent=2000,
                occurred_at=local_dt(2026, 3, 2, 8, 0),
            ),
        ]

        deltas = _calculate_account_record_deltas(records)

        self.assertEqual(deltas[cash_account.id], 1800)
        self.assertEqual(deltas[card_account.id], 2000)

    def test_月汇总会忽略转账并聚合分类与天维度(self) -> None:
        account = build_account("现金", BillAccountType.cash)
        food_category = build_category("餐饮", BillCategoryType.expense, "#f97316")
        salary_category = build_category("工资", BillCategoryType.income, "#16a34a")

        income_record = BillRecord(
            user_id=generate_uuid7(),
            type=BillRecordType.income,
            account_id=account.id,
            amount_cent=10000,
            occurred_at=local_dt(2026, 3, 1, 9, 0),
            category=salary_category,
            category_id=salary_category.id,
            account=account,
        )
        expense_record = BillRecord(
            user_id=generate_uuid7(),
            type=BillRecordType.expense,
            account_id=account.id,
            amount_cent=2300,
            occurred_at=local_dt(2026, 3, 1, 12, 0),
            category=food_category,
            category_id=food_category.id,
            account=account,
        )
        transfer_record = BillRecord(
            user_id=generate_uuid7(),
            type=BillRecordType.transfer,
            account_id=account.id,
            target_account_id=generate_uuid7(),
            amount_cent=5000,
            occurred_at=local_dt(2026, 3, 2, 8, 0),
            account=account,
        )

        summary = _build_month_summary("2026-03", [income_record, expense_record, transfer_record])

        self.assertEqual(summary.income_cent, 10000)
        self.assertEqual(summary.expense_cent, 2300)
        self.assertEqual(summary.net_cent, 7700)
        self.assertEqual(summary.record_count, 3)
        self.assertEqual(len(summary.daily_totals), 1)
        self.assertEqual(summary.daily_totals[0].income_cent, 10000)
        self.assertEqual(summary.daily_totals[0].expense_cent, 2300)
        self.assertEqual(len(summary.category_totals), 2)

    def test_固定账单会在短月回退到月末日期(self) -> None:
        occurred_at = _resolve_template_occurred_at("2026-02", 31).astimezone(LOCAL_TZ)

        self.assertEqual((occurred_at.year, occurred_at.month, occurred_at.day), (2026, 2, 28))
        self.assertEqual((occurred_at.hour, occurred_at.minute), (9, 0))


class BillSetupTest(unittest.IsolatedAsyncioTestCase):
    """默认账单初始化测试。"""

    async def test_默认初始化会使用幂等插入语句避免并发冲突(self) -> None:
        db = AsyncMock()
        user = cast(User, SimpleNamespace(id=generate_uuid7()))

        await ensure_default_bill_setup(db, user)

        self.assertEqual(db.execute.await_count, 2)

        account_stmt = db.execute.await_args_list[0].args[0]
        category_stmt = db.execute.await_args_list[1].args[0]
        account_sql = str(account_stmt.compile(dialect=postgresql.dialect()))
        category_sql = str(category_stmt.compile(dialect=postgresql.dialect()))

        self.assertIn("ON CONFLICT ON CONSTRAINT uq_bill_accounts_user_id_name DO NOTHING", account_sql)
        self.assertIn("ON CONFLICT ON CONSTRAINT uq_bill_categories_user_id_type_name DO NOTHING", category_sql)


if __name__ == "__main__":
    unittest.main()
