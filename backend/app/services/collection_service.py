"""收藏模块服务。"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collection import (
    Collection,
    CollectionAsset,
    CollectionStatus,
    CollectionTag,
    CollectionTagRelation,
    CollectionType,
)
from app.models.file import File, FilePurpose
from app.models.moment import Moment
from app.models.user import User
from app.schemas.article import ArticleDraftCreate
from app.schemas.collection import (
    CollectionAssetInput,
    CollectionAssetRead,
    CollectionBatchStatusUpdate,
    CollectionConvertResult,
    CollectionCreate,
    CollectionRead,
    CollectionTagRead,
    CollectionUpdate,
)
from app.schemas.file import FileRead
from app.schemas.shared import PaginatedResponse
from app.schemas.todo import TodoCreate
from app.services.articles.crud import create_article_draft
from app.services.file_service import build_file_read
from app.services.todo_service import create_todo


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def collection_query():
    """构建收藏详情查询。"""
    return (
        select(Collection)
        .options(
            selectinload(Collection.assets).selectinload(CollectionAsset.file),
            selectinload(Collection.collection_tags),
        )
    )


def parse_collection_type(value: str) -> CollectionType:
    """解析收藏类型。"""
    try:
        return CollectionType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的收藏类型") from exc


def parse_collection_status(value: str) -> CollectionStatus:
    """解析收藏状态。"""
    try:
        return CollectionStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的收藏状态") from exc


def build_collection_asset_read(asset: CollectionAsset) -> CollectionAssetRead:
    """构造收藏附件响应。"""
    if asset.file is None:
        raise HTTPException(status_code=500, detail="收藏附件数据不完整")
    return CollectionAssetRead(
        id=asset.id,
        file_id=asset.file_id,
        sort_order=asset.sort_order,
        created_at=asset.created_at,
        file=FileRead.model_validate(build_file_read(asset.file)),
    )


def build_collection_read(collection: Collection) -> CollectionRead:
    """构造收藏详情响应。"""
    return CollectionRead(
        id=collection.id,
        type=collection.type.value,
        title=collection.title,
        content_text=collection.content_text,
        note=collection.note,
        status=collection.status.value,
        tags=collection.tags,
        assets=[build_collection_asset_read(asset) for asset in collection.assets],
        archived_at=collection.archived_at,
        is_deleted=collection.is_deleted,
        deleted_at=collection.deleted_at,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def apply_archived_state(collection: Collection, status: CollectionStatus, *, now: datetime | None = None) -> None:
    """同步归档时间。"""
    collection.status = status
    if status == CollectionStatus.archived:
        collection.archived_at = collection.archived_at or (now or utcnow())
        return
    collection.archived_at = None


def apply_collection_deleted_state(collection: Collection, *, now: datetime | None = None) -> None:
    """将收藏标记为已删除。"""
    collection.is_deleted = True
    collection.deleted_at = now or utcnow()


def restore_collection_deleted_state(collection: Collection) -> None:
    """恢复收藏的删除状态。"""
    collection.is_deleted = False
    collection.deleted_at = None


def _normalize_tag_names(tag_names: list[str] | None) -> list[str]:
    """返回去重后的标签列表。"""
    if not tag_names:
        return []
    return list(dict.fromkeys(tag_names))


async def _ensure_collection_tags_loaded(db: AsyncSession, collection: Collection) -> None:
    """确保收藏标签已加载。"""
    if "collection_tags" in inspect(collection).unloaded:
        await db.refresh(collection, attribute_names=["collection_tags"])


async def _ensure_collection_assets_loaded(db: AsyncSession, collection: Collection) -> None:
    """确保收藏附件已加载。"""
    if "assets" in inspect(collection).unloaded:
        await db.refresh(collection, attribute_names=["assets"])


async def _get_user_tags_by_names(db: AsyncSession, user_id: UUID, tag_names: list[str]) -> dict[str, CollectionTag]:
    """按名称读取用户收藏标签。"""
    if not tag_names:
        return {}

    result = await db.execute(
        select(CollectionTag).where(
            CollectionTag.user_id == user_id,
            CollectionTag.name.in_(tag_names),
        )
    )
    tags = result.scalars().all()
    return {tag.name: tag for tag in tags}


async def _sync_collection_tags(db: AsyncSession, collection: Collection, tag_names: list[str] | None) -> None:
    """同步收藏标签。"""
    await _ensure_collection_tags_loaded(db, collection)
    normalized_names = _normalize_tag_names(tag_names)
    if not normalized_names:
        collection.collection_tags = []
        return

    existing_tags = await _get_user_tags_by_names(db, collection.user_id, normalized_names)
    resolved_tags: list[CollectionTag] = []
    for name in normalized_names:
        tag = existing_tags.get(name)
        if tag is None:
            tag = CollectionTag(user_id=collection.user_id, name=name)
            db.add(tag)
            await db.flush()
            existing_tags[name] = tag
        resolved_tags.append(tag)

    collection.collection_tags = resolved_tags


async def _get_user_files_by_ids(db: AsyncSession, user: User, file_ids: list[UUID]) -> dict[UUID, File]:
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


async def _sync_collection_assets(
    db: AsyncSession,
    collection: Collection,
    user: User,
    assets: list[CollectionAssetInput] | None,
) -> None:
    """同步收藏附件。"""
    await _ensure_collection_assets_loaded(db, collection)
    if not assets:
        collection.assets = []
        return

    deduplicated_assets: list[CollectionAssetInput] = []
    seen_file_ids: set[UUID] = set()
    for asset in assets:
        if asset.file_id in seen_file_ids:
            continue
        seen_file_ids.add(asset.file_id)
        deduplicated_assets.append(asset)

    file_map = await _get_user_files_by_ids(db, user, [asset.file_id for asset in deduplicated_assets])
    collection.assets = [
        CollectionAsset(
            file_id=asset.file_id,
            sort_order=asset.sort_order,
            file=file_map[asset.file_id],
        )
        for asset in deduplicated_assets
    ]


def _build_keyword_clause(keyword: str):
    """构造关键词搜索条件。"""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return None
    like_keyword = f"%{normalized_keyword}%"
    return or_(
        Collection.title.ilike(like_keyword),
        Collection.content_text.ilike(like_keyword),
        Collection.note.ilike(like_keyword),
    )


async def list_collection_tags(db: AsyncSession, user: User, *, is_deleted: bool) -> list[CollectionTagRead]:
    """读取当前用户的收藏标签列表。"""
    result = await db.execute(
        select(
            CollectionTag.name,
            func.count(CollectionTagRelation.collection_id).label("count"),
        )
        .select_from(CollectionTag)
        .join(CollectionTagRelation, CollectionTagRelation.tag_id == CollectionTag.id)
        .join(Collection, Collection.id == CollectionTagRelation.collection_id)
        .where(CollectionTag.user_id == user.id, Collection.is_deleted == is_deleted)
        .group_by(CollectionTag.id, CollectionTag.name)
        .order_by(func.count(CollectionTagRelation.collection_id).desc(), CollectionTag.name.asc())
    )
    return [CollectionTagRead(name=row.name, count=row._mapping["count"]) for row in result]


async def list_collections(
    db: AsyncSession,
    user: User,
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
    query = select(Collection).where(Collection.user_id == user.id, Collection.is_deleted == is_deleted)

    if status:
        query = query.where(Collection.status == parse_collection_status(status))
    if collection_type:
        query = query.where(Collection.type == parse_collection_type(collection_type))
    if tag:
        query = query.where(Collection.collection_tags.any(CollectionTag.name == tag))
    if keyword:
        keyword_clause = _build_keyword_clause(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    primary_order_column = Collection.deleted_at.desc() if is_deleted else Collection.updated_at.desc()
    result = await db.execute(
        query.options(
            selectinload(Collection.assets).selectinload(CollectionAsset.file),
            selectinload(Collection.collection_tags),
        )
        .order_by(primary_order_column, Collection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().unique().all()
    return PaginatedResponse(
        items=[build_collection_read(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_collection_or_404(db: AsyncSession, user: User, collection_id: str) -> Collection:
    """读取当前用户的单条收藏。"""
    result = await db.execute(
        collection_query().where(
            Collection.id == collection_id,
            Collection.user_id == user.id,
            Collection.is_deleted.is_(False),
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return collection


async def get_deleted_collection_or_404(db: AsyncSession, user: User, collection_id: str) -> Collection:
    """读取当前用户回收站中的收藏。"""
    result = await db.execute(
        collection_query().where(
            Collection.id == collection_id,
            Collection.user_id == user.id,
            Collection.is_deleted.is_(True),
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail="收藏不存在或未被删除")
    return collection


async def create_collection(db: AsyncSession, user: User, body: CollectionCreate) -> CollectionRead:
    """创建收藏。"""
    current_time = utcnow()
    collection = Collection(
        user_id=user.id,
        type=parse_collection_type(body.type),
        title=body.title,
        content_text=body.content_text,
        note=body.note,
    )
    apply_archived_state(collection, parse_collection_status(body.status), now=current_time)
    db.add(collection)
    await db.flush()
    await _sync_collection_tags(db, collection, body.tags)
    await _sync_collection_assets(db, collection, user, body.assets)
    await db.flush()
    return build_collection_read(await get_collection_or_404(db, user, str(collection.id)))


async def update_collection(
    db: AsyncSession,
    user: User,
    collection_id: str,
    body: CollectionUpdate,
) -> CollectionRead:
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
        collection.type = parse_collection_type(type_value)
    if status_value is not None:
        apply_archived_state(collection, parse_collection_status(status_value))
    if "tags" in body.model_fields_set:
        await _sync_collection_tags(db, collection, tag_names)
    if "assets" in body.model_fields_set:
        await _sync_collection_assets(db, collection, user, assets)

    await db.flush()
    return build_collection_read(await get_collection_or_404(db, user, collection_id))


async def delete_collection(db: AsyncSession, user: User, collection_id: str, *, permanent: bool) -> None:
    """删除收藏。"""
    if permanent:
        collection = await get_deleted_collection_or_404(db, user, collection_id)
        await db.delete(collection)
        return

    collection = await get_collection_or_404(db, user, collection_id)
    apply_collection_deleted_state(collection)
    await db.flush()


async def restore_collection(db: AsyncSession, user: User, collection_id: str) -> CollectionRead:
    """从回收站恢复收藏。"""
    collection = await get_deleted_collection_or_404(db, user, collection_id)
    restore_collection_deleted_state(collection)
    await db.flush()
    return build_collection_read(await get_collection_or_404(db, user, collection_id))


async def batch_update_collection_status(
    db: AsyncSession,
    user: User,
    body: CollectionBatchStatusUpdate,
) -> int:
    """批量更新收藏状态。"""
    result = await db.execute(
        select(Collection).where(
            Collection.user_id == user.id,
            Collection.is_deleted.is_(False),
            Collection.id.in_(body.ids),
        )
    )
    collections = list(result.scalars().all())
    if len(collections) != len(set(body.ids)):
        raise HTTPException(status_code=404, detail="存在无效的收藏记录")

    next_status = parse_collection_status(body.status)
    current_time = utcnow()
    for collection in collections:
        apply_archived_state(collection, next_status, now=current_time)
    await db.flush()
    return len(collections)


def _get_collection_title(collection: Collection) -> str:
    """返回收藏的展示标题。"""
    if collection.title:
        return collection.title
    if collection.note:
        return _truncate_text(collection.note, 60)
    if collection.content_text:
        return _truncate_text(collection.content_text, 60)
    return "未命名收藏"


def _build_article_content(collection: Collection) -> str:
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


def _build_moment_draft_title(collection: Collection) -> str | None:
    """构造动态草稿标题。"""
    title = collection.title
    if title is None:
        return None
    return _truncate_text(title, 100)


def _build_moment_draft_content(collection: Collection) -> str:
    """构造动态草稿正文。"""
    parts: list[str] = []
    if collection.note:
        parts.append(collection.note)
    elif collection.content_text:
        parts.append(collection.content_text)

    content = "\n\n".join(part.strip() for part in parts if part.strip())
    if not content:
        content = _get_collection_title(collection)
    return _truncate_text(content, 1000)


def _build_todo_description(collection: Collection) -> str | None:
    """构造待办描述。"""
    parts: list[str] = []
    if collection.note:
        parts.append(f"备注：{collection.note}")
    if collection.content_text:
        parts.append(f"内容：{_truncate_text(collection.content_text, 500)}")
    description = "\n".join(parts).strip()
    return description or None


async def convert_collection_to_article(
    db: AsyncSession,
    user: User,
    collection_id: str,
) -> CollectionConvertResult:
    """将收藏转换为文章草稿。"""
    collection = await get_collection_or_404(db, user, collection_id)
    article = await create_article_draft(
        db,
        ArticleDraftCreate(
            title=_get_collection_title(collection),
            content=_build_article_content(collection),
            excerpt=_truncate_text(collection.note or _get_collection_title(collection), 500),
            cover_url=None,
        ),
        user,
    )
    await db.flush()
    return CollectionConvertResult(
        collection_id=collection.id,
        target_type="article",
        target_id=article.id,
        message="已生成文章草稿",
    )


async def convert_collection_to_moment_draft(
    db: AsyncSession,
    user: User,
    collection_id: str,
) -> CollectionConvertResult:
    """将收藏转换为动态草稿。"""
    collection = await get_collection_or_404(db, user, collection_id)
    result = await db.execute(
        select(Moment).where(
            Moment.user_id == user.id,
            Moment.is_published.is_(False),
        )
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        draft = Moment(
            user_id=user.id,
            title=_build_moment_draft_title(collection),
            content=_build_moment_draft_content(collection),
            is_published=False,
        )
        db.add(draft)
    else:
        draft.title = _build_moment_draft_title(collection)
        draft.content = _build_moment_draft_content(collection)
        draft.updated_at = utcnow()

    await db.flush()
    return CollectionConvertResult(
        collection_id=collection.id,
        target_type="moment_draft",
        target_id=draft.id,
        message="已写入动态草稿",
    )


async def convert_collection_to_todo(
    db: AsyncSession,
    user: User,
    collection_id: str,
) -> CollectionConvertResult:
    """将收藏转换为待办。"""
    collection = await get_collection_or_404(db, user, collection_id)
    todo = await create_todo(
        db,
        user,
        TodoCreate(
            title=_truncate_text(_get_collection_title(collection), 300),
            description=_build_todo_description(collection),
            tags=_normalize_tag_names([*(collection.tags or []), "收藏"]),
        ),
    )
    await db.flush()
    return CollectionConvertResult(
        collection_id=collection.id,
        target_type="todo",
        target_id=todo.id,
        message="已生成待办事项",
    )
