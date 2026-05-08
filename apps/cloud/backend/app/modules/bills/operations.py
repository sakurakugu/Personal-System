"""账单增删改操作。"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.bills.common import (
    构建账户读取,
    构建分类读取,
    构建记录读取,
    构建模板读取,
    确保默认账单设置,
    确保账户名唯一,
    确保分类名唯一,
    获取账户记录差值,
    获取账单账户或404,
    获取账单分类或404,
    获取账单记录或404,
    获取账单模板或404,
    解析账户类型,
    解析分类类型,
    解析记录类型,
    解析记录载荷依赖,
)
from app.modules.bills.models import BillAccount, BillCategory, BillRecord, BillTemplate
from app.modules.bills.schemas import (
    BillAccountCreate,
    BillAccountRead,
    BillAccountUpdate,
    BillCategoryCreate,
    BillCategoryRead,
    BillCategoryUpdate,
    BillRecordCreate,
    BillRecordRead,
    BillRecordUpdate,
    BillTemplateCreate,
    BillTemplateRead,
    BillTemplateUpdate,
)


async def create_bill_account(db: AsyncSession, user: User, body: BillAccountCreate) -> BillAccountRead:
    """创建账单账户。"""
    await 确保默认账单设置(db, user)
    await 确保账户名唯一(db, user_id=user.id, name=body.name)
    account = BillAccount(
        user_id=user.id,
        name=body.name,
        type=解析账户类型(body.type),
        initial_balance_cent=body.initial_balance_cent,
        note=body.note,
    )
    db.add(account)
    await db.flush()
    return 构建账户读取(account, current_balance_cent=account.initial_balance_cent)


async def update_bill_account(
    db: AsyncSession,
    user: User,
    account_id: UUID | str,
    body: BillAccountUpdate,
) -> BillAccountRead:
    """更新账单账户。"""
    account = await 获取账单账户或404(db, user, account_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        if data["name"] is None:
            raise HTTPException(status_code=422, detail="账户名称不能为空")
        await 确保账户名唯一(db, user_id=user.id, name=data["name"], exclude_id=account.id)
        account.name = data["name"]
    if "type" in data and data["type"] is not None:
        account.type = 解析账户类型(data["type"])
    if "initial_balance_cent" in data and data["initial_balance_cent"] is not None:
        account.initial_balance_cent = data["initial_balance_cent"]
    if "note" in data:
        account.note = data["note"]

    await db.flush()
    delta_map = await 获取账户记录差值(db, user)
    return 构建账户读取(
        account,
        current_balance_cent=account.initial_balance_cent + delta_map.get(account.id, 0),
    )


async def delete_bill_account(db: AsyncSession, user: User, account_id: UUID | str) -> None:
    """删除账单账户。"""
    account = await 获取账单账户或404(db, user, account_id)
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


async def 创建账单分类(db: AsyncSession, user: User, body: BillCategoryCreate) -> BillCategoryRead:
    """创建账单分类。"""
    await 确保默认账单设置(db, user)
    category_type = 解析分类类型(body.type)
    await 确保分类名唯一(db, user_id=user.id, category_type=category_type, name=body.name)
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
    return 构建分类读取(category)


async def 更新账单分类(
    db: AsyncSession,
    user: User,
    category_id: UUID | str,
    body: BillCategoryUpdate,
) -> BillCategoryRead:
    """更新账单分类。"""
    category = await 获取账单分类或404(db, user, category_id)
    data = body.model_dump(exclude_unset=True)
    next_type = category.type
    next_name = category.name

    if "type" in data and data["type"] is not None:
        next_type = 解析分类类型(data["type"])
    if "name" in data:
        if data["name"] is None:
            raise HTTPException(status_code=422, detail="分类名称不能为空")
        next_name = data["name"]

    if next_type != category.type or next_name != category.name:
        await 确保分类名唯一(
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
    return 构建分类读取(category)


async def 删除账单分类(db: AsyncSession, user: User, category_id: UUID | str) -> None:
    """删除账单分类。"""
    category = await 获取账单分类或404(db, user, category_id)
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


async def 创建账单模板(db: AsyncSession, user: User, body: BillTemplateCreate) -> BillTemplateRead:
    """创建固定账单模板。"""
    await 确保默认账单设置(db, user)
    template_type = 解析记录类型(body.type)
    await 解析记录载荷依赖(
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
    saved = await 获取账单模板或404(db, user, template.id)
    return 构建模板读取(saved)


async def 更新账单模板(
    db: AsyncSession,
    user: User,
    template_id: UUID | str,
    body: BillTemplateUpdate,
) -> BillTemplateRead:
    """更新固定账单模板。"""
    template = await 获取账单模板或404(db, user, template_id)
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

    template_type = 解析记录类型(template_type_value)
    await 解析记录载荷依赖(
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
    saved = await 获取账单模板或404(db, user, template.id)
    return 构建模板读取(saved)


async def 删除账单模板(db: AsyncSession, user: User, template_id: UUID | str) -> None:
    """删除固定账单模板。"""
    template = await 获取账单模板或404(db, user, template_id)
    await db.delete(template)


async def create_bill_record(db: AsyncSession, user: User, body: BillRecordCreate) -> BillRecordRead:
    """创建账单流水。"""
    await 确保默认账单设置(db, user)
    record_type = 解析记录类型(body.type)
    await 解析记录载荷依赖(
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
    saved = await 获取账单记录或404(db, user, record.id)
    return 构建记录读取(saved)


async def update_bill_record(
    db: AsyncSession,
    user: User,
    record_id: UUID | str,
    body: BillRecordUpdate,
) -> BillRecordRead:
    """更新账单流水。"""
    record = await 获取账单记录或404(db, user, record_id)
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

    record_type = 解析记录类型(record_type_value)
    await 解析记录载荷依赖(
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
    saved = await 获取账单记录或404(db, user, record.id)
    return 构建记录读取(saved)


async def delete_bill_record(db: AsyncSession, user: User, record_id: UUID | str) -> None:
    """删除账单流水。"""
    record = await 获取账单记录或404(db, user, record_id)
    await db.delete(record)
