"""账单查询与汇总。"""

from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.bills.common import (
    账单记录查询,
    账单模板查询,
    构建账户读取,
    构建分类读取,
    构建月度汇总,
    构建记录读取,
    构建模板读取,
    确保默认账单设置,
    获取账户记录差值,
    解析月份值,
    解析记录类型,
    解析模板发生时间,
)
from app.modules.bills.models import BillAccount, BillCategory, BillRecord, BillTemplate
from app.modules.bills.schemas import BillAccountRead, BillCategoryRead, BillMonthSummaryRead, BillTemplateGenerateResultRead, BillTemplateRead
from app.shared.kernel.pagination import PaginatedResponse


async def list_bill_accounts(db: AsyncSession, user: User) -> list[BillAccountRead]:
    """获取当前用户的账单账户列表。"""
    await 确保默认账单设置(db, user)
    result = await db.execute(
        select(BillAccount)
        .where(BillAccount.user_id == user.id)
        .order_by(BillAccount.created_at.asc())
    )
    accounts = result.scalars().all()
    delta_map = await 获取账户记录差值(db, user)
    return [
        构建账户读取(
            account,
            current_balance_cent=account.initial_balance_cent + delta_map.get(account.id, 0),
        )
        for account in accounts
    ]


async def 列出账单分类(db: AsyncSession, user: User) -> list[BillCategoryRead]:
    """获取当前用户的账单分类列表。"""
    await 确保默认账单设置(db, user)
    result = await db.execute(
        select(BillCategory)
        .where(BillCategory.user_id == user.id)
        .order_by(BillCategory.type.asc(), BillCategory.sort_order.asc(), BillCategory.created_at.asc())
    )
    categories = result.scalars().all()
    return [构建分类读取(category) for category in categories]


async def list_bill_templates(db: AsyncSession, user: User) -> list[BillTemplateRead]:
    """获取当前用户的固定账单模板列表。"""
    await 确保默认账单设置(db, user)
    result = await db.execute(
        账单模板查询()
        .where(BillTemplate.user_id == user.id)
        .order_by(BillTemplate.is_active.desc(), BillTemplate.day_of_month.asc(), BillTemplate.created_at.asc())
    )
    templates = result.scalars().unique().all()
    return [构建模板读取(template) for template in templates]


async def 为月份生成账单模板(
    db: AsyncSession,
    user: User,
    *,
    month: str | None,
) -> BillTemplateGenerateResultRead:
    """按月生成固定账单流水。"""
    await 确保默认账单设置(db, user)
    month_value, _, _ = 解析月份值(month)
    result = await db.execute(
        账单模板查询()
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
                occurred_at=解析模板发生时间(month_value, template.day_of_month),
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
    await 确保默认账单设置(db, user)
    await 为月份生成账单模板(db, user, month=month)
    _, start_at, end_at = 解析月份值(month)
    query = 账单记录查询().where(
        BillRecord.user_id == user.id,
        BillRecord.occurred_at >= start_at,
        BillRecord.occurred_at < end_at,
    )

    if record_type:
        query = query.where(BillRecord.type == 解析记录类型(record_type))
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
        items=[构建记录读取(record) for record in records],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def 获取账单月度汇总(
    db: AsyncSession,
    user: User,
    *,
    month: str | None,
) -> BillMonthSummaryRead:
    """获取当前用户的账单月汇总。"""
    await 确保默认账单设置(db, user)
    await 为月份生成账单模板(db, user, month=month)
    month_value, start_at, end_at = 解析月份值(month)
    result = await db.execute(
        账单记录查询()
        .where(
            BillRecord.user_id == user.id,
            BillRecord.occurred_at >= start_at,
            BillRecord.occurred_at < end_at,
        )
        .order_by(BillRecord.occurred_at.asc(), BillRecord.created_at.asc())
    )
    records = result.scalars().unique().all()
    return 构建月度汇总(month_value, records)
