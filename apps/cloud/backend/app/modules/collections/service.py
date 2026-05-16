"""收藏模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.files.models import File, FilePurpose
from app.modules.moments.models import 动态
from app.modules.users.models import 用户
from app.modules.collections.models import 收藏, 收藏资产, 收藏状态, 收藏标签, 收藏标签关联, 收藏类型
from app.modules.collections.schemas import 收藏资产输入, 收藏资产信息, 收藏批量状态更新, 收藏转换结果, 收藏创建, 收藏信息, 收藏标签信息, 收藏更新
from app.modules.todos.schemas import TodoCreate
from app.modules.todos.service import create_todo
from app.modules.articles.schemas import 文章草稿创建
from app.modules.articles.crud import 创建文章草稿
from app.modules.files.presentation import 构建文件读取
from app.modules.files.schemas import FileRead
from app.shared.kernel.pagination import PaginatedResponse


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def collection_query():
    """构建收藏详情查询。"""
    return (
        select(收藏)
        .options(
            selectinload(收藏.assets).selectinload(收藏资产.file),
            selectinload(收藏.collection_tags),
        )
    )


def 解析收藏类型(value: str) -> 收藏类型:
    """解析收藏类型。"""
    try:
        return 收藏类型(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的收藏类型") from exc


def 解析收藏状态(value: str) -> 收藏状态:
    """解析收藏状态。"""
    try:
        return 收藏状态(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的收藏状态") from exc


def 构建收藏资产读取(asset: 收藏资产) -> 收藏资产信息:
    """构造收藏附件响应。"""
    if asset.file is None:
        raise HTTPException(status_code=500, detail="收藏附件数据不完整")
    return 收藏资产信息(
        id=asset.id,
        file_id=asset.file_id,
        sort_order=asset.sort_order,
        created_at=asset.created_at,
        file=FileRead.model_validate(构建文件读取(asset.file)),
    )


def 构建收藏读取(collection: 收藏) -> 收藏信息:
    """构造收藏详情响应。"""
    return 收藏信息(
        id=collection.id,
        type=collection.type.value,
        title=collection.title,
        content_text=collection.content_text,
        note=collection.note,
        status=collection.status.value,
        tags=collection.tags,
        assets=[构建收藏资产读取(asset) for asset in collection.assets],
        archived_at=collection.archived_at,
        is_deleted=collection.is_deleted,
        deleted_at=collection.deleted_at,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def 应用归档状态(collection: 收藏, status: 收藏状态, *, now: datetime | None = None) -> None:
    """同步归档时间。"""
    collection.status = status
    if status == 收藏状态.archived:
        collection.archived_at = collection.archived_at or (now or utcnow())
        return
    collection.archived_at = None


def 应用收藏删除状态(collection: 收藏, *, now: datetime | None = None) -> None:
    """将收藏标记为已删除。"""
    collection.is_deleted = True
    collection.deleted_at = now or utcnow()


def 恢复收藏删除状态(collection: 收藏) -> None:
    """恢复收藏的删除状态。"""
    collection.is_deleted = False
    collection.deleted_at = None


def _规范化标签名称(tag_names: list[str] | None) -> list[str]:
    """返回去重后的标签列表。"""
    if not tag_names:
        return []
    return list(dict.fromkeys(tag_names))


async def _确保收藏标签已加载(db: AsyncSession, collection: 收藏) -> None:
    """确保收藏标签已加载。"""
    if "collection_tags" in inspect(collection).unloaded:
        await db.refresh(collection, attribute_names=["collection_tags"])


async def _确保收藏资产已加载(db: AsyncSession, collection: 收藏) -> None:
    """确保收藏附件已加载。"""
    if "assets" in inspect(collection).unloaded:
        await db.refresh(collection, attribute_names=["assets"])


async def _按名称获取用户标签(db: AsyncSession, user_id: UUID, tag_names: list[str]) -> dict[str, 收藏标签]:
    """按名称读取用户收藏标签。"""
    if not tag_names:
        return {}

    result = await db.execute(
        select(收藏标签).where(
            收藏标签.user_id == user_id,
            收藏标签.name.in_(tag_names),
        )
    )
    tags = result.scalars().all()
    return {tag.name: tag for tag in tags}


async def _同步收藏标签(db: AsyncSession, collection: 收藏, tag_names: list[str] | None) -> None:
    """同步收藏标签。"""
    await _确保收藏标签已加载(db, collection)
    normalized_names = _规范化标签名称(tag_names)
    if not normalized_names:
        collection.collection_tags = []
        return

    existing_tags = await _按名称获取用户标签(db, collection.user_id, normalized_names)
    resolved_tags: list[收藏标签] = []
    for name in normalized_names:
        tag = existing_tags.get(name)
        if tag is None:
            tag = 收藏标签(user_id=collection.user_id, name=name)
            db.add(tag)
            await db.flush()
            existing_tags[name] = tag
        resolved_tags.append(tag)

    collection.collection_tags = resolved_tags


async def _按ID获取用户文件(db: AsyncSession, user: 用户, file_ids: list[UUID]) -> dict[UUID, File]:
    """读取当前用户可绑定的文件。"""
    if not file_ids:
        return {}
    result = await db.execute(
        select(File).where(
            File.user_id == user.id,
            File.purpose == FilePurpose.file,
            File.id.in_(file_ids),
        )
    )
    files = list(result.scalars().all())
    file_map = {file.id: file for file in files}
    if len(file_map) != len(set(file_ids)):
        raise HTTPException(status_code=404, detail="存在无效的附件文件")
    return file_map


async def _同步收藏资产(
    db: AsyncSession,
    collection: 收藏,
    user: 用户,
    assets: list[收藏资产输入] | None,
) -> None:
    """同步收藏附件。"""
    await _确保收藏资产已加载(db, collection)
    if not assets:
        collection.assets = []
        return

    deduplicated_assets: list[收藏资产输入] = []
    seen_file_ids: set[UUID] = set()
    for asset in assets:
        if asset.file_id in seen_file_ids:
            continue
        seen_file_ids.add(asset.file_id)
        deduplicated_assets.append(asset)

    file_map = await _按ID获取用户文件(db, user, [asset.file_id for asset in deduplicated_assets])
    collection.assets = [
        收藏资产(
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
        收藏.title.ilike(like_keyword),
        收藏.content_text.ilike(like_keyword),
        收藏.note.ilike(like_keyword),
    )


async def 列出收藏标签(db: AsyncSession, user: 用户, *, is_deleted: bool) -> list[收藏标签信息]:
    """读取当前用户的收藏标签列表。"""
    result = await db.execute(
        select(
            收藏标签.name,
            func.count(收藏标签关联.collection_id).label("count"),
        )
        .select_from(收藏标签)
        .join(收藏标签关联, 收藏标签关联.tag_id == 收藏标签.id)
        .join(收藏, 收藏.id == 收藏标签关联.collection_id)
        .where(收藏标签.user_id == user.id, 收藏.is_deleted == is_deleted)
        .group_by(收藏标签.id, 收藏标签.name)
        .order_by(func.count(收藏标签关联.collection_id).desc(), 收藏标签.name.asc())
    )
    return [收藏标签信息(name=row.name, count=row._mapping["count"]) for row in result]


async def 列出收藏(
    db: AsyncSession,
    user: 用户,
    *,
    page: int,
    page_size: int,
    status: str | None,
    collection_type: str | None,
    tag: str | None,
    keyword: str | None,
    is_deleted: bool,
) -> PaginatedResponse:
    """获取当前用户的收藏列表。"""
    query = select(收藏).where(收藏.user_id == user.id, 收藏.is_deleted == is_deleted)

    if status:
        query = query.where(收藏.status == 解析收藏状态(status))
    if collection_type:
        query = query.where(收藏.type == 解析收藏类型(collection_type))
    if tag:
        query = query.where(收藏.collection_tags.any(收藏标签.name == tag))
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    primary_order_column = 收藏.deleted_at.desc() if is_deleted else 收藏.updated_at.desc()
    result = await db.execute(
        query.options(
            selectinload(收藏.assets).selectinload(收藏资产.file),
            selectinload(收藏.collection_tags),
        )
        .order_by(primary_order_column, 收藏.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[构建收藏读取(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_collection_or_404(db: AsyncSession, user: 用户, collection_id: str) -> 收藏:
    """读取当前用户的单条收藏。"""
    result = await db.execute(
        collection_query().where(
            收藏.id == collection_id,
            收藏.user_id == user.id,
            收藏.is_deleted.is_(False),
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return collection


async def 获取已删收藏或404(db: AsyncSession, user: 用户, collection_id: str) -> 收藏:
    """读取当前用户回收站中的收藏。"""
    result = await db.execute(
        collection_query().where(
            收藏.id == collection_id,
            收藏.user_id == user.id,
            收藏.is_deleted.is_(True),
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail="收藏不存在或未被删除")
    return collection


async def 创建收藏(db: AsyncSession, user: 用户, body: 收藏创建) -> 收藏信息:
    """创建收藏。"""
    current_time = utcnow()
    collection = 收藏(
        user_id=user.id,
        type=解析收藏类型(body.type),
        title=body.title,
        content_text=body.content_text,
        note=body.note,
    )
    应用归档状态(collection, 解析收藏状态(body.status), now=current_time)
    db.add(collection)
    await db.flush()
    await _同步收藏标签(db, collection, body.tags)
    await _同步收藏资产(db, collection, user, body.assets)
    await db.flush()
    return 构建收藏读取(await get_collection_or_404(db, user, str(collection.id)))


async def 更新收藏(
    db: AsyncSession,
    user: 用户,
    collection_id: str,
    body: 收藏更新,
) -> 收藏信息:
    """更新收藏。"""
    collection = await get_collection_or_404(db, user, collection_id)
    data = body.model_dump(exclude_unset=True)
    tag_names = data.pop("tags", None)
    assets = data.pop("assets", None)
    type_value = data.pop("type", None)
    status_value = data.pop("status", None)

    for key, value in data.items():
        setattr(collection, key, value)

    if type_value is not None:
        collection.type = 解析收藏类型(type_value)
    if status_value is not None:
        应用归档状态(collection, 解析收藏状态(status_value))
    if "tags" in body.model_fields_set:
        await _同步收藏标签(db, collection, tag_names)
    if "assets" in body.model_fields_set:
        await _同步收藏资产(db, collection, user, assets)

    await db.flush()
    return 构建收藏读取(await get_collection_or_404(db, user, collection_id))


async def 删除收藏(db: AsyncSession, user: 用户, collection_id: str, *, permanent: bool) -> None:
    """删除收藏。"""
    if permanent:
        collection = await 获取已删收藏或404(db, user, collection_id)
        await db.delete(collection)
        return

    collection = await get_collection_or_404(db, user, collection_id)
    应用收藏删除状态(collection)
    await db.flush()


async def 恢复收藏(db: AsyncSession, user: 用户, collection_id: str) -> 收藏信息:
    """从回收站恢复收藏。"""
    collection = await 获取已删收藏或404(db, user, collection_id)
    恢复收藏删除状态(collection)
    await db.flush()
    return 构建收藏读取(await get_collection_or_404(db, user, collection_id))


async def 批量更新收藏状态(
    db: AsyncSession,
    user: 用户,
    body: 收藏批量状态更新,
) -> int:
    """批量更新收藏状态。"""
    result = await db.execute(
        select(收藏).where(
            收藏.user_id == user.id,
            收藏.is_deleted.is_(False),
            收藏.id.in_(body.ids),
        )
    )
    collections = list(result.scalars().all())
    if len(collections) != len(set(body.ids)):
        raise HTTPException(status_code=404, detail="存在无效的收藏记录")

    next_status = 解析收藏状态(body.status)
    current_time = utcnow()
    for collection in collections:
        应用归档状态(collection, next_status, now=current_time)
    await db.flush()
    return len(collections)


def _获取收藏标题(collection: 收藏) -> str:
    """返回收藏的展示标题。"""
    if collection.title:
        return collection.title
    if collection.note:
        return _truncate_text(collection.note, 60)
    if collection.content_text:
        return _truncate_text(collection.content_text, 60)
    return "未命名收藏"


def _构建文章内容(collection: 收藏) -> str:
    """将收藏整理为文章草稿正文。"""
    sections: list[str] = []
    if collection.note:
        sections.append(f"## 备注\n\n{collection.note}")
    if collection.content_text:
        sections.append(f"## 内容\n\n{collection.content_text}")
    if not sections:
        sections.append("## 内容\n\n待补充")
    return "\n\n".join(sections)


def _truncate_text(value: str, length: int) -> str:
    """按长度截断文本。"""
    if len(value) <= length:
        return value
    if length <= 1:
        return value[:length]
    return f"{value[: length - 1]}…"


def _构建动态草稿标题(collection: 收藏) -> str | None:
    """构造动态草稿标题。"""
    title = collection.title
    if title is None:
        return None
    return _truncate_text(title, 100)


def _构建动态草稿内容(collection: 收藏) -> str:
    """构造动态草稿正文。"""
    parts: list[str] = []
    if collection.note:
        parts.append(collection.note)
    elif collection.content_text:
        parts.append(collection.content_text)

    content = "\n\n".join(part.strip() for part in parts if part.strip())
    if not content:
        content = _获取收藏标题(collection)
    return _truncate_text(content, 1000)


def _构建待办描述(collection: 收藏) -> str | None:
    """构造待办描述。"""
    parts: list[str] = []
    if collection.note:
        parts.append(f"备注：{collection.note}")
    if collection.content_text:
        parts.append(f"内容：{_truncate_text(collection.content_text, 500)}")
    description = "\n".join(parts).strip()
    return description or None


async def 转换收藏为文章(
    db: AsyncSession,
    user: 用户,
    collection_id: str,
) -> 收藏转换结果:
    """将收藏转换为文章草稿。"""
    collection = await get_collection_or_404(db, user, collection_id)
    article = await 创建文章草稿(
        db,
        文章草稿创建(
            title=_获取收藏标题(collection),
            content=_构建文章内容(collection),
            excerpt=_truncate_text(collection.note or _获取收藏标题(collection), 500),
            cover_url=None,
        ),
        user,
    )
    await db.flush()
    return 收藏转换结果(
        collection_id=collection.id,
        target_type="article",
        target_id=article.id,
        message="已生成文章草稿",
    )


async def 转换收藏为动态草稿(
    db: AsyncSession,
    user: 用户,
    collection_id: str,
) -> 收藏转换结果:
    """将收藏转换为动态草稿。"""
    collection = await get_collection_or_404(db, user, collection_id)
    result = await db.execute(
        select(动态).where(
            动态.user_id == user.id,
            动态.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        draft = 动态(
            user_id=user.id,
            title=_构建动态草稿标题(collection),
            content=_构建动态草稿内容(collection),
            is_published=False,
        )
        db.add(draft)
    else:
        draft.title = _构建动态草稿标题(collection)
        draft.content = _构建动态草稿内容(collection)
        draft.updated_at = utcnow()

    await db.flush()
    return 收藏转换结果(
        collection_id=collection.id,
        target_type="moment_draft",
        target_id=draft.id,
        message="已写入动态草稿",
    )


async def 转换收藏为待办(
    db: AsyncSession,
    user: 用户,
    collection_id: str,
) -> 收藏转换结果:
    """将收藏转换为待办。"""
    collection = await get_collection_or_404(db, user, collection_id)
    todo = await create_todo(
        db,
        user,
        TodoCreate(
            title=_truncate_text(_获取收藏标题(collection), 300),
            description=_构建待办描述(collection),
            tags=_规范化标签名称([*(collection.tags or []), "收藏"]),
        ),
    )
    await db.flush()
    return 收藏转换结果(
        collection_id=collection.id,
        target_type="todo",
        target_id=todo.id,
        message="已生成待办事项",
    )
