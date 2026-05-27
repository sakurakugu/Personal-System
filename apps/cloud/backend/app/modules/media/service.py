"""作品推荐模块服务。"""

from __future__ import annotations

import math
from typing import cast as type_cast
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import String, cast as sql_cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.files.models import File, FilePurpose
from app.modules.files.presentation import 构建文件读取
from app.modules.files.schemas import FileRead
from app.modules.media.models import 文娱条目
from app.modules.media.schemas import (
    允许的文娱主分类,
    允许的文娱状态,
    文娱主分类,
    文娱创作者建议,
    文娱列表响应,
    文娱条目创建,
    文娱条目信息,
    文娱条目更新,
    文娱筛选项,
    文娱状态,
)
from app.modules.users.models import 用户


def 文娱条目查询():
    """构建文娱条目详情查询。"""
    return select(文娱条目).options(selectinload(文娱条目.cover_file))


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


def 构建文娱读取(item: 文娱条目) -> 文娱条目信息:
    """构造文娱条目响应。"""
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
        cover_file_id=item.cover_file_id,
        cover_file=FileRead.model_validate(构建文件读取(item.cover_file)) if item.cover_file else None,
        is_visible=item.is_visible,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _按ID获取用户文件(db: AsyncSession, user: 用户, file_id: UUID | None) -> File | None:
    """读取当前用户可绑定的封面文件。"""
    if file_id is None:
        return None
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
        )
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=404, detail="封面文件不存在")
    return file


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
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="文娱条目不存在")
    return item


async def 列出文娱类型(db: AsyncSession, user: 用户) -> list[文娱筛选项]:
    """统计当前用户的文娱主分类。"""
    result = await db.execute(
        select(
            文娱条目.media_type.label("name"),
            func.count(文娱条目.id).label("count"),
        )
        .where(文娱条目.user_id == user.id)
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
    """统计当前用户的标签或子分类。"""
    array_column = 文娱条目.tags if field_name == "tags" else 文娱条目.genres
    query = (
        select(
            func.unnest(array_column).label("name"),
            func.count(文娱条目.id).label("count"),
        )
        .where(文娱条目.user_id == user.id)
    )
    if media_type:
        query = query.where(文娱条目.media_type == 解析文娱主分类(media_type))

    result = await db.execute(
        query.group_by("name")
        .order_by(func.count(文娱条目.id).desc(), sql_cast("name", String).asc())
    )
    return [文娱筛选项(name=str(row.name), count=int(row._mapping["count"])) for row in result if row.name]


async def 列出文娱创作者建议(
    db: AsyncSession,
    user: 用户,
    *,
    keyword: str | None,
    limit: int,
) -> list[文娱创作者建议]:
    """按当前用户已有数据返回创作者建议。"""
    query = (
        select(
            文娱条目.creator.label("name"),
            func.count(文娱条目.id).label("count"),
        )
        .where(
            文娱条目.user_id == user.id,
            文娱条目.creator.is_not(None),
            func.length(func.btrim(文娱条目.creator)) > 0,
        )
    )
    normalized_keyword = (keyword or "").strip()
    if normalized_keyword:
        query = query.where(文娱条目.creator.ilike(f"%{normalized_keyword}%"))

    result = await db.execute(
        query.group_by(文娱条目.creator)
        .order_by(func.count(文娱条目.id).desc(), 文娱条目.creator.asc())
        .limit(limit)
    )
    return [文娱创作者建议(name=str(row.name), count=int(row._mapping["count"])) for row in result if row.name]


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
) -> 文娱列表响应:
    """获取当前用户的文娱条目列表。"""
    全部文娱最后更新时间 = await 获取全部文娱最后更新时间(db)
    query = select(文娱条目).where(文娱条目.user_id == user.id)
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
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.options(selectinload(文娱条目.cover_file))
        .order_by(文娱条目.updated_at.desc(), 文娱条目.created_at.desc())
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
) -> 文娱列表响应:
    """获取公开文娱条目列表。"""
    全部文娱最后更新时间 = await 获取全部文娱最后更新时间(db)
    query = select(文娱条目).where(文娱条目.is_visible.is_(True))
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
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.options(selectinload(文娱条目.cover_file))
        .order_by(文娱条目.rating.desc().nullslast(), 文娱条目.updated_at.desc(), 文娱条目.created_at.desc())
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


async def 创建文娱(db: AsyncSession, user: 用户, body: 文娱条目创建) -> 文娱条目信息:
    """创建文娱条目。"""
    cover_file = await _按ID获取用户文件(db, user, body.cover_file_id)
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
        cover_file_id=body.cover_file_id,
        cover_file=cover_file,
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
    if "cover_file_id" in data:
        cover_file = await _按ID获取用户文件(db, user, data["cover_file_id"])
        item.cover_file_id = data["cover_file_id"]
        item.cover_file = cover_file
        data.pop("cover_file_id")

    for key, value in data.items():
        setattr(item, key, value)

    await db.flush()
    return 构建文娱读取(await get_media_or_404(db, user, media_id))


async def 删除文娱(db: AsyncSession, user: 用户, media_id: str) -> None:
    """删除文娱条目。"""
    item = await get_media_or_404(db, user, media_id)
    await db.delete(item)
