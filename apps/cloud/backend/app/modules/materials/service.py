"""资料库模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.files.models import File, FilePurpose
from app.modules.files.presentation import 构建文件读取
from app.modules.files.schemas import FileRead
from app.modules.materials.models import 资料, 资料标签, 资料标签关联, 资料状态, 资料类型, 资料资产
from app.modules.materials.schemas import 资料创建, 资料信息, 资料批量状态更新, 资料更新, 资料标签信息, 资料资产信息, 资料资产输入
from app.modules.users.models import 用户
from app.shared.kernel.pagination import PaginatedResponse


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def material_query():
    """构建资料库详情查询。"""
    return (
        select(资料)
        .options(
            selectinload(资料.assets).selectinload(资料资产.file),
            selectinload(资料.material_tags),
        )
    )


def 解析资料类型(value: str) -> 资料类型:
    """解析资料库类型。"""
    try:
        return 资料类型(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的资料库类型") from exc


def 解析资料状态(value: str) -> 资料状态:
    """解析资料库状态。"""
    try:
        return 资料状态(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的资料库状态") from exc


def 构建资料资产读取(asset: 资料资产) -> 资料资产信息:
    """构造资料库附件响应。"""
    if asset.file is None:
        raise HTTPException(status_code=500, detail="资料库附件数据不完整")
    return 资料资产信息(
        id=asset.id,
        file_id=asset.file_id,
        sort_order=asset.sort_order,
        created_at=asset.created_at,
        file=FileRead.model_validate(构建文件读取(asset.file)),
    )


def 构建资料读取(material: 资料) -> 资料信息:
    """构造资料库详情响应。"""
    return 资料信息(
        id=material.id,
        type=material.type.value,
        title=material.title,
        content_text=material.content_text,
        note=material.note,
        status=material.status.value,
        tags=material.tags,
        assets=[构建资料资产读取(asset) for asset in material.assets],
        archived_at=material.archived_at,
        is_deleted=material.is_deleted,
        deleted_at=material.deleted_at,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


def 应用资料状态(material: 资料, status: 资料状态, *, now: datetime | None = None) -> None:
    """同步资料库状态与归档时间。"""
    material.status = status
    if status == 资料状态.archived:
        material.archived_at = material.archived_at or (now or utcnow())
        return
    material.archived_at = None


def 应用资料删除状态(material: 资料, *, now: datetime | None = None) -> None:
    """将资料库条目标记为已删除。"""
    material.is_deleted = True
    material.deleted_at = now or utcnow()


def 恢复资料删除状态(material: 资料) -> None:
    """恢复资料库条目的删除状态。"""
    material.is_deleted = False
    material.deleted_at = None


def _规范化标签名称(tag_names: list[str] | None) -> list[str]:
    """返回去重后的标签列表。"""
    if not tag_names:
        return []
    return list(dict.fromkeys(tag_names))


async def _确保资料标签已加载(db: AsyncSession, material: 资料) -> None:
    """确保资料库标签已加载。"""
    if "material_tags" in inspect(material).unloaded:
        await db.refresh(material, attribute_names=["material_tags"])


async def _确保资料资产已加载(db: AsyncSession, material: 资料) -> None:
    """确保资料库附件已加载。"""
    if "assets" in inspect(material).unloaded:
        await db.refresh(material, attribute_names=["assets"])


async def _按名称获取用户标签(db: AsyncSession, user_id: UUID, tag_names: list[str]) -> dict[str, 资料标签]:
    """按名称读取用户资料库标签。"""
    if not tag_names:
        return {}

    result = await db.execute(
        select(资料标签).where(
            资料标签.user_id == user_id,
            资料标签.name.in_(tag_names),
        )
    )
    tags = result.scalars().all()
    return {tag.name: tag for tag in tags}


async def _同步资料标签(db: AsyncSession, material: 资料, tag_names: list[str] | None) -> None:
    """同步资料库标签。"""
    await _确保资料标签已加载(db, material)
    normalized_names = _规范化标签名称(tag_names)
    if not normalized_names:
        material.material_tags = []
        return

    existing_tags = await _按名称获取用户标签(db, material.user_id, normalized_names)
    resolved_tags: list[资料标签] = []
    for name in normalized_names:
        tag = existing_tags.get(name)
        if tag is None:
            tag = 资料标签(user_id=material.user_id, name=name)
            db.add(tag)
            await db.flush()
            existing_tags[name] = tag
        resolved_tags.append(tag)

    material.material_tags = resolved_tags


async def _按ID获取用户文件(db: AsyncSession, user: 用户, file_ids: list[UUID]) -> dict[UUID, File]:
    """读取当前用户可绑定的文件。"""
    if not file_ids:
        return {}
    result = await db.execute(
        select(File).where(
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.is_deleted.is_(False),
            File.id.in_(file_ids),
        )
    )
    files = list(result.scalars().all())
    file_map = {file.id: file for file in files}
    if len(file_map) != len(set(file_ids)):
        raise HTTPException(status_code=404, detail="存在无效的附件文件")
    return file_map


async def _同步资料资产(
    db: AsyncSession,
    material: 资料,
    user: 用户,
    assets: list[资料资产输入] | None,
) -> None:
    """同步资料库附件。"""
    await _确保资料资产已加载(db, material)
    if not assets:
        material.assets = []
        return

    deduplicated_assets: list[资料资产输入] = []
    seen_file_ids: set[UUID] = set()
    for asset in assets:
        if asset.file_id in seen_file_ids:
            continue
        seen_file_ids.add(asset.file_id)
        deduplicated_assets.append(asset)

    file_map = await _按ID获取用户文件(db, user, [asset.file_id for asset in deduplicated_assets])
    material.assets = [
        资料资产(
            file_id=asset.file_id,
            sort_order=asset.sort_order,
            file=file_map[asset.file_id],
        )
        for asset in deduplicated_assets
    ]


def _构建关键词条件(keyword: str):
    """构造关键词搜索条件。"""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return None
    like_keyword = f"%{normalized_keyword}%"
    return or_(
        资料.title.ilike(like_keyword),
        资料.content_text.ilike(like_keyword),
        资料.note.ilike(like_keyword),
    )


async def 列出资料标签(db: AsyncSession, user: 用户, *, is_deleted: bool) -> list[资料标签信息]:
    """读取当前用户的资料库标签列表。"""
    result = await db.execute(
        select(
            资料标签.name,
            func.count(资料标签关联.material_id).label("count"),
        )
        .select_from(资料标签)
        .join(资料标签关联, 资料标签关联.tag_id == 资料标签.id)
        .join(资料, 资料.id == 资料标签关联.material_id)
        .where(资料标签.user_id == user.id, 资料.is_deleted == is_deleted)
        .group_by(资料标签.id, 资料标签.name)
        .order_by(func.count(资料标签关联.material_id).desc(), 资料标签.name.asc())
    )
    return [资料标签信息(name=row.name, count=row._mapping["count"]) for row in result]


async def 列出资料(
    db: AsyncSession,
    user: 用户,
    *,
    page: int,
    page_size: int,
    status: str | None,
    material_type: str | None,
    tag: str | None,
    keyword: str | None,
    is_deleted: bool,
) -> PaginatedResponse:
    """获取当前用户的资料库列表。"""
    query = select(资料).where(资料.user_id == user.id, 资料.is_deleted == is_deleted)

    if status:
        query = query.where(资料.status == 解析资料状态(status))
    if material_type:
        query = query.where(资料.type == 解析资料类型(material_type))
    if tag:
        query = query.where(资料.material_tags.any(资料标签.name == tag))
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    primary_order_column = 资料.deleted_at.desc() if is_deleted else 资料.updated_at.desc()
    result = await db.execute(
        query.options(
            selectinload(资料.assets).selectinload(资料资产.file),
            selectinload(资料.material_tags),
        )
        .order_by(primary_order_column, 资料.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[构建资料读取(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_material_or_404(db: AsyncSession, user: 用户, material_id: str) -> 资料:
    """读取当前用户的单条资料库条目。"""
    result = await db.execute(
        material_query().where(
            资料.id == material_id,
            资料.user_id == user.id,
            资料.is_deleted.is_(False),
        )
    )
    material = result.scalar_one_or_none()
    if material is None:
        raise HTTPException(status_code=404, detail="资料库条目不存在")
    return material


async def 获取已删资料或404(db: AsyncSession, user: 用户, material_id: str) -> 资料:
    """读取当前用户回收站中的资料库条目。"""
    result = await db.execute(
        material_query().where(
            资料.id == material_id,
            资料.user_id == user.id,
            资料.is_deleted.is_(True),
        )
    )
    material = result.scalar_one_or_none()
    if material is None:
        raise HTTPException(status_code=404, detail="资料库条目不存在或未被删除")
    return material


async def 创建资料(db: AsyncSession, user: 用户, body: 资料创建) -> 资料信息:
    """创建资料库条目。"""
    current_time = utcnow()
    material = 资料(
        user_id=user.id,
        type=解析资料类型(body.type),
        title=body.title,
        content_text=body.content_text,
        note=body.note,
    )
    应用资料状态(material, 解析资料状态(body.status), now=current_time)
    db.add(material)
    await db.flush()
    await _同步资料标签(db, material, body.tags)
    await _同步资料资产(db, material, user, body.assets)
    await db.flush()
    return 构建资料读取(await get_material_or_404(db, user, str(material.id)))


async def 更新资料(
    db: AsyncSession,
    user: 用户,
    material_id: str,
    body: 资料更新,
) -> 资料信息:
    """更新资料库条目。"""
    material = await get_material_or_404(db, user, material_id)
    data = body.model_dump(exclude_unset=True)
    tag_names = data.pop("tags", None)
    assets = data.pop("assets", None)
    type_value = data.pop("type", None)
    status_value = data.pop("status", None)

    for key, value in data.items():
        setattr(material, key, value)

    if type_value is not None:
        material.type = 解析资料类型(type_value)
    if status_value is not None:
        应用资料状态(material, 解析资料状态(status_value))
    if "tags" in body.model_fields_set:
        await _同步资料标签(db, material, tag_names)
    if "assets" in body.model_fields_set:
        await _同步资料资产(db, material, user, assets)

    await db.flush()
    return 构建资料读取(await get_material_or_404(db, user, material_id))


async def 删除资料(db: AsyncSession, user: 用户, material_id: str, *, permanent: bool) -> None:
    """删除资料库条目。"""
    if permanent:
        material = await 获取已删资料或404(db, user, material_id)
        await db.delete(material)
        return

    material = await get_material_or_404(db, user, material_id)
    应用资料删除状态(material)
    await db.flush()


async def 恢复资料(db: AsyncSession, user: 用户, material_id: str) -> 资料信息:
    """从回收站恢复资料库条目。"""
    material = await 获取已删资料或404(db, user, material_id)
    恢复资料删除状态(material)
    await db.flush()
    return 构建资料读取(await get_material_or_404(db, user, material_id))


async def 批量更新资料状态(
    db: AsyncSession,
    user: 用户,
    body: 资料批量状态更新,
) -> int:
    """批量更新资料库状态。"""
    result = await db.execute(
        select(资料).where(
            资料.user_id == user.id,
            资料.is_deleted.is_(False),
            资料.id.in_(body.ids),
        )
    )
    materials = list(result.scalars().all())
    if len(materials) != len(set(body.ids)):
        raise HTTPException(status_code=404, detail="存在无效的资料库条目")

    next_status = 解析资料状态(body.status)
    current_time = utcnow()
    for material in materials:
        应用资料状态(material, next_status, now=current_time)
    await db.flush()
    return len(materials)
