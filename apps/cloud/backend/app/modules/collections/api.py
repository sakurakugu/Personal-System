"""收藏模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.collections.schemas import 收藏批量状态更新, 收藏转换结果, 收藏创建, 收藏信息, 收藏标签信息, 收藏更新
from app.modules.collections.service import (
    批量更新收藏状态 as 批量更新收藏状态_service,
    构建收藏读取,
    转换收藏为文章 as 转换收藏为文章_service,
    转换收藏为动态草稿 as 转换收藏为动态草稿_service,
    转换收藏为待办 as 转换收藏为待办_service,
    创建收藏 as 创建收藏_service,
    删除收藏 as 删除收藏_service,
    get_collection_or_404,
    列出收藏标签 as 列出收藏标签_service,
    列出收藏 as 列出收藏_service,
    恢复收藏 as 恢复收藏_service,
    更新收藏 as 更新收藏_service,
)
from app.shared.kernel.pagination import PaginatedResponse
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/tags", response_model=list[收藏标签信息])
async def 列出收藏标签(
    is_deleted: bool = Query(False, description="是否统计回收站标签"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏标签列表。"""
    return await 列出收藏标签_service(db, user, is_deleted=is_deleted)


@router.get("", response_model=PaginatedResponse)
async def 列出收藏(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    status: str | None = Query(default=None),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    is_deleted: bool = Query(False, description="是否显示已删除（回收站）"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏列表。"""
    return await 列出收藏_service(
        db,
        user,
        page=page,
        page_size=page_size,
        status=status,
        collection_type=type,
        tag=tag,
        keyword=keyword,
        is_deleted=is_deleted,
    )


@router.get("/{collection_id}", response_model=收藏信息)
async def get_collection(
    collection_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取单条收藏详情。"""
    collection = await get_collection_or_404(db, user, collection_id)
    return 构建收藏读取(collection)


@router.post("", response_model=收藏信息, status_code=status.HTTP_201_CREATED)
async def 创建收藏(
    body: 收藏创建,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建收藏。"""
    return await 创建收藏_service(db, user, body)


@router.patch("/{collection_id}", response_model=收藏信息)
async def 更新收藏(
    collection_id: str,
    body: 收藏更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新收藏。"""
    return await 更新收藏_service(db, user, collection_id, body)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除收藏(
    collection_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除收藏。"""
    await 删除收藏_service(db, user, collection_id, permanent=permanent)


@router.post("/{collection_id}/restore", response_model=收藏信息)
async def 恢复收藏(
    collection_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复收藏。"""
    return await 恢复收藏_service(db, user, collection_id)


@router.post("/batch/status")
async def 批量更新收藏状态(
    body: 收藏批量状态更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """批量更新收藏状态。"""
    count = await 批量更新收藏状态_service(db, user, body)
    return {"count": count}


@router.post("/{collection_id}/convert/article", response_model=收藏转换结果)
async def 转换收藏为文章(
    collection_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为文章草稿。"""
    return await 转换收藏为文章_service(db, user, collection_id)


@router.post("/{collection_id}/convert/moment-draft", response_model=收藏转换结果)
async def 转换收藏为动态草稿(
    collection_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为动态草稿。"""
    return await 转换收藏为动态草稿_service(db, user, collection_id)


@router.post("/{collection_id}/convert/todo", response_model=收藏转换结果)
async def 转换收藏为待办(
    collection_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为待办。"""
    return await 转换收藏为待办_service(db, user, collection_id)
