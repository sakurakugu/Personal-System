"""统计相关 MCP 只读工具。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.articles.models import 文章
from app.modules.materials.models import 资料
from app.modules.files.models import File
from app.modules.media.models import 文娱条目
from app.modules.memos.models import 备忘录
from app.modules.moments.models import 动态
from app.modules.stats.models import PageView
from app.modules.stats.service import 获取博客统计
from app.modules.todos.models import Todo, TodoCompletionEvent

统计活动模块 = Literal[
    "articles",
    "moments",
    "materials",
    "memos",
    "todos",
    "files",
    "media",
    "page_views",
    "todo_completions",
]

默认活动模块: list[统计活动模块] = [
    "articles",
    "moments",
    "materials",
    "memos",
    "todos",
    "files",
    "media",
    "page_views",
    "todo_completions",
]


class 统计活动趋势参数(BaseModel):
    """统计活动趋势查询参数。"""

    start_date: date | None = Field(default=None, description="开始日期，默认最近 7 天")
    end_date: date | None = Field(default=None, description="结束日期，默认今天")
    modules: list[统计活动模块] | None = Field(default=None, description="要统计的模块列表，默认全部")


def _获取MCP会话(context: MCP调用上下文) -> AsyncSession:
    """获取当前 MCP 运行时数据库会话。"""
    if context.db is None:
        raise RuntimeError("MCP 工具缺少数据库会话")
    return context.db


def _枚举值(value: Any) -> Any:
    """将枚举值转为可 JSON 序列化的原始值。"""
    return value.value if hasattr(value, "value") else value


def _当天开始(value: date) -> datetime:
    """将日期转为 UTC 当天开始时间。"""
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _校验日期范围(start_date: date, end_date: date) -> None:
    """校验统计查询日期范围。"""
    if end_date < start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="结束日期不能早于开始日期")
    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="查询区间不能超过 366 天")


def _日期列表(start_date: date, end_date: date) -> list[date]:
    """生成闭区间日期列表。"""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def _构建活动趋势响应(
    aggregates: dict[统计活动模块, dict[date, int]],
    *,
    start_date: date,
    end_date: date,
    modules: list[统计活动模块],
) -> dict[str, Any]:
    """根据聚合结果构建补零后的活动趋势响应。"""
    days = _日期列表(start_date, end_date)
    totals = {
        module: sum(aggregates.get(module, {}).get(day, 0) for day in days)
        for module in modules
    }
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "modules": modules,
        "totals": totals,
        "days": [
            {
                "date": day.isoformat(),
                "counts": {
                    module: aggregates.get(module, {}).get(day, 0)
                    for module in modules
                },
            }
            for day in days
        ],
    }


async def _统计数量(db: AsyncSession, statement: Any) -> int:
    """执行 count 查询并返回整数。"""
    return int((await db.execute(statement)).scalar() or 0)


async def _按状态统计(db: AsyncSession, statement: Any) -> dict[str, int]:
    """执行状态分组统计。"""
    result = await db.execute(statement)
    return {str(_枚举值(status_value)): int(count_value or 0) for status_value, count_value in result}


async def _按日期统计(db: AsyncSession, statement: Any) -> dict[date, int]:
    """执行日期分组统计。"""
    result = await db.execute(statement)
    return {occurred_on: int(count_value or 0) for occurred_on, count_value in result if occurred_on is not None}


async def stats_blog_overview(_args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取博客概览统计。"""
    stats = await 获取博客统计(_获取MCP会话(context), user=context.user)
    data = stats.model_dump(mode="json")
    return {
        "summary": "已读取博客概览统计",
        "scope": "authenticated",
        "data": data,
    }


async def stats_content_overview(_args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """汇总当前用户内容数量。"""
    db = _获取MCP会话(context)
    user_id = context.user.id

    article_status = await _按状态统计(
        db,
        select(文章.status.label("status"), func.count(文章.id).label("count"))
        .where(文章.author_id == user_id, 文章.is_deleted.is_(False))
        .group_by(文章.status),
    )
    todo_status = await _按状态统计(
        db,
        select(Todo.status.label("status"), func.count(Todo.id).label("count"))
        .where(Todo.user_id == user_id, Todo.is_deleted.is_(False))
        .group_by(Todo.status),
    )
    memo_status = await _按状态统计(
        db,
        select(备忘录.status.label("status"), func.count(备忘录.id).label("count"))
        .where(备忘录.user_id == user_id, 备忘录.deleted_at.is_(None))
        .group_by(备忘录.status),
    )
    material_status = await _按状态统计(
        db,
        select(资料.status.label("status"), func.count(资料.id).label("count"))
        .where(资料.user_id == user_id, 资料.is_deleted.is_(False))
        .group_by(资料.status),
    )

    modules = {
        "articles": {
            "total": await _统计数量(db, select(func.count(文章.id)).where(文章.author_id == user_id)),
            "active": sum(article_status.values()),
            "deleted": await _统计数量(
                db,
                select(func.count(文章.id)).where(文章.author_id == user_id, 文章.is_deleted.is_(True)),
            ),
            "by_status": article_status,
        },
        "moments": {
            "total": await _统计数量(db, select(func.count(动态.id)).where(动态.user_id == user_id)),
            "active": await _统计数量(
                db,
                select(func.count(动态.id)).where(动态.user_id == user_id, 动态.is_deleted.is_(False)),
            ),
            "deleted": await _统计数量(
                db,
                select(func.count(动态.id)).where(动态.user_id == user_id, 动态.is_deleted.is_(True)),
            ),
            "published": await _统计数量(
                db,
                select(func.count(动态.id)).where(
                    动态.user_id == user_id,
                    动态.is_deleted.is_(False),
                    动态.is_published.is_(True),
                ),
            ),
            "draft": await _统计数量(
                db,
                select(func.count(动态.id)).where(
                    动态.user_id == user_id,
                    动态.is_deleted.is_(False),
                    动态.is_published.is_(False),
                ),
            ),
        },
        "materials": {
            "total": await _统计数量(db, select(func.count(资料.id)).where(资料.user_id == user_id)),
            "active": sum(material_status.values()),
            "deleted": await _统计数量(
                db,
                select(func.count(资料.id)).where(资料.user_id == user_id, 资料.is_deleted.is_(True)),
            ),
            "by_status": material_status,
        },
        "memos": {
            "total": await _统计数量(db, select(func.count(备忘录.id)).where(备忘录.user_id == user_id)),
            "active": sum(memo_status.values()),
            "deleted": await _统计数量(
                db,
                select(func.count(备忘录.id)).where(备忘录.user_id == user_id, 备忘录.deleted_at.is_not(None)),
            ),
            "by_status": memo_status,
        },
        "todos": {
            "total": await _统计数量(db, select(func.count(Todo.id)).where(Todo.user_id == user_id)),
            "active": sum(todo_status.values()),
            "deleted": await _统计数量(
                db,
                select(func.count(Todo.id)).where(Todo.user_id == user_id, Todo.is_deleted.is_(True)),
            ),
            "by_status": todo_status,
        },
        "files": {
            "total": await _统计数量(db, select(func.count(File.id)).where(File.user_id == user_id)),
            "total_size": await _统计数量(
                db,
                select(func.coalesce(func.sum(File.size), 0)).where(File.user_id == user_id),
            ),
        },
        "media": {
            "total": await _统计数量(db, select(func.count(文娱条目.id)).where(文娱条目.user_id == user_id)),
            "active": await _统计数量(
                db,
                select(func.count(文娱条目.id)).where(文娱条目.user_id == user_id, 文娱条目.is_deleted.is_(False)),
            ),
            "deleted": await _统计数量(
                db,
                select(func.count(文娱条目.id)).where(文娱条目.user_id == user_id, 文娱条目.is_deleted.is_(True)),
            ),
        },
    }
    return {
        "summary": "已读取内容概览统计",
        "user_id": str(user_id),
        "modules": modules,
    }


async def stats_activity_trend(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """按时间范围读取当前用户活动趋势。"""
    body = 统计活动趋势参数.model_validate(args)
    today = datetime.now(timezone.utc).date()
    end_date = body.end_date or today
    start_date = body.start_date or (end_date - timedelta(days=6))
    _校验日期范围(start_date, end_date)

    modules = body.modules or 默认活动模块
    db = _获取MCP会话(context)
    user_id = context.user.id
    start_at = _当天开始(start_date)
    end_at = _当天开始(end_date + timedelta(days=1))

    aggregates: dict[统计活动模块, dict[date, int]] = {}
    if "articles" in modules:
        aggregates["articles"] = await _按日期统计(
            db,
            select(cast(文章.created_at, Date).label("occurred_on"), func.count(文章.id).label("count"))
            .where(文章.author_id == user_id, 文章.created_at >= start_at, 文章.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "moments" in modules:
        aggregates["moments"] = await _按日期统计(
            db,
            select(cast(动态.created_at, Date).label("occurred_on"), func.count(动态.id).label("count"))
            .where(动态.user_id == user_id, 动态.created_at >= start_at, 动态.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "materials" in modules:
        aggregates["materials"] = await _按日期统计(
            db,
            select(cast(资料.created_at, Date).label("occurred_on"), func.count(资料.id).label("count"))
            .where(资料.user_id == user_id, 资料.created_at >= start_at, 资料.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "memos" in modules:
        aggregates["memos"] = await _按日期统计(
            db,
            select(cast(备忘录.created_at, Date).label("occurred_on"), func.count(备忘录.id).label("count"))
            .where(备忘录.user_id == user_id, 备忘录.created_at >= start_at, 备忘录.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "todos" in modules:
        aggregates["todos"] = await _按日期统计(
            db,
            select(cast(Todo.created_at, Date).label("occurred_on"), func.count(Todo.id).label("count"))
            .where(Todo.user_id == user_id, Todo.created_at >= start_at, Todo.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "files" in modules:
        aggregates["files"] = await _按日期统计(
            db,
            select(cast(File.created_at, Date).label("occurred_on"), func.count(File.id).label("count"))
            .where(File.user_id == user_id, File.created_at >= start_at, File.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "media" in modules:
        aggregates["media"] = await _按日期统计(
            db,
            select(cast(文娱条目.created_at, Date).label("occurred_on"), func.count(文娱条目.id).label("count"))
            .where(文娱条目.user_id == user_id, 文娱条目.created_at >= start_at, 文娱条目.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "page_views" in modules:
        aggregates["page_views"] = await _按日期统计(
            db,
            select(cast(PageView.created_at, Date).label("occurred_on"), func.count(PageView.id).label("count"))
            .join(文章, PageView.article_id == 文章.id)
            .where(文章.author_id == user_id, PageView.created_at >= start_at, PageView.created_at < end_at)
            .group_by("occurred_on"),
        )
    if "todo_completions" in modules:
        aggregates["todo_completions"] = await _按日期统计(
            db,
            select(TodoCompletionEvent.occurred_on.label("occurred_on"), func.sum(TodoCompletionEvent.delta).label("count"))
            .where(
                TodoCompletionEvent.user_id == user_id,
                TodoCompletionEvent.occurred_on >= start_date,
                TodoCompletionEvent.occurred_on <= end_date,
            )
            .group_by(TodoCompletionEvent.occurred_on),
        )

    return {
        "summary": "已读取活动趋势统计",
        **_构建活动趋势响应(
            aggregates,
            start_date=start_date,
            end_date=end_date,
            modules=modules,
        ),
    }


注册工具(
    MCP工具定义(
        name="stats.blog_overview",
        description="读取博客概览统计，返回文章、分类、标签、字数和最近发布时间。",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        permission="readonly",
        handler=stats_blog_overview,
    )
)
注册工具(
    MCP工具定义(
        name="stats.content_overview",
        description="汇总当前用户文章、动态、资料库、备忘录、待办、文件和文娱条目的数量。",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        permission="readonly",
        handler=stats_content_overview,
    )
)
注册工具(
    MCP工具定义(
        name="stats.activity_trend",
        description="按日期范围读取当前用户活动趋势，返回每日各模块计数。",
        input_schema=统计活动趋势参数.model_json_schema(),
        permission="readonly",
        handler=stats_activity_trend,
    )
)
