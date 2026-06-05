"""作品推荐模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import cast as type_cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import String, cast as sql_cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.media.models import 文娱资源, 文娱外部来源, 文娱条目
from app.modules.media.schemas import (
    允许的文娱主分类,
    允许的文娱状态,
    文娱主分类,
    文娱创作者建议,
    文娱列表响应,
    文娱外部来源信息,
    文娱资源信息,
    文娱条目创建,
    文娱条目信息,
    文娱条目更新,
    文娱筛选项,
    文娱状态,
    文娱资源类型,
)
from app.modules.users.models import 用户
from app.shared.kernel.soft_delete import 可软删除对象
from app.shared.storage.client import 构建公开URL, 尽力删除多个对象
from app.shared.storage.file_url import 构建公开文件URL, 构建签名文件URL


def 文娱条目查询():
    """构建文娱条目详情查询。"""
    return select(文娱条目).options(
        selectinload(文娱条目.primary_cover_asset),
        selectinload(文娱条目.assets),
        selectinload(文娱条目.external_sources),
    )


def 解析文娱主分类(value: str) -> str:
    """解析文娱主分类。"""
    if value not in 允许的文娱主分类:
        raise HTTPException(status_code=400, detail="无效的文娱分类")
    return type_cast(文娱主分类, value)


def 解析文娱状态(value: str) -> str:
    """解析文娱状态。"""
    if value not in 允许的文娱状态:
        raise HTTPException(status_code=400, detail="无效的文娱状态")
    return type_cast(文娱状态, value)


def 构建文娱资源读取(asset: 文娱资源, *, 使用公开文件URL: bool = False) -> 文娱资源信息:
    """构造文娱资源响应。"""
    url = None
    preview_url = None
    thumbnail_url = asset.thumbnail_url
    if asset.storage_key:
        允许使用公开文件URL = 使用公开文件URL and asset.asset_type == "cover"
        if 允许使用公开文件URL:
            缓存版本 = int(asset.updated_at.timestamp())
            url = 构建公开文件URL(asset.storage_key, query_params={"v": 缓存版本})
            preview_url = url
        else:
            url = 构建公开URL(asset.storage_key)
            preview_url = 构建签名文件URL(asset.storage_key)
        if (
            asset.mime_type
            and asset.mime_type.startswith("image/")
            and asset.mime_type != "image/svg+xml"
        ):
            构建文件URL = 构建公开文件URL if 允许使用公开文件URL else 构建签名文件URL
            缩略图参数 = {
                "thumbnail_width": 180,
                "thumbnail_height": 240,
            }
            if 允许使用公开文件URL:
                缩略图参数["v"] = int(asset.updated_at.timestamp())
            thumbnail_url = 构建文件URL(
                asset.storage_key,
                query_params=缩略图参数,
            )

    return 文娱资源信息(
        id=asset.id,
        media_item_id=asset.media_item_id,
        asset_type=type_cast(文娱资源类型, asset.asset_type),
        storage_key=asset.storage_key,
        external_url=asset.external_url,
        thumbnail_url=thumbnail_url,
        source_provider=asset.source_provider,
        source_asset_id=asset.source_asset_id,
        original_name=asset.original_name,
        mime_type=asset.mime_type,
        width=asset.width,
        height=asset.height,
        size=asset.size,
        attribution=asset.attribution,
        license=asset.license,
        is_primary=asset.is_primary,
        sort_order=asset.sort_order,
        url=url or asset.external_url,
        preview_url=preview_url or asset.external_url,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def 构建外部来源读取(source: 文娱外部来源) -> 文娱外部来源信息:
    """构造文娱外部来源响应。"""
    return 文娱外部来源信息(
        id=source.id,
        media_item_id=source.media_item_id,
        provider=source.provider,
        external_id=source.external_id,
        external_url=source.external_url,
        fetched_at=source.fetched_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def 构建文娱读取(item: 文娱条目, *, 使用公开文件URL: bool = False) -> 文娱条目信息:
    """构造文娱条目响应。"""
    assets = sorted(item.assets or [], key=lambda asset: (asset.sort_order, asset.created_at))
    return 文娱条目信息(
        id=item.id,
        title=item.title,
        original_title=item.original_title,
        media_type=type_cast(文娱主分类, item.media_type),
        status=type_cast(文娱状态, item.status),
        rating=item.rating,
        creator=item.creator,
        summary=item.summary,
        description=item.description,
        genres=item.genres or [],
        tags=item.tags or [],
        personal_tags=item.personal_tags or [],
        release_date=item.release_date,
        primary_cover_asset_id=item.primary_cover_asset_id,
        primary_cover_asset=构建文娱资源读取(
            item.primary_cover_asset, 使用公开文件URL=使用公开文件URL
        )
        if item.primary_cover_asset
        else None,
        assets=[构建文娱资源读取(asset, 使用公开文件URL=使用公开文件URL) for asset in assets],
        external_sources=[构建外部来源读取(source) for source in item.external_sources or []],
        is_visible=item.is_visible,
        is_deleted=item.is_deleted,
        deleted_at=item.deleted_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _按ID获取用户文娱资源(
    db: AsyncSession, user: 用户, asset_id: UUID | None
) -> 文娱资源 | None:
    """读取当前用户可绑定的文娱资源。"""
    if asset_id is None:
        return None
    result = await db.execute(
        select(文娱资源).where(
            文娱资源.id == asset_id,
            文娱资源.user_id == user.id,
        )
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="文娱资源不存在")
    return asset


def _构建关键词条件(keyword: str):
    """构造关键词搜索条件。"""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return None
    like_keyword = f"%{normalized_keyword}%"
    return or_(
        文娱条目.title.ilike(like_keyword),
        文娱条目.original_title.ilike(like_keyword),
        文娱条目.creator.ilike(like_keyword),
        文娱条目.summary.ilike(like_keyword),
        文娱条目.description.ilike(like_keyword),
    )


async def 获取全部文娱最后更新时间(db: AsyncSession):
    """读取全部文娱数据的最近更新时间，不受公开状态和筛选条件影响。"""
    result = await db.execute(select(func.max(文娱条目.updated_at)))
    return result.scalar_one_or_none()


async def get_media_or_404(db: AsyncSession, user: 用户, media_id: str) -> 文娱条目:
    """读取当前用户的单条文娱条目。"""
    result = await db.execute(
        文娱条目查询().where(
            文娱条目.id == media_id,
            文娱条目.user_id == user.id,
            文娱条目.is_deleted.is_(False),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="文娱条目不存在")
    return item


async def get_public_media_or_404(db: AsyncSession, media_id: str) -> 文娱条目:
    """读取公开文娱条目。"""
    result = await db.execute(
        文娱条目查询().where(
            文娱条目.id == media_id,
            文娱条目.is_visible.is_(True),
            文娱条目.is_deleted.is_(False),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="文娱条目不存在")
    return item


async def 获取已删文娱或404(db: AsyncSession, user: 用户, media_id: str) -> 文娱条目:
    """读取当前用户回收站中的文娱条目。"""
    result = await db.execute(
        文娱条目查询().where(
            文娱条目.id == media_id,
            文娱条目.user_id == user.id,
            文娱条目.is_deleted.is_(True),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="文娱条目不存在或未被删除")
    return item


def 应用文娱删除状态(item: 可软删除对象, *, now: datetime | None = None) -> None:
    """将文娱条目标记为已删除。"""
    item.is_deleted = True
    item.deleted_at = now or datetime.now(timezone.utc)


def 恢复文娱删除状态(item: 可软删除对象) -> None:
    """恢复文娱条目的删除状态。"""
    item.is_deleted = False
    item.deleted_at = None


async def 列出文娱类型(db: AsyncSession, user: 用户) -> list[文娱筛选项]:
    """统计当前用户的文娱主分类。"""
    result = await db.execute(
        select(
            文娱条目.media_type.label("name"),
            func.count(文娱条目.id).label("count"),
        )
        .where(文娱条目.user_id == user.id, 文娱条目.is_deleted.is_(False))
        .group_by(文娱条目.media_type)
        .order_by(func.count(文娱条目.id).desc(), 文娱条目.media_type.asc())
    )
    return [文娱筛选项(name=str(row.name), count=int(row._mapping["count"])) for row in result]


async def 列出文娱标签(
    db: AsyncSession,
    user: 用户,
    *,
    field_name: str,
    media_type: str | None = None,
) -> list[文娱筛选项]:
    """统计当前用户的标签或分类字段。"""
    array_column = {
        "genres": 文娱条目.genres,
        "tags": 文娱条目.tags,
        "personal_tags": 文娱条目.personal_tags,
    }.get(field_name)
    if array_column is None:
        raise HTTPException(status_code=400, detail="无效的文娱统计字段")
    query = select(
        func.unnest(array_column).label("name"),
        func.count(文娱条目.id).label("count"),
    ).where(文娱条目.user_id == user.id, 文娱条目.is_deleted.is_(False))
    if media_type:
        query = query.where(文娱条目.media_type == 解析文娱主分类(media_type))

    result = await db.execute(
        query.group_by("name").order_by(
            func.count(文娱条目.id).desc(), sql_cast("name", String).asc()
        )
    )
    return [
        文娱筛选项(name=str(row.name), count=int(row._mapping["count"]))
        for row in result
        if row.name
    ]


async def 列出文娱创作者建议(
    db: AsyncSession,
    user: 用户,
    *,
    keyword: str | None,
    limit: int,
) -> list[文娱创作者建议]:
    """按当前用户已有数据返回创作者建议。"""
    query = select(
        文娱条目.creator.label("name"),
        func.count(文娱条目.id).label("count"),
    ).where(
        文娱条目.user_id == user.id,
        文娱条目.is_deleted.is_(False),
        文娱条目.creator.is_not(None),
        func.length(func.btrim(文娱条目.creator)) > 0,
    )
    normalized_keyword = (keyword or "").strip()
    if normalized_keyword:
        query = query.where(文娱条目.creator.ilike(f"%{normalized_keyword}%"))

    result = await db.execute(
        query.group_by(文娱条目.creator)
        .order_by(func.count(文娱条目.id).desc(), 文娱条目.creator.asc())
        .limit(limit)
    )
    return [
        文娱创作者建议(name=str(row.name), count=int(row._mapping["count"]))
        for row in result
        if row.name
    ]


async def 列出文娱(
    db: AsyncSession,
    user: 用户,
    *,
    page: int,
    page_size: int,
    media_type: str | None,
    status: str | None,
    rating: int | None,
    keyword: str | None,
    genre: str | None,
    tag: str | None,
    personal_tag: str | None,
    is_deleted: bool = False,
) -> 文娱列表响应:
    """获取当前用户的文娱条目列表。"""
    全部文娱最后更新时间 = await 获取全部文娱最后更新时间(db)
    query = select(文娱条目).where(文娱条目.user_id == user.id, 文娱条目.is_deleted.is_(is_deleted))
    if media_type:
        query = query.where(文娱条目.media_type == 解析文娱主分类(media_type))
    if status:
        query = query.where(文娱条目.status == 解析文娱状态(status))
    if rating is not None:
        query = query.where(文娱条目.rating == rating)
    if genre:
        query = query.where(文娱条目.genres.contains([genre]))
    if tag:
        query = query.where(文娱条目.tags.contains([tag]))
    if personal_tag:
        query = query.where(文娱条目.personal_tags.contains([personal_tag]))
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.options(
            selectinload(文娱条目.primary_cover_asset),
            selectinload(文娱条目.assets),
            selectinload(文娱条目.external_sources),
        )
        .order_by(
            (文娱条目.deleted_at.desc() if is_deleted else 文娱条目.updated_at.desc()),
            文娱条目.created_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return 文娱列表响应(
        items=[构建文娱读取(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        all_data_updated_at=全部文娱最后更新时间,
    )


async def 列出公开文娱(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    media_type: str | None,
    status: str | None,
    rating: int | None,
    keyword: str | None,
    genre: str | None,
    tag: str | None,
    personal_tag: str | None,
) -> 文娱列表响应:
    """获取公开文娱条目列表。"""
    全部文娱最后更新时间 = await 获取全部文娱最后更新时间(db)
    query = select(文娱条目).where(文娱条目.is_visible.is_(True), 文娱条目.is_deleted.is_(False))
    if media_type:
        query = query.where(文娱条目.media_type == 解析文娱主分类(media_type))
    if status:
        query = query.where(文娱条目.status == 解析文娱状态(status))
    if rating is not None:
        query = query.where(文娱条目.rating == rating)
    if genre:
        query = query.where(文娱条目.genres.contains([genre]))
    if tag:
        query = query.where(文娱条目.tags.contains([tag]))
    if personal_tag:
        query = query.where(文娱条目.personal_tags.contains([personal_tag]))
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.options(
            selectinload(文娱条目.primary_cover_asset),
            selectinload(文娱条目.assets),
            selectinload(文娱条目.external_sources),
        )
        .order_by(
            文娱条目.rating.desc().nullslast(),
            文娱条目.updated_at.desc(),
            文娱条目.created_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return 文娱列表响应(
        items=[构建文娱读取(item, 使用公开文件URL=True) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        all_data_updated_at=全部文娱最后更新时间,
    )


async def 创建文娱(db: AsyncSession, user: 用户, body: 文娱条目创建) -> 文娱条目信息:
    """创建文娱条目。"""
    primary_cover_asset = await _按ID获取用户文娱资源(db, user, body.primary_cover_asset_id)
    item = 文娱条目(
        user_id=user.id,
        title=body.title,
        original_title=body.original_title,
        media_type=body.media_type,
        status=body.status,
        rating=body.rating,
        creator=body.creator,
        summary=body.summary,
        description=body.description,
        genres=body.genres or [],
        tags=body.tags or [],
        personal_tags=body.personal_tags or [],
        release_date=body.release_date,
        primary_cover_asset_id=body.primary_cover_asset_id,
        primary_cover_asset=primary_cover_asset,
        is_visible=body.is_visible,
    )
    db.add(item)
    await db.flush()
    return 构建文娱读取(await get_media_or_404(db, user, str(item.id)))


async def 更新文娱(
    db: AsyncSession,
    user: 用户,
    media_id: str,
    body: 文娱条目更新,
) -> 文娱条目信息:
    """更新文娱条目。"""
    item = await get_media_or_404(db, user, media_id)
    data = body.model_dump(exclude_unset=True)
    if "primary_cover_asset_id" in data:
        primary_cover_asset = await _按ID获取用户文娱资源(db, user, data["primary_cover_asset_id"])
        if primary_cover_asset is not None and primary_cover_asset.media_item_id != item.id:
            raise HTTPException(status_code=400, detail="封面资源不属于该文娱条目")
        item.primary_cover_asset_id = data["primary_cover_asset_id"]
        item.primary_cover_asset = primary_cover_asset
        data.pop("primary_cover_asset_id")

    for key, value in data.items():
        setattr(item, key, value)

    await db.flush()
    return 构建文娱读取(await get_media_or_404(db, user, media_id))


async def 删除文娱(db: AsyncSession, user: 用户, media_id: str, *, permanent: bool) -> None:
    """删除文娱条目。"""
    if permanent:
        item = await 获取已删文娱或404(db, user, media_id)
        storage_keys = [asset.storage_key for asset in item.assets or [] if asset.storage_key]
        await db.delete(item)
        尽力删除多个对象(storage_keys)
        return

    item = await get_media_or_404(db, user, media_id)
    应用文娱删除状态(item)
    await db.flush()


async def 恢复文娱(db: AsyncSession, user: 用户, media_id: str) -> 文娱条目信息:
    """从回收站恢复文娱条目。"""
    item = await 获取已删文娱或404(db, user, media_id)
    恢复文娱删除状态(item)
    await db.flush()
    return 构建文娱读取(await get_media_or_404(db, user, media_id))
