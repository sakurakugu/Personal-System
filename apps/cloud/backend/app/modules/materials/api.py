"""资料库模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.materials.schemas import 资料创建, 资料信息, 资料批量状态更新, 资料更新, 资料标签信息
from app.modules.materials.service import (
    get_material_or_404,
    删除资料 as 删除资料_service,
    创建资料 as 创建资料_service,
    列出资料 as 列出资料_service,
    列出资料标签 as 列出资料标签_service,
    恢复资料 as 恢复资料_service,
    批量更新资料状态 as 批量更新资料状态_service,
    构建资料读取,
    更新资料 as 更新资料_service,
)
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db
from app.shared.kernel.pagination import PaginatedResponse

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/tags", response_model=list[资料标签信息])
async def 列出资料标签(
    is_deleted: bool = Query(False, description="是否统计回收站标签"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的资料库标签列表。"""
    return await 列出资料标签_service(db, user, is_deleted=is_deleted)


@router.get("", response_model=PaginatedResponse)
async def 列出资料(
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
    """获取当前用户的资料库列表。"""
    return await 列出资料_service(
        db,
        user,
        page=page,
        page_size=page_size,
        status=status,
        material_type=type,
        tag=tag,
        keyword=keyword,
        is_deleted=is_deleted,
    )


@router.get("/{material_id}", response_model=资料信息)
async def get_material(
    material_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取单条资料库详情。"""
    material = await get_material_or_404(db, user, material_id)
    return 构建资料读取(material)


@router.post("", response_model=资料信息, status_code=status.HTTP_201_CREATED)
async def 创建资料(
    body: 资料创建,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """创建资料库条目。"""
    return await 创建资料_service(db, user, body)


@router.patch("/{material_id}", response_model=资料信息)
async def 更新资料(
    material_id: str,
    body: 资料更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新资料库条目。"""
    return await 更新资料_service(db, user, material_id, body)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除资料(
    material_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """删除资料库条目。"""
    await 删除资料_service(db, user, material_id, permanent=permanent)


@router.post("/{material_id}/restore", response_model=资料信息)
async def 恢复资料(
    material_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """从回收站恢复资料库条目。"""
    return await 恢复资料_service(db, user, material_id)


@router.post("/batch/status")
async def 批量更新资料状态(
    body: 资料批量状态更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """批量更新资料库状态。"""
    count = await 批量更新资料状态_service(db, user, body)
    return {"count": count}
