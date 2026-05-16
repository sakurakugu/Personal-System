"""账单公共规则与构造。"""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import 用户
from app.modules.bills.models import BillAccount, BillAccountType, BillCategory, BillCategoryType, BillRecord, BillRecordType, BillTemplate
from app.modules.bills.schemas import (
    BillAccountRead,
    BillAccountSimpleRead,
    BillCategoryRead,
    BillCategorySimpleRead,
    BillMonthSummaryRead,
    BillRecordRead,
    BillSummaryCategoryRead,
    BillSummaryDailyTotalRead,
    BillTemplateRead,
)
from app.utils.uuid import generate_uuid7

默认账户列表 = [
    {
        "name": "现金",
        "type": BillAccountType.cash,
        "initial_balance_cent": 0,
        "note": "默认账户",
    }
]

默认分类列表 = [
    {"type": BillCategoryType.expense, "name": "餐饮", "color": "#f97316", "icon": "food", "sort_order": 10},
    {"type": BillCategoryType.expense, "name": "交通", "color": "#0ea5e9", "icon": "bus", "sort_order": 20},
    {"type": BillCategoryType.expense, "name": "购物", "color": "#ec4899", "icon": "bag", "sort_order": 30},
    {"type": BillCategoryType.expense, "name": "居住", "color": "#8b5cf6", "icon": "home", "sort_order": 40},
    {"type": BillCategoryType.expense, "name": "娱乐", "color": "#22c55e", "icon": "game", "sort_order": 50},
    {"type": BillCategoryType.expense, "name": "医疗", "color": "#ef4444", "icon": "health", "sort_order": 60},
    {"type": BillCategoryType.expense, "name": "学习", "color": "#14b8a6", "icon": "book", "sort_order": 70},
    {"type": BillCategoryType.expense, "name": "其他", "color": "#94a3b8", "icon": "more", "sort_order": 99},
    {"type": BillCategoryType.income, "name": "工资", "color": "#16a34a", "icon": "salary", "sort_order": 10},
    {"type": BillCategoryType.income, "name": "奖金", "color": "#65a30d", "icon": "bonus", "sort_order": 20},
    {"type": BillCategoryType.income, "name": "理财", "color": "#0f766e", "icon": "chart", "sort_order": 30},
    {"type": BillCategoryType.income, "name": "退款", "color": "#2563eb", "icon": "refund", "sort_order": 40},
    {"type": BillCategoryType.income, "name": "其他", "color": "#64748b", "icon": "more", "sort_order": 99},
]


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def local_timezone():
    """返回系统当前本地时区。"""
    return datetime.now().astimezone().tzinfo or timezone.utc


def to_local(dt: datetime) -> datetime:
    """将时间统一转换为本地时区。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(local_timezone())


def 当前月份值() -> str:
    """返回当前本地月份字符串。"""
    return to_local(utcnow()).strftime("%Y-%m")


def 解析月份值(value: str | None) -> tuple[str, datetime, datetime]:
    """解析月份参数并返回对应的 UTC 区间。"""
    month_value = (value or 当前月份值()).strip()
    parts = month_value.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=422, detail="月份格式不正确，应为 YYYY-MM")

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="月份格式不正确，应为 YYYY-MM") from exc

    if year < 2000 or year > 2100 or month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="月份格式不正确，应为 YYYY-MM")

    current_local_timezone = local_timezone()
    start_local = datetime(year, month, 1, tzinfo=current_local_timezone)
    if month == 12:
        next_local = datetime(year + 1, 1, 1, tzinfo=current_local_timezone)
    else:
        next_local = datetime(year, month + 1, 1, tzinfo=current_local_timezone)

    return month_value, start_local.astimezone(timezone.utc), next_local.astimezone(timezone.utc)


def 解析账户类型(value: str) -> BillAccountType:
    """解析账户类型。"""
    try:
        return BillAccountType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的账户类型") from exc


def 解析分类类型(value: str) -> BillCategoryType:
    """解析分类类型。"""
    try:
        return BillCategoryType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的分类类型") from exc


def 解析记录类型(value: str) -> BillRecordType:
    """解析流水类型。"""
    try:
        return BillRecordType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的流水类型") from exc


def 构建账户简要(account: BillAccount) -> BillAccountSimpleRead:
    """构建账户简要响应。"""
    return BillAccountSimpleRead(
        id=UUID(str(account.id)),
        name=account.name,
        type=account.type.value,
    )


def 构建账户读取(account: BillAccount, *, current_balance_cent: int) -> BillAccountRead:
    """构建账户响应。"""
    return BillAccountRead(
        id=UUID(str(account.id)),
        name=account.name,
        type=account.type.value,
        initial_balance_cent=account.initial_balance_cent,
        current_balance_cent=current_balance_cent,
        note=account.note,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def 构建分类简要(category: BillCategory) -> BillCategorySimpleRead:
    """构建分类简要响应。"""
    return BillCategorySimpleRead(
        id=UUID(str(category.id)),
        type=category.type.value,
        name=category.name,
        color=category.color,
        icon=category.icon,
    )


def 构建分类读取(category: BillCategory) -> BillCategoryRead:
    """构建分类响应。"""
    return BillCategoryRead(
        id=UUID(str(category.id)),
        type=category.type.value,
        name=category.name,
        color=category.color,
        icon=category.icon,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def 账单记录查询():
    """构建账单流水详情查询。"""
    return select(BillRecord).options(
        selectinload(BillRecord.account),
        selectinload(BillRecord.target_account),
        selectinload(BillRecord.category),
        selectinload(BillRecord.template),
    )


def 账单模板查询():
    """构建固定账单模板详情查询。"""
    return select(BillTemplate).options(
        selectinload(BillTemplate.account),
        selectinload(BillTemplate.target_account),
        selectinload(BillTemplate.category),
    )


def 构建记录读取(record: BillRecord) -> BillRecordRead:
    """构建流水响应。"""
    return BillRecordRead(
        id=UUID(str(record.id)),
        template_id=UUID(str(record.template_id)) if record.template_id is not None else None,
        template_title=record.template.title if record.template is not None else None,
        type=record.type.value,
        amount_cent=record.amount_cent,
        merchant=record.merchant,
        note=record.note,
        occurred_at=record.occurred_at,
        account=构建账户简要(record.account),
        target_account=构建账户简要(record.target_account) if record.target_account is not None else None,
        category=构建分类简要(record.category) if record.category is not None else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def 构建模板读取(template: BillTemplate) -> BillTemplateRead:
    """构建固定账单模板响应。"""
    return BillTemplateRead(
        id=UUID(str(template.id)),
        title=template.title,
        type=template.type.value,
        amount_cent=template.amount_cent,
        merchant=template.merchant,
        note=template.note,
        day_of_month=template.day_of_month,
        is_active=template.is_active,
        account=构建账户简要(template.account),
        target_account=构建账户简要(template.target_account) if template.target_account is not None else None,
        category=构建分类简要(template.category) if template.category is not None else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def 计算账户记录差值(records: Sequence[BillRecord]) -> dict[UUID, int]:
    """根据流水计算各账户的余额增量。"""
    deltas: dict[UUID, int] = defaultdict(int)
    for record in records:
        if record.type == BillRecordType.expense:
            deltas[record.account_id] -= record.amount_cent
            continue
        if record.type == BillRecordType.income:
            deltas[record.account_id] += record.amount_cent
            continue
        deltas[record.account_id] -= record.amount_cent
        if record.target_account_id is not None:
            deltas[record.target_account_id] += record.amount_cent
    return dict(deltas)


def 构建月度汇总(month_value: str, records: Sequence[BillRecord]) -> BillMonthSummaryRead:
    """根据流水列表生成月汇总。"""
    income_cent = 0
    expense_cent = 0
    daily_map: dict[date, dict[str, int]] = defaultdict(lambda: {"income_cent": 0, "expense_cent": 0})
    category_map: dict[UUID, BillSummaryCategoryRead] = {}

    for record in records:
        local_day = to_local(record.occurred_at).date()

        if record.type == BillRecordType.income:
            income_cent += record.amount_cent
            daily_map[local_day]["income_cent"] += record.amount_cent
        elif record.type == BillRecordType.expense:
            expense_cent += record.amount_cent
            daily_map[local_day]["expense_cent"] += record.amount_cent
        else:
            continue

        if record.category is None:
            continue

        current = category_map.get(record.category.id)
        if current is None:
            category_map[record.category.id] = BillSummaryCategoryRead(
                category_id=UUID(str(record.category.id)),
                type=record.category.type.value,
                name=record.category.name,
                color=record.category.color,
                amount_cent=record.amount_cent,
                record_count=1,
            )
            continue

        category_map[record.category.id] = BillSummaryCategoryRead(
            category_id=current.category_id,
            type=current.type,
            name=current.name,
            color=current.color,
            amount_cent=current.amount_cent + record.amount_cent,
            record_count=current.record_count + 1,
        )

    daily_totals = [
        BillSummaryDailyTotalRead(
            date=day,
            income_cent=value["income_cent"],
            expense_cent=value["expense_cent"],
        )
        for day, value in sorted(daily_map.items())
    ]
    category_totals = sorted(
        category_map.values(),
        key=lambda item: (-item.amount_cent, item.name),
    )

    return BillMonthSummaryRead(
        month=month_value,
        income_cent=income_cent,
        expense_cent=expense_cent,
        net_cent=income_cent - expense_cent,
        record_count=len(records),
        daily_totals=daily_totals,
        category_totals=category_totals,
    )


def 解析模板发生时间(month_value: str, day_of_month: int) -> datetime:
    """根据月份和值班日生成固定账单的发生时间。"""
    year_str, month_str = month_value.split("-")
    year = int(year_str)
    month = int(month_str)
    last_day = calendar.monthrange(year, month)[1]
    actual_day = min(day_of_month, last_day)
    current_local_timezone = local_timezone()
    return datetime(year, month, actual_day, 9, 0, tzinfo=current_local_timezone).astimezone(timezone.utc)


def 构建默认账户值(user_id: UUID, *, now: datetime | None = None) -> list[dict[str, object]]:
    """构造默认账单账户插入数据。"""
    current_time = now or utcnow()
    return [
        {
            "id": generate_uuid7(),
            "user_id": user_id,
            "name": item["name"],
            "type": item["type"],
            "initial_balance_cent": item["initial_balance_cent"],
            "note": item["note"],
            "created_at": current_time,
            "updated_at": current_time,
        }
        for item in 默认账户列表
    ]


def 构建默认分类值(user_id: UUID, *, now: datetime | None = None) -> list[dict[str, object]]:
    """构造默认账单分类插入数据。"""
    current_time = now or utcnow()
    return [
        {
            "id": generate_uuid7(),
            "user_id": user_id,
            "type": item["type"],
            "name": item["name"],
            "color": item["color"],
            "icon": item["icon"],
            "sort_order": item["sort_order"],
            "created_at": current_time,
            "updated_at": current_time,
        }
        for item in 默认分类列表
    ]


async def 确保默认账单设置(db: AsyncSession, user: 用户) -> None:
    """确保当前用户已有默认账单账户和分类。"""
    await db.execute(
        pg_insert(BillAccount)
        .values(构建默认账户值(user.id))
        .on_conflict_do_nothing(constraint="uq_bill_accounts_user_id_name")
    )
    await db.execute(
        pg_insert(BillCategory)
        .values(构建默认分类值(user.id))
        .on_conflict_do_nothing(constraint="uq_bill_categories_user_id_type_name")
    )


async def 获取账户记录差值(db: AsyncSession, user: 用户) -> dict[UUID, int]:
    """查询当前用户所有账户的流水增量。"""
    result = await db.execute(select(BillRecord).where(BillRecord.user_id == user.id))
    records = result.scalars().all()
    return 计算账户记录差值(records)


async def 获取账单账户或404(db: AsyncSession, user: 用户, account_id: UUID | str) -> BillAccount:
    """获取当前用户的账单账户。"""
    result = await db.execute(
        select(BillAccount).where(
            BillAccount.id == account_id,
            BillAccount.user_id == user.id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="账单账户不存在")
    return account


async def 获取账单分类或404(db: AsyncSession, user: 用户, category_id: UUID | str) -> BillCategory:
    """获取当前用户的账单分类。"""
    result = await db.execute(
        select(BillCategory).where(
            BillCategory.id == category_id,
            BillCategory.user_id == user.id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="账单分类不存在")
    return category


async def 获取账单记录或404(db: AsyncSession, user: 用户, record_id: UUID | str) -> BillRecord:
    """获取当前用户的账单流水。"""
    result = await db.execute(
        账单记录查询().where(
            BillRecord.id == record_id,
            BillRecord.user_id == user.id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="账单流水不存在")
    return record


async def 获取账单模板或404(db: AsyncSession, user: 用户, template_id: UUID | str) -> BillTemplate:
    """获取当前用户的固定账单模板。"""
    result = await db.execute(
        账单模板查询().where(
            BillTemplate.id == template_id,
            BillTemplate.user_id == user.id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="固定账单模板不存在")
    return template


async def 确保账户名唯一(
    db: AsyncSession,
    *,
    user_id: UUID,
    name: str,
    exclude_id: UUID | None = None,
) -> None:
    """确保账户名称在当前用户下唯一。"""
    query = select(BillAccount.id).where(
        BillAccount.user_id == user_id,
        BillAccount.name == name,
    )
    if exclude_id is not None:
        query = query.where(BillAccount.id != exclude_id)
    exists = (await db.execute(query.limit(1))).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=400, detail="账户名称已存在")


async def 确保分类名唯一(
    db: AsyncSession,
    *,
    user_id: UUID,
    category_type: BillCategoryType,
    name: str,
    exclude_id: UUID | None = None,
) -> None:
    """确保分类名称在当前用户和分类类型下唯一。"""
    query = select(BillCategory.id).where(
        BillCategory.user_id == user_id,
        BillCategory.type == category_type,
        BillCategory.name == name,
    )
    if exclude_id is not None:
        query = query.where(BillCategory.id != exclude_id)
    exists = (await db.execute(query.limit(1))).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=400, detail="分类名称已存在")


async def 解析记录载荷依赖(
    db: AsyncSession,
    user: 用户,
    *,
    record_type: BillRecordType,
    account_id: UUID,
    target_account_id: UUID | None,
    category_id: UUID | None,
) -> tuple[BillAccount, BillAccount | None, BillCategory | None]:
    """解析流水所依赖的账户和分类。"""
    account = await 获取账单账户或404(db, user, account_id)
    target_account = None
    category = None

    if target_account_id is not None:
        target_account = await 获取账单账户或404(db, user, target_account_id)

    if category_id is not None:
        category = await 获取账单分类或404(db, user, category_id)

    if record_type == BillRecordType.transfer:
        if target_account is None:
            raise HTTPException(status_code=422, detail="转账记录必须选择转入账户")
        if category is not None:
            raise HTTPException(status_code=422, detail="转账记录不能选择分类")
    else:
        if target_account is not None:
            raise HTTPException(status_code=422, detail="收入或支出记录不能选择转入账户")
        if category is None:
            raise HTTPException(status_code=422, detail="收入或支出记录必须选择分类")
        if category.type.value != record_type.value:
            raise HTTPException(status_code=422, detail="所选分类与账单类型不匹配")

    if target_account is not None and target_account.id == account.id:
        raise HTTPException(status_code=422, detail="转出账户和转入账户不能相同")

    return account, target_account, category
