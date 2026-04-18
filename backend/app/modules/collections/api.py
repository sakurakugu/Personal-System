"""收藏模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.collections.schemas import CollectionBatchStatusUpdate, CollectionConvertResult, CollectionCreate, CollectionRead, CollectionTagRead, CollectionUpdate
from app.modules.collections.service import (
    batch_update_collection_status as batch_update_collection_status_service,
    build_collection_read,
    convert_collection_to_article as convert_collection_to_article_service,
    convert_collection_to_moment_draft as convert_collection_to_moment_draft_service,
    convert_collection_to_todo as convert_collection_to_todo_service,
    create_collection as create_collection_service,
    delete_collection as delete_collection_service,
    get_collection_or_404,
    list_collection_tags as list_collection_tags_service,
    list_collections as list_collections_service,
    restore_collection as restore_collection_service,
    update_collection as update_collection_service,
)
from app.schemas.shared import PaginatedResponse
from app.shared.auth.deps import get_current_user
from app.shared.db.session import get_db

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/tags", response_model=list[CollectionTagRead])
async def list_collection_tags(
    is_deleted: bool = Query(False, description="是否统计回收站标签"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏标签列表。"""
    return await list_collection_tags_service(db, user, is_deleted=is_deleted)


@router.get("", response_model=PaginatedResponse)
async def list_collections(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    status: str | None = Query(default=None),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    is_deleted: bool = Query(False, description="是否显示已删除（回收站）"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的收藏列表。"""
    return await list_collections_service(
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


@router.get("/{collection_id}", response_model=CollectionRead)
async def get_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单条收藏详情。"""
    collection = await get_collection_or_404(db, user, collection_id)
    return build_collection_read(collection)


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建收藏。"""
    return await create_collection_service(db, user, body)


@router.patch("/{collection_id}", response_model=CollectionRead)
async def update_collection(
    collection_id: str,
    body: CollectionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新收藏。"""
    return await update_collection_service(db, user, collection_id, body)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除收藏。"""
    await delete_collection_service(db, user, collection_id, permanent=permanent)


@router.post("/{collection_id}/restore", response_model=CollectionRead)
async def restore_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复收藏。"""
    return await restore_collection_service(db, user, collection_id)


@router.post("/batch/status")
async def batch_update_collection_status(
    body: CollectionBatchStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新收藏状态。"""
    count = await batch_update_collection_status_service(db, user, body)
    return {"count": count}


@router.post("/{collection_id}/convert/article", response_model=CollectionConvertResult)
async def convert_collection_to_article(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为文章草稿。"""
    return await convert_collection_to_article_service(db, user, collection_id)


@router.post("/{collection_id}/convert/moment-draft", response_model=CollectionConvertResult)
async def convert_collection_to_moment_draft(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为动态草稿。"""
    return await convert_collection_to_moment_draft_service(db, user, collection_id)


@router.post("/{collection_id}/convert/todo", response_model=CollectionConvertResult)
async def convert_collection_to_todo(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将收藏转换为待办。"""
    return await convert_collection_to_todo_service(db, user, collection_id)
