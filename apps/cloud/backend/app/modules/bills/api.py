"""账单相关路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.bills.queries import (
    为月份生成账单模板,
    获取账单月度汇总,
    list_bill_accounts,
    列出账单分类,
    list_bill_records,
    list_bill_templates,
)
from app.modules.bills.operations import (
    create_bill_account,
    创建账单分类 as 创建账单分类操作,
    create_bill_record,
    创建账单模板 as 创建账单模板操作,
    delete_bill_account,
    删除账单分类,
    delete_bill_record,
    删除账单模板,
    update_bill_account,
    更新账单分类,
    update_bill_record,
    更新账单模板,
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
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("/accounts", response_model=list[BillAccountRead])
async def 获取账单账户列表(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的账单账户列表。"""
    return await list_bill_accounts(db, user)


@router.post("/accounts", response_model=BillAccountRead, status_code=status.HTTP_201_CREATED)
async def 创建账单账户(
    body: BillAccountCreate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建账单账户。"""
    return await create_bill_account(db, user, body)


@router.patch("/accounts/{account_id}", response_model=BillAccountRead)
async def patch_bill_account(
    account_id: UUID,
    body: BillAccountUpdate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新账单账户。"""
    return await update_bill_account(db, user, account_id, body)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_account(
    account_id: UUID,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除账单账户。"""
    await delete_bill_account(db, user, account_id)


@router.get("/categories", response_model=list[BillCategoryRead])
async def 获取账单分类列表(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的账单分类列表。"""
    return await 列出账单分类(db, user)


@router.post("/categories", response_model=BillCategoryRead, status_code=status.HTTP_201_CREATED)
async def 创建账单分类(
    body: BillCategoryCreate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建账单分类。"""
    return await 创建账单分类操作(db, user, body)


@router.patch("/categories/{category_id}", response_model=BillCategoryRead)
async def patch_bill_category(
    category_id: UUID,
    body: BillCategoryUpdate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新账单分类。"""
    return await 更新账单分类(db, user, category_id, body)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 移除账单分类(
    category_id: UUID,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除账单分类。"""
    await 删除账单分类(db, user, category_id)


@router.get("/templates", response_model=list[BillTemplateRead])
async def 获取账单模板列表(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的固定账单模板列表。"""
    return await list_bill_templates(db, user)


@router.post("/templates", response_model=BillTemplateRead, status_code=status.HTTP_201_CREATED)
async def 创建账单模板(
    body: BillTemplateCreate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建固定账单模板。"""
    return await 创建账单模板操作(db, user, body)


@router.patch("/templates/{template_id}", response_model=BillTemplateRead)
async def patch_bill_template(
    template_id: UUID,
    body: BillTemplateUpdate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新固定账单模板。"""
    return await 更新账单模板(db, user, template_id, body)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 移除账单模板(
    template_id: UUID,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除固定账单模板。"""
    await 删除账单模板(db, user, template_id)


@router.post("/templates/generate", response_model=BillTemplateGenerateResultRead)
async def 生成账单模板接口(
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """手动补齐指定月份的固定账单。"""
    return await 为月份生成账单模板(db, user, month=month)


@router.get("/records", response_model=PaginatedResponse)
async def 获取账单记录列表(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    record_type: str | None = Query(None, alias="type", description="流水类型：expense/income/transfer"),
    account_id: UUID | None = Query(None, description="账户 ID"),
    category_id: UUID | None = Query(None, description="分类 ID"),
    keyword: str | None = Query(None, description="商户或备注关键词"),
    user: 用户 = Depends(获取当前用户),
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
async def 创建账单记录(
    body: BillRecordCreate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建账单流水。"""
    return await create_bill_record(db, user, body)


@router.patch("/records/{record_id}", response_model=BillRecordRead)
async def patch_bill_record(
    record_id: UUID,
    body: BillRecordUpdate,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新账单流水。"""
    return await update_bill_record(db, user, record_id, body)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bill_record(
    record_id: UUID,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除账单流水。"""
    await delete_bill_record(db, user, record_id)


@router.get("/summary", response_model=BillMonthSummaryRead)
async def get_month_summary(
    month: str | None = Query(None, description="账单月份，格式 YYYY-MM"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取账单月汇总。"""
    return await 获取账单月度汇总(db, user, month=month)
