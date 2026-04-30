"""账单相关路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.bills.queries import (
    generate_bill_templates_for_month,
    get_bill_month_summary,
    list_bill_accounts,
    list_bill_categories,
    list_bill_records,
    list_bill_templates,
)
from app.modules.bills.operations import (
    create_bill_account,
    create_bill_category,
    create_bill_record,
    create_bill_template,
    delete_bill_account,
    delete_bill_category,
    delete_bill_record,
    delete_bill_template,
    update_bill_account,
    update_bill_category,
    update_bill_record,
    update_bill_template,
)
from app.modules.bills.schemas import (
    BillAccountCreate,
    BillAccountRead,
    BillAccountUpdate,
    BillCategoryCreate,
    BillCategoryRead,
    BillCategoryUpdate,
    BillMonthSummaryRead,
    BillRecordCreate,
    BillRecordRead,
    BillRecordUpdate,
    BillTemplateCreate,
    BillTemplateGenerateResultRead,
    BillTemplateRead,
    BillTemplateUpdate,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import get_current_user
from app.shared.db.session import get_db

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("/accounts", response_model=list[BillAccountRead])
async def get_bill_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的账单账户列表。"""
    return await list_bill_accounts(db, user)


@router.post("/accounts", response_model=BillAccountRead, status_code=status.HTTP_201_CREATED)
async def post_bill_account(
    body: BillAccountCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建账单账户。"""
    return await create_bill_account(db, user, body)


@router.patch("/accounts/{account_id}", response_model=BillAccountRead)
async def patch_bill_account(
    account_id: UUID,
    body: BillAccountUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账单账户。"""
    return await update_bill_account(db, user, account_id, body)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除账单账户。"""
    await delete_bill_account(db, user, account_id)


@router.get("/categories", response_model=list[BillCategoryRead])
async def get_bill_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的账单分类列表。"""
    return await list_bill_categories(db, user)


@router.post("/categories", response_model=BillCategoryRead, status_code=status.HTTP_201_CREATED)
async def post_bill_category(
    body: BillCategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建账单分类。"""
    return await create_bill_category(db, user, body)


@router.patch("/categories/{category_id}", response_model=BillCategoryRead)
async def patch_bill_category(
    category_id: UUID,
    body: BillCategoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账单分类。"""
    return await update_bill_category(db, user, category_id, body)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_category(
    category_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除账单分类。"""
    await delete_bill_category(db, user, category_id)


@router.get("/templates", response_model=list[BillTemplateRead])
async def get_bill_templates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的固定账单模板列表。"""
    return await list_bill_templates(db, user)


@router.post("/templates", response_model=BillTemplateRead, status_code=status.HTTP_201_CREATED)
async def post_bill_template(
    body: BillTemplateCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建固定账单模板。"""
    return await create_bill_template(db, user, body)


@router.patch("/templates/{template_id}", response_model=BillTemplateRead)
async def patch_bill_template(
    template_id: UUID,
    body: BillTemplateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新固定账单模板。"""
    return await update_bill_template(db, user, template_id, body)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_template(
    template_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除固定账单模板。"""
    await delete_bill_template(db, user, template_id)


@router.post("/templates/generate", response_model=BillTemplateGenerateResultRead)
async def post_generate_bill_templates(
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动补齐指定月份的固定账单。"""
    return await generate_bill_templates_for_month(db, user, month=month)


@router.get("/records", response_model=PaginatedResponse)
async def get_bill_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    record_type: str | None = Query(None, alias="type", description="流水类型：expense/income/transfer"),
    account_id: UUID | None = Query(None, description="账户 ID"),
    category_id: UUID | None = Query(None, description="分类 ID"),
    keyword: str | None = Query(None, description="商户或备注关键词"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """分页获取账单流水。"""
    return await list_bill_records(
        db,
        user,
        page=page,
        page_size=page_size,
        month=month,
        record_type=record_type,
        account_id=account_id,
        category_id=category_id,
        keyword=keyword,
    )


@router.post("/records", response_model=BillRecordRead, status_code=status.HTTP_201_CREATED)
async def post_bill_record(
    body: BillRecordCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建账单流水。"""
    return await create_bill_record(db, user, body)


@router.patch("/records/{record_id}", response_model=BillRecordRead)
async def patch_bill_record(
    record_id: UUID,
    body: BillRecordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新账单流水。"""
    return await update_bill_record(db, user, record_id, body)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_record(
    record_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除账单流水。"""
    await delete_bill_record(db, user, record_id)


@router.get("/summary", response_model=BillMonthSummaryRead)
async def get_month_summary(
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取账单月汇总。"""
    return await get_bill_month_summary(db, user, month=month)
