"""账单领域服务。"""

from __future__ import annotations

import calendar
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bill import BillAccount, BillAccountType, BillCategory, BillCategoryType, BillRecord, BillRecordType, BillTemplate
from app.models.user import User
from app.schemas.bill import (
    BillAccountCreate,
    BillAccountRead,
    BillAccountSimpleRead,
    BillAccountUpdate,
    BillCategoryCreate,
    BillCategoryRead,
    BillCategorySimpleRead,
    BillCategoryUpdate,
    BillMonthSummaryRead,
    BillRecordCreate,
    BillRecordRead,
    BillRecordUpdate,
    BillTemplateCreate,
    BillTemplateGenerateResultRead,
    BillTemplateRead,
    BillTemplateUpdate,
    BillSummaryCategoryRead,
    BillSummaryDailyTotalRead,
)
from app.schemas.shared import PaginatedResponse
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


def _utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def _local_timezone():
    """返回系统当前本地时区。"""
    return datetime.now().astimezone().tzinfo or timezone.utc


def _to_local(dt: datetime) -> datetime:
    """将时间统一转换为本地时区。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_local_timezone())


def _current_month_value() -> str:
    """返回当前本地月份字符串。"""
    return _to_local(_utcnow()).strftime("%Y-%m")


def _parse_month_value(value: str | None) -> tuple[str, datetime, datetime]:
    """解析月份参数并返回对应的 UTC 区间。"""
    month_value = (value or _current_month_value()).strip()
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

    local_tz = _local_timezone()
    start_local = datetime(year, month, 1, tzinfo=local_tz)
    if month == 12:
        next_local = datetime(year + 1, 1, 1, tzinfo=local_tz)
    else:
        next_local = datetime(year, month + 1, 1, tzinfo=local_tz)

    return month_value, start_local.astimezone(timezone.utc), next_local.astimezone(timezone.utc)


def _parse_account_type(value: str) -> BillAccountType:
    """解析账户类型。"""
    try:
        return BillAccountType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的账户类型") from exc


def _parse_category_type(value: str) -> BillCategoryType:
    """解析分类类型。"""
    try:
        return BillCategoryType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的分类类型") from exc


def _parse_record_type(value: str) -> BillRecordType:
    """解析流水类型。"""
    try:
        return BillRecordType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的流水类型") from exc


def _build_account_simple(account: BillAccount) -> BillAccountSimpleRead:
    """构建账户简要响应。"""
    return BillAccountSimpleRead(
        id=UUID(str(account.id)),
        name=account.name,
        type=account.type.value,
    )


def _build_account_read(account: BillAccount, *, current_balance_cent: int) -> BillAccountRead:
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


def _build_category_simple(category: BillCategory) -> BillCategorySimpleRead:
    """构建分类简要响应。"""
    return BillCategorySimpleRead(
        id=UUID(str(category.id)),
        type=category.type.value,
        name=category.name,
        color=category.color,
        icon=category.icon,
    )


def _build_category_read(category: BillCategory) -> BillCategoryRead:
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


def _bill_record_query():
    """构建账单流水详情查询。"""
    return select(BillRecord).options(
        selectinload(BillRecord.account),
        selectinload(BillRecord.target_account),
        selectinload(BillRecord.category),
        selectinload(BillRecord.template),
    )


def _bill_template_query():
    """构建固定账单模板详情查询。"""
    return select(BillTemplate).options(
        selectinload(BillTemplate.account),
        selectinload(BillTemplate.target_account),
        selectinload(BillTemplate.category),
    )


def _build_record_read(record: BillRecord) -> BillRecordRead:
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
        account=_build_account_simple(record.account),
        target_account=_build_account_simple(record.target_account) if record.target_account is not None else None,
        category=_build_category_simple(record.category) if record.category is not None else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _build_template_read(template: BillTemplate) -> BillTemplateRead:
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
        account=_build_account_simple(template.account),
        target_account=_build_account_simple(template.target_account) if template.target_account is not None else None,
        category=_build_category_simple(template.category) if template.category is not None else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _calculate_account_record_deltas(records: Sequence[BillRecord]) -> dict[UUID, int]:
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


def _build_month_summary(month_value: str, records: Sequence[BillRecord]) -> BillMonthSummaryRead:
    """根据流水列表生成月汇总。"""
    income_cent = 0
    expense_cent = 0
    daily_map: dict[date, dict[str, int]] = defaultdict(lambda: {"income_cent": 0, "expense_cent": 0})
    category_map: dict[UUID, BillSummaryCategoryRead] = {}

    for record in records:
        local_day = _to_local(record.occurred_at).date()

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


def _resolve_template_occurred_at(month_value: str, day_of_month: int) -> datetime:
    """根据月份和值班日生成固定账单的发生时间。"""
    year_str, month_str = month_value.split("-")
    year = int(year_str)
    month = int(month_str)
    last_day = calendar.monthrange(year, month)[1]
    actual_day = min(day_of_month, last_day)
    local_tz = _local_timezone()
    return datetime(year, month, actual_day, 9, 0, tzinfo=local_tz).astimezone(timezone.utc)


def _build_default_account_values(user_id: UUID, *, now: datetime | None = None) -> list[dict[str, object]]:
    """构造默认账单账户插入数据。"""
    current_time = now or _utcnow()
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


def _build_default_category_values(user_id: UUID, *, now: datetime | None = None) -> list[dict[str, object]]:
    """构造默认账单分类插入数据。"""
    current_time = now or _utcnow()
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


async def ensure_default_bill_setup(db: AsyncSession, user: User) -> None:
    """确保当前用户已有默认账单账户和分类。"""
    await db.execute(
        pg_insert(BillAccount)
        .values(_build_default_account_values(user.id))
        .on_conflict_do_nothing(constraint="uq_bill_accounts_user_id_name")
    )
    await db.execute(
        pg_insert(BillCategory)
        .values(_build_default_category_values(user.id))
        .on_conflict_do_nothing(constraint="uq_bill_categories_user_id_type_name")
    )


async def _get_account_record_deltas(db: AsyncSession, user: User) -> dict[UUID, int]:
    """查询当前用户所有账户的流水增量。"""
    result = await db.execute(select(BillRecord).where(BillRecord.user_id == user.id))
    records = result.scalars().all()
    return _calculate_account_record_deltas(records)


async def get_bill_account_or_404(db: AsyncSession, user: User, account_id: UUID | str) -> BillAccount:
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


async def get_bill_category_or_404(db: AsyncSession, user: User, category_id: UUID | str) -> BillCategory:
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


async def get_bill_record_or_404(db: AsyncSession, user: User, record_id: UUID | str) -> BillRecord:
    """获取当前用户的账单流水。"""
    result = await db.execute(
        _bill_record_query().where(
            BillRecord.id == record_id,
            BillRecord.user_id == user.id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="账单流水不存在")
    return record


async def get_bill_template_or_404(db: AsyncSession, user: User, template_id: UUID | str) -> BillTemplate:
    """获取当前用户的固定账单模板。"""
    result = await db.execute(
        _bill_template_query().where(
            BillTemplate.id == template_id,
            BillTemplate.user_id == user.id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="固定账单模板不存在")
    return template


async def _ensure_unique_account_name(
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


async def _ensure_unique_category_name(
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


async def list_bill_accounts(db: AsyncSession, user: User) -> list[BillAccountRead]:
    """获取当前用户的账单账户列表。"""
    await ensure_default_bill_setup(db, user)
    result = await db.execute(
        select(BillAccount)
        .where(BillAccount.user_id == user.id)
        .order_by(BillAccount.created_at.asc())
    )
    accounts = result.scalars().all()
    delta_map = await _get_account_record_deltas(db, user)
    return [
        _build_account_read(
            account,
            current_balance_cent=account.initial_balance_cent + delta_map.get(account.id, 0),
        )
        for account in accounts
    ]


async def create_bill_account(db: AsyncSession, user: User, body: BillAccountCreate) -> BillAccountRead:
    """创建账单账户。"""
    await ensure_default_bill_setup(db, user)
    await _ensure_unique_account_name(db, user_id=user.id, name=body.name)
    account = BillAccount(
        user_id=user.id,
        name=body.name,
        type=_parse_account_type(body.type),
        initial_balance_cent=body.initial_balance_cent,
        note=body.note,
    )
    db.add(account)
    await db.flush()
    return _build_account_read(account, current_balance_cent=account.initial_balance_cent)


async def update_bill_account(
    db: AsyncSession,
    user: User,
    account_id: UUID | str,
    body: BillAccountUpdate,
) -> BillAccountRead:
    """更新账单账户。"""
    account = await get_bill_account_or_404(db, user, account_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        if data["name"] is None:
            raise HTTPException(status_code=422, detail="账户名称不能为空")
        await _ensure_unique_account_name(db, user_id=user.id, name=data["name"], exclude_id=account.id)
        account.name = data["name"]
    if "type" in data and data["type"] is not None:
        account.type = _parse_account_type(data["type"])
    if "initial_balance_cent" in data and data["initial_balance_cent"] is not None:
        account.initial_balance_cent = data["initial_balance_cent"]
    if "note" in data:
        account.note = data["note"]

    await db.flush()
    delta_map = await _get_account_record_deltas(db, user)
    return _build_account_read(
        account,
        current_balance_cent=account.initial_balance_cent + delta_map.get(account.id, 0),
    )


async def delete_bill_account(db: AsyncSession, user: User, account_id: UUID | str) -> None:
    """删除账单账户。"""
    account = await get_bill_account_or_404(db, user, account_id)
    related_record = (
        await db.execute(
            select(BillRecord.id)
            .where(
                BillRecord.user_id == user.id,
                or_(
                    BillRecord.account_id == account.id,
                    BillRecord.target_account_id == account.id,
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if related_record is not None:
        raise HTTPException(status_code=400, detail="该账户已有关联账单，不能删除")
    related_template = (
        await db.execute(
            select(BillTemplate.id)
            .where(
                BillTemplate.user_id == user.id,
                or_(
                    BillTemplate.account_id == account.id,
                    BillTemplate.target_account_id == account.id,
                ),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if related_template is not None:
        raise HTTPException(status_code=400, detail="该账户已有关联固定账单模板，不能删除")
    await db.delete(account)


async def list_bill_categories(db: AsyncSession, user: User) -> list[BillCategoryRead]:
    """获取当前用户的账单分类列表。"""
    await ensure_default_bill_setup(db, user)
    result = await db.execute(
        select(BillCategory)
        .where(BillCategory.user_id == user.id)
        .order_by(BillCategory.type.asc(), BillCategory.sort_order.asc(), BillCategory.created_at.asc())
    )
    categories = result.scalars().all()
    return [_build_category_read(category) for category in categories]


async def create_bill_category(db: AsyncSession, user: User, body: BillCategoryCreate) -> BillCategoryRead:
    """创建账单分类。"""
    await ensure_default_bill_setup(db, user)
    category_type = _parse_category_type(body.type)
    await _ensure_unique_category_name(db, user_id=user.id, category_type=category_type, name=body.name)
    category = BillCategory(
        user_id=user.id,
        type=category_type,
        name=body.name,
        color=body.color,
        icon=body.icon,
        sort_order=body.sort_order,
    )
    db.add(category)
    await db.flush()
    return _build_category_read(category)


async def update_bill_category(
    db: AsyncSession,
    user: User,
    category_id: UUID | str,
    body: BillCategoryUpdate,
) -> BillCategoryRead:
    """更新账单分类。"""
    category = await get_bill_category_or_404(db, user, category_id)
    data = body.model_dump(exclude_unset=True)
    next_type = category.type
    next_name = category.name

    if "type" in data and data["type"] is not None:
        next_type = _parse_category_type(data["type"])
    if "name" in data:
        if data["name"] is None:
            raise HTTPException(status_code=422, detail="分类名称不能为空")
        next_name = data["name"]

    if next_type != category.type or next_name != category.name:
        await _ensure_unique_category_name(
            db,
            user_id=user.id,
            category_type=next_type,
            name=next_name,
            exclude_id=category.id,
        )

    category.type = next_type
    category.name = next_name
    if "color" in data and data["color"] is not None:
        category.color = data["color"]
    if "icon" in data and data["icon"] is not None:
        category.icon = data["icon"]
    if "sort_order" in data and data["sort_order"] is not None:
        category.sort_order = data["sort_order"]

    await db.flush()
    return _build_category_read(category)


async def delete_bill_category(db: AsyncSession, user: User, category_id: UUID | str) -> None:
    """删除账单分类。"""
    category = await get_bill_category_or_404(db, user, category_id)
    related_record = (
        await db.execute(
            select(BillRecord.id)
            .where(
                BillRecord.user_id == user.id,
                BillRecord.category_id == category.id,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if related_record is not None:
        raise HTTPException(status_code=400, detail="该分类已有关联账单，不能删除")
    related_template = (
        await db.execute(
            select(BillTemplate.id)
            .where(
                BillTemplate.user_id == user.id,
                BillTemplate.category_id == category.id,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if related_template is not None:
        raise HTTPException(status_code=400, detail="该分类已有关联固定账单模板，不能删除")
    await db.delete(category)


async def list_bill_templates(db: AsyncSession, user: User) -> list[BillTemplateRead]:
    """获取当前用户的固定账单模板列表。"""
    await ensure_default_bill_setup(db, user)
    result = await db.execute(
        _bill_template_query()
        .where(BillTemplate.user_id == user.id)
        .order_by(BillTemplate.is_active.desc(), BillTemplate.day_of_month.asc(), BillTemplate.created_at.asc())
    )
    templates = result.scalars().unique().all()
    return [_build_template_read(template) for template in templates]


async def create_bill_template(db: AsyncSession, user: User, body: BillTemplateCreate) -> BillTemplateRead:
    """创建固定账单模板。"""
    await ensure_default_bill_setup(db, user)
    template_type = _parse_record_type(body.type)
    await _resolve_record_payload_dependencies(
        db,
        user,
        record_type=template_type,
        account_id=body.account_id,
        target_account_id=body.target_account_id,
        category_id=body.category_id,
    )

    template = BillTemplate(
        user_id=user.id,
        title=body.title,
        type=template_type,
        account_id=body.account_id,
        target_account_id=body.target_account_id,
        category_id=body.category_id,
        amount_cent=body.amount_cent,
        merchant=body.merchant,
        note=body.note,
        day_of_month=body.day_of_month,
        is_active=body.is_active,
    )
    db.add(template)
    await db.flush()
    saved = await get_bill_template_or_404(db, user, template.id)
    return _build_template_read(saved)


async def update_bill_template(
    db: AsyncSession,
    user: User,
    template_id: UUID | str,
    body: BillTemplateUpdate,
) -> BillTemplateRead:
    """更新固定账单模板。"""
    template = await get_bill_template_or_404(db, user, template_id)
    data = body.model_dump(exclude_unset=True)

    if "title" in data and data["title"] is None:
        raise HTTPException(status_code=422, detail="模板标题不能为空")
    if "type" in data and data["type"] is None:
        raise HTTPException(status_code=422, detail="模板类型不能为空")
    if "account_id" in data and data["account_id"] is None:
        raise HTTPException(status_code=422, detail="账户不能为空")
    if "amount_cent" in data and data["amount_cent"] is None:
        raise HTTPException(status_code=422, detail="金额不能为空")
    if "day_of_month" in data and data["day_of_month"] is None:
        raise HTTPException(status_code=422, detail="出账日不能为空")

    template_type_value = data.get("type", template.type.value)
    account_id = data.get("account_id", template.account_id)
    target_account_id = data.get("target_account_id", template.target_account_id)
    category_id = data.get("category_id", template.category_id)
    amount_cent = data.get("amount_cent", template.amount_cent)
    merchant = data.get("merchant", template.merchant)
    note = data.get("note", template.note)
    day_of_month = data.get("day_of_month", template.day_of_month)
    title = data.get("title", template.title)
    is_active = data.get("is_active", template.is_active)

    template_type = _parse_record_type(template_type_value)
    await _resolve_record_payload_dependencies(
        db,
        user,
        record_type=template_type,
        account_id=account_id,
        target_account_id=target_account_id,
        category_id=category_id,
    )

    template.title = title
    template.type = template_type
    template.account_id = account_id
    template.target_account_id = target_account_id
    template.category_id = category_id
    template.amount_cent = amount_cent
    template.merchant = merchant
    template.note = note
    template.day_of_month = day_of_month
    template.is_active = is_active
    await db.flush()
    saved = await get_bill_template_or_404(db, user, template.id)
    return _build_template_read(saved)


async def delete_bill_template(db: AsyncSession, user: User, template_id: UUID | str) -> None:
    """删除固定账单模板。"""
    template = await get_bill_template_or_404(db, user, template_id)
    await db.delete(template)


async def generate_bill_templates_for_month(
    db: AsyncSession,
    user: User,
    *,
    month: str | None,
) -> BillTemplateGenerateResultRead:
    """按月生成固定账单流水。"""
    await ensure_default_bill_setup(db, user)
    month_value, _, _ = _parse_month_value(month)
    result = await db.execute(
        _bill_template_query()
        .where(
            BillTemplate.user_id == user.id,
            BillTemplate.is_active.is_(True),
        )
        .order_by(BillTemplate.day_of_month.asc(), BillTemplate.created_at.asc())
    )
    templates = result.scalars().unique().all()
    if not templates:
        return BillTemplateGenerateResultRead(month=month_value, created_count=0, skipped_count=0)

    template_ids = [template.id for template in templates]
    existing_result = await db.execute(
        select(BillRecord.template_id).where(
            BillRecord.user_id == user.id,
            BillRecord.template_id.in_(template_ids),
            BillRecord.template_month == month_value,
        )
    )
    existing_template_ids = {template_id for template_id in existing_result.scalars().all() if template_id is not None}

    created_count = 0
    skipped_count = 0
    for template in templates:
        if template.id in existing_template_ids:
            skipped_count += 1
            continue

        db.add(
            BillRecord(
                user_id=user.id,
                type=template.type,
                account_id=template.account_id,
                target_account_id=template.target_account_id,
                category_id=template.category_id,
                template_id=template.id,
                template_month=month_value,
                amount_cent=template.amount_cent,
                merchant=template.merchant,
                note=template.note,
                occurred_at=_resolve_template_occurred_at(month_value, template.day_of_month),
            )
        )
        created_count += 1

    if created_count > 0:
        await db.flush()

    return BillTemplateGenerateResultRead(
        month=month_value,
        created_count=created_count,
        skipped_count=skipped_count,
    )


async def _resolve_record_payload_dependencies(
    db: AsyncSession,
    user: User,
    *,
    record_type: BillRecordType,
    account_id: UUID,
    target_account_id: UUID | None,
    category_id: UUID | None,
) -> tuple[BillAccount, BillAccount | None, BillCategory | None]:
    """解析流水所依赖的账户和分类。"""
    account = await get_bill_account_or_404(db, user, account_id)
    target_account = None
    category = None

    if target_account_id is not None:
        target_account = await get_bill_account_or_404(db, user, target_account_id)

    if category_id is not None:
        category = await get_bill_category_or_404(db, user, category_id)

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


async def list_bill_records(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
    month: str | None,
    record_type: str | None,
    account_id: UUID | None,
    category_id: UUID | None,
    keyword: str | None,
) -> PaginatedResponse:
    """分页获取当前用户的账单流水。"""
    await ensure_default_bill_setup(db, user)
    await generate_bill_templates_for_month(db, user, month=month)
    _, start_at, end_at = _parse_month_value(month)
    query = _bill_record_query().where(
        BillRecord.user_id == user.id,
        BillRecord.occurred_at >= start_at,
        BillRecord.occurred_at < end_at,
    )

    if record_type:
        query = query.where(BillRecord.type == _parse_record_type(record_type))
    if account_id is not None:
        query = query.where(or_(BillRecord.account_id == account_id, BillRecord.target_account_id == account_id))
    if category_id is not None:
        query = query.where(BillRecord.category_id == category_id)
    if keyword:
        normalized_keyword = keyword.strip()
        if normalized_keyword:
            like_keyword = f"%{normalized_keyword}%"
            query = query.where(
                or_(
                    BillRecord.merchant.ilike(like_keyword),
                    BillRecord.note.ilike(like_keyword),
                )
            )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(BillRecord.occurred_at.desc(), BillRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().unique().all()
    return PaginatedResponse(
        items=[_build_record_read(record) for record in records],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def create_bill_record(db: AsyncSession, user: User, body: BillRecordCreate) -> BillRecordRead:
    """创建账单流水。"""
    await ensure_default_bill_setup(db, user)
    record_type = _parse_record_type(body.type)
    await _resolve_record_payload_dependencies(
        db,
        user,
        record_type=record_type,
        account_id=body.account_id,
        target_account_id=body.target_account_id,
        category_id=body.category_id,
    )

    record = BillRecord(
        user_id=user.id,
        type=record_type,
        account_id=body.account_id,
        target_account_id=body.target_account_id,
        category_id=body.category_id,
        amount_cent=body.amount_cent,
        merchant=body.merchant,
        note=body.note,
        occurred_at=body.occurred_at,
    )
    db.add(record)
    await db.flush()
    saved = await get_bill_record_or_404(db, user, record.id)
    return _build_record_read(saved)


async def update_bill_record(
    db: AsyncSession,
    user: User,
    record_id: UUID | str,
    body: BillRecordUpdate,
) -> BillRecordRead:
    """更新账单流水。"""
    record = await get_bill_record_or_404(db, user, record_id)
    data = body.model_dump(exclude_unset=True)

    if "type" in data and data["type"] is None:
        raise HTTPException(status_code=422, detail="流水类型不能为空")
    if "account_id" in data and data["account_id"] is None:
        raise HTTPException(status_code=422, detail="账户不能为空")
    if "amount_cent" in data and data["amount_cent"] is None:
        raise HTTPException(status_code=422, detail="金额不能为空")
    if "occurred_at" in data and data["occurred_at"] is None:
        raise HTTPException(status_code=422, detail="记账时间不能为空")

    record_type_value = data.get("type", record.type.value)
    account_id = data.get("account_id", record.account_id)
    target_account_id = data.get("target_account_id", record.target_account_id)
    category_id = data.get("category_id", record.category_id)
    amount_cent = data.get("amount_cent", record.amount_cent)
    merchant = data.get("merchant", record.merchant)
    note = data.get("note", record.note)
    occurred_at = data.get("occurred_at", record.occurred_at)

    record_type = _parse_record_type(record_type_value)
    await _resolve_record_payload_dependencies(
        db,
        user,
        record_type=record_type,
        account_id=account_id,
        target_account_id=target_account_id,
        category_id=category_id,
    )

    record.type = record_type
    record.account_id = account_id
    record.target_account_id = target_account_id
    record.category_id = category_id
    record.amount_cent = amount_cent
    record.merchant = merchant
    record.note = note
    record.occurred_at = occurred_at

    await db.flush()
    saved = await get_bill_record_or_404(db, user, record.id)
    return _build_record_read(saved)


async def delete_bill_record(db: AsyncSession, user: User, record_id: UUID | str) -> None:
    """删除账单流水。"""
    record = await get_bill_record_or_404(db, user, record_id)
    await db.delete(record)


async def get_bill_month_summary(
    db: AsyncSession,
    user: User,
    *,
    month: str | None,
) -> BillMonthSummaryRead:
    """获取当前用户的账单月汇总。"""
    await ensure_default_bill_setup(db, user)
    await generate_bill_templates_for_month(db, user, month=month)
    month_value, start_at, end_at = _parse_month_value(month)
    result = await db.execute(
        _bill_record_query()
        .where(
            BillRecord.user_id == user.id,
            BillRecord.occurred_at >= start_at,
            BillRecord.occurred_at < end_at,
        )
        .order_by(BillRecord.occurred_at.asc(), BillRecord.created_at.asc())
    )
    records = result.scalars().unique().all()
    return _build_month_summary(month_value, records)
