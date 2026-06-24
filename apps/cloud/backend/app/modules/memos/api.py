"""备忘录模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memos.schemas import 备忘录创建, 备忘录信息, 备忘录更新, 备忘录转换结果
from app.modules.memos.service import (
    删除备忘录 as 删除备忘录_service,
    列出备忘录 as 列出备忘录_service,
    创建备忘录 as 创建备忘录_service,
    构建备忘录读取,
    恢复备忘录 as 恢复备忘录_service,
    get_memo_or_404,
    转换备忘录为文章 as 转换备忘录为文章_service,
    转换备忘录为待办 as 转换备忘录为待办_service,
    转换备忘录为资料 as 转换备忘录为资料_service,
    更新备忘录 as 更新备忘录_service,
)
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db
from app.shared.kernel.pagination import PaginatedResponse

router = APIRouter(prefix="/memos", tags=["memos"])


@router.get("", response_model=PaginatedResponse)
async def 列出备忘录(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    is_deleted: bool = Query(False, description="是否显示已删除（回收站）"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的备忘录列表。"""
    return await 列出备忘录_service(
        db,
        user,
        page=page,
        page_size=page_size,
        status=status,
        source=source,
        keyword=keyword,
        is_deleted=is_deleted,
    )


@router.get("/{memo_id}", response_model=备忘录信息)
async def 获取备忘录(
    memo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取单条备忘录详情。"""
    memo = await get_memo_or_404(db, user, memo_id)
    return 构建备忘录读取(memo)


@router.post("", response_model=备忘录信息, status_code=status.HTTP_201_CREATED)
async def 创建备忘录(
    body: 备忘录创建,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建备忘录。"""
    return await 创建备忘录_service(db, user, body)


@router.patch("/{memo_id}", response_model=备忘录信息)
async def 更新备忘录(
    memo_id: str,
    body: 备忘录更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新备忘录。"""
    return await 更新备忘录_service(db, user, memo_id, body)


@router.delete("/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除备忘录(
    memo_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除备忘录。"""
    await 删除备忘录_service(db, user, memo_id, permanent=permanent)


@router.post("/{memo_id}/restore", response_model=备忘录信息)
async def 恢复备忘录(
    memo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复备忘录。"""
    return await 恢复备忘录_service(db, user, memo_id)


@router.post("/{memo_id}/convert/material", response_model=备忘录转换结果)
async def 转换备忘录为资料(
    memo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将备忘录转换为资料库资料。"""
    return await 转换备忘录为资料_service(db, user, memo_id)


@router.post("/{memo_id}/convert/article", response_model=备忘录转换结果)
async def 转换备忘录为文章(
    memo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将备忘录转换为文章草稿。"""
    return await 转换备忘录为文章_service(db, user, memo_id)


@router.post("/{memo_id}/convert/todo", response_model=备忘录转换结果)
async def 转换备忘录为待办(
    memo_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将备忘录转换为待办。"""
    return await 转换备忘录为待办_service(db, user, memo_id)
