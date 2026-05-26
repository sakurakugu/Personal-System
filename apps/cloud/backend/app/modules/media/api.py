"""文娱推荐模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media.schemas import 文娱列表响应, 文娱条目创建, 文娱条目信息, 文娱条目更新, 文娱筛选项
from app.modules.media.service import (
    创建文娱 as 创建文娱_service,
    删除文娱 as 删除文娱_service,
    get_media_or_404,
    get_public_media_or_404,
    列出公开文娱 as 列出公开文娱_service,
    列出文娱 as 列出文娱_service,
    列出文娱标签 as 列出文娱标签_service,
    列出文娱类型 as 列出文娱类型_service,
    更新文娱 as 更新文娱_service,
    构建文娱读取,
)
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db
router = APIRouter(prefix="/media", tags=["media"])


@router.get("/types", response_model=list[文娱筛选项])
async def 列出文娱类型(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的文娱分类统计。"""
    return await 列出文娱类型_service(db, user)


@router.get("/genres", response_model=list[文娱筛选项])
async def 列出文娱子分类(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的文娱子分类统计。"""
    return await 列出文娱标签_service(db, user, field_name="genres")


@router.get("/tags", response_model=list[文娱筛选项])
async def 列出文娱标签(
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的文娱标签统计。"""
    return await 列出文娱标签_service(db, user, field_name="tags")


@router.get("", response_model=文娱列表响应)
async def 列出文娱(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    media_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    rating: int | None = Query(default=None, ge=1, le=10),
    keyword: str | None = Query(default=None),
    genre: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的文娱列表。"""
    return await 列出文娱_service(
        db,
        user,
        page=page,
        page_size=page_size,
        media_type=media_type,
        status=status,
        rating=rating,
        keyword=keyword,
        genre=genre,
        tag=tag,
    )


@router.get("/public", response_model=文娱列表响应)
async def 列出公开文娱(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    media_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    rating: int | None = Query(default=None, ge=1, le=10),
    keyword: str | None = Query(default=None),
    genre: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """获取公开文娱列表。"""
    return await 列出公开文娱_service(
        db,
        page=page,
        page_size=page_size,
        media_type=media_type,
        status=status,
        rating=rating,
        keyword=keyword,
        genre=genre,
        tag=tag,
    )


@router.get("/public/{media_id}", response_model=文娱条目信息)
async def 获取公开文娱详情(
    media_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取公开文娱详情。"""
    return 构建文娱读取(await get_public_media_or_404(db, media_id))


@router.get("/{media_id}", response_model=文娱条目信息)
async def 获取文娱详情(
    media_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取单条文娱详情。"""
    return 构建文娱读取(await get_media_or_404(db, user, media_id))


@router.post("", response_model=文娱条目信息, status_code=status.HTTP_201_CREATED)
async def 创建文娱(
    body: 文娱条目创建,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建文娱条目。"""
    return await 创建文娱_service(db, user, body)


@router.patch("/{media_id}", response_model=文娱条目信息)
async def 更新文娱(
    media_id: str,
    body: 文娱条目更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新文娱条目。"""
    return await 更新文娱_service(db, user, media_id, body)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除文娱(
    media_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除文娱条目。"""
    await 删除文娱_service(db, user, media_id)
