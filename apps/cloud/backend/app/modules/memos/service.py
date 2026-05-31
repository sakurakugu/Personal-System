"""备忘录模块服务。"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.crud import 创建文章草稿
from app.modules.articles.schemas import 文章草稿创建
from app.modules.collections.schemas import 收藏创建
from app.modules.collections.service import 创建收藏
from app.modules.memos.models import 备忘录, 备忘录来源, 备忘录状态
from app.modules.memos.schemas import 备忘录创建, 备忘录信息, 备忘录更新, 备忘录转换结果
from app.modules.todos.schemas import TodoCreate
from app.modules.todos.service import create_todo
from app.modules.users.models import 用户
from app.shared.kernel.pagination import PaginatedResponse

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def 解析备忘录状态(value: str) -> 备忘录状态:
    """解析备忘录状态。"""
    try:
        return 备忘录状态(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的备忘录状态") from exc


def 解析备忘录来源(value: str) -> 备忘录来源:
    """解析备忘录来源。"""
    try:
        return 备忘录来源(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的备忘录来源") from exc


def 构建备忘录读取(memo: 备忘录) -> 备忘录信息:
    """构造备忘录详情响应。"""
    return 备忘录信息(
        id=memo.id,
        content=memo.content,
        status=memo.status.value,
        source=memo.source.value,
        converted_to_type=memo.converted_to_type,
        converted_to_id=memo.converted_to_id,
        archived_at=memo.archived_at,
        deleted_at=memo.deleted_at,
        created_at=memo.created_at,
        updated_at=memo.updated_at,
    )


def _truncate_text(value: str, length: int) -> str:
    """按长度截断文本。"""
    if len(value) <= length:
        return value
    if length <= 1:
        return value[:length]
    return f"{value[: length - 1]}…"


def 提取备忘录标题(content: str, *, fallback: str = "未命名备忘录", max_length: int = 80) -> str:
    """从备忘录正文首个非空行提取标题。"""
    for line in content.splitlines():
        normalized = line.strip()
        if normalized:
            return _truncate_text(normalized, max_length)
    return fallback


def 提取备忘录链接(content: str) -> str | None:
    """从备忘录正文中提取第一个链接。"""
    match = URL_PATTERN.search(content)
    return match.group(0) if match else None


def 应用备忘录状态(memo: 备忘录, status: 备忘录状态, *, now: datetime | None = None) -> None:
    """同步备忘录状态时间字段。"""
    memo.status = status
    if status == 备忘录状态.archived:
        memo.archived_at = memo.archived_at or (now or utcnow())
        memo.deleted_at = None
        return
    if status == 备忘录状态.dropped:
        current_time = now or utcnow()
        memo.archived_at = None
        memo.deleted_at = memo.deleted_at or current_time
        return
    memo.archived_at = None
    memo.deleted_at = None


def 应用备忘录删除状态(memo: 备忘录, *, now: datetime | None = None) -> None:
    """将备忘录标记为废弃。"""
    应用备忘录状态(memo, 备忘录状态.dropped, now=now)


def 恢复备忘录删除状态(memo: 备忘录) -> None:
    """恢复废弃备忘录。"""
    memo.status = 备忘录状态.inbox
    memo.archived_at = None
    memo.deleted_at = None


def 标记备忘录已转换(memo: 备忘录, target_type: str, target_id: UUID, *, now: datetime | None = None) -> None:
    """记录备忘录转出目标。"""
    应用备忘录状态(memo, 备忘录状态.processed, now=now)
    memo.converted_to_type = target_type
    memo.converted_to_id = target_id


def _构建关键词条件(keyword: str):
    """构造关键词搜索条件。"""
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return None
    like_keyword = f"%{normalized_keyword}%"
    return or_(备忘录.content.ilike(like_keyword), 备忘录.converted_to_type.ilike(like_keyword))


async def 列出备忘录(
    db: AsyncSession,
    user: 用户,
    *,
    page: int,
    page_size: int,
    status: str | None,
    source: str | None,
    keyword: str | None,
    is_deleted: bool,
) -> PaginatedResponse:
    """获取当前用户的备忘录列表。"""
    query = select(备忘录).where(备忘录.user_id == user.id)
    if is_deleted:
        query = query.where(备忘录.deleted_at.is_not(None))
    else:
        query = query.where(备忘录.deleted_at.is_(None))

    if status:
        query = query.where(备忘录.status == 解析备忘录状态(status))
    if source:
        query = query.where(备忘录.source == 解析备忘录来源(source))
    if keyword:
        keyword_clause = _构建关键词条件(keyword)
        if keyword_clause is not None:
            query = query.where(keyword_clause)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    primary_order_column = 备忘录.deleted_at.desc() if is_deleted else 备忘录.updated_at.desc()
    result = await db.execute(
        query.order_by(primary_order_column, 备忘录.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return PaginatedResponse(
        items=[构建备忘录读取(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_memo_or_404(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录:
    """读取当前用户的单条备忘录。"""
    result = await db.execute(
        select(备忘录).where(
            备忘录.id == memo_id,
            备忘录.user_id == user.id,
            备忘录.deleted_at.is_(None),
        )
    )
    memo = result.scalar_one_or_none()
    if memo is None:
        raise HTTPException(status_code=404, detail="备忘录不存在")
    return memo


async def 获取已删备忘录或404(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录:
    """读取当前用户回收站中的备忘录。"""
    result = await db.execute(
        select(备忘录).where(
            备忘录.id == memo_id,
            备忘录.user_id == user.id,
            备忘录.deleted_at.is_not(None),
        )
    )
    memo = result.scalar_one_or_none()
    if memo is None:
        raise HTTPException(status_code=404, detail="备忘录不存在或未被删除")
    return memo


async def 创建备忘录(db: AsyncSession, user: 用户, body: 备忘录创建) -> 备忘录信息:
    """创建备忘录。"""
    memo = 备忘录(
        user_id=user.id,
        content=body.content,
        source=解析备忘录来源(body.source),
    )
    db.add(memo)
    await db.flush()
    return 构建备忘录读取(memo)


async def 更新备忘录(db: AsyncSession, user: 用户, memo_id: str, body: 备忘录更新) -> 备忘录信息:
    """更新备忘录。"""
    memo = await get_memo_or_404(db, user, memo_id)
    data = body.model_dump(exclude_unset=True)
    status_value = data.pop("status", None)
    source_value = data.pop("source", None)

    for key, value in data.items():
        setattr(memo, key, value)

    if source_value is not None:
        memo.source = 解析备忘录来源(source_value)
    if status_value is not None:
        应用备忘录状态(memo, 解析备忘录状态(status_value))

    await db.flush()
    return 构建备忘录读取(memo)


async def 删除备忘录(db: AsyncSession, user: 用户, memo_id: str, *, permanent: bool) -> None:
    """删除备忘录。"""
    if permanent:
        memo = await 获取已删备忘录或404(db, user, memo_id)
        await db.delete(memo)
        return

    memo = await get_memo_or_404(db, user, memo_id)
    应用备忘录删除状态(memo)
    await db.flush()


async def 恢复备忘录(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录信息:
    """从回收站恢复备忘录。"""
    memo = await 获取已删备忘录或404(db, user, memo_id)
    恢复备忘录删除状态(memo)
    await db.flush()
    return 构建备忘录读取(memo)


async def 转换备忘录为资料(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录转换结果:
    """将备忘录转换为资料库资料。"""
    memo = await get_memo_or_404(db, user, memo_id)
    content = memo.content
    url = 提取备忘录链接(content)
    collection = await 创建收藏(
        db,
        user,
        收藏创建(
            type="link" if url else "text",
            title=提取备忘录标题(content, fallback="未命名资料", max_length=80),
            content_text=url if url else content,
            note=content,
            status="inbox",
            tags=None,
            assets=None,
        ),
    )
    标记备忘录已转换(memo, "collection", collection.id)
    await db.flush()
    return 备忘录转换结果(
        memo_id=memo.id,
        target_type="collection",
        target_id=collection.id,
        message="已转入资料库",
    )


async def 转换备忘录为文章(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录转换结果:
    """将备忘录转换为文章草稿。"""
    memo = await get_memo_or_404(db, user, memo_id)
    article = await 创建文章草稿(
        db,
        文章草稿创建(
            title=提取备忘录标题(memo.content, fallback="未命名文章", max_length=120),
            content=memo.content,
            excerpt=_truncate_text(memo.content, 500),
            cover_url=None,
        ),
        user,
    )
    标记备忘录已转换(memo, "article", article.id)
    await db.flush()
    return 备忘录转换结果(
        memo_id=memo.id,
        target_type="article",
        target_id=article.id,
        message="已生成文章草稿",
    )


async def 转换备忘录为待办(db: AsyncSession, user: 用户, memo_id: str) -> 备忘录转换结果:
    """将备忘录转换为待办。"""
    memo = await get_memo_or_404(db, user, memo_id)
    todo = await create_todo(
        db,
        user,
        TodoCreate(
            title=提取备忘录标题(memo.content, fallback="未命名待办", max_length=300),
            description=memo.content,
            tags=["备忘录"],
        ),
    )
    标记备忘录已转换(memo, "todo", todo.id)
    await db.flush()
    return 备忘录转换结果(
        memo_id=memo.id,
        target_type="todo",
        target_id=todo.id,
        message="已生成待办事项",
    )
