"""统计模块服务。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Date, Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.modules.articles.models import 文章, 文章状态
from app.modules.users.models import 用户
from app.modules.stats.models import PageView
from app.modules.stats.schemas import (
    博客统计,
    仪表盘统计,
    页面浏览记录请求,
    待办完成历史日信息,
    待办完成历史项信息,
    待办完成历史信息,
)
from app.modules.bills.service import 获取账单月度汇总
from app.modules.todos.models import Todo, TodoCompletionEvent

_BLOG_STATS_CACHE_KEY = "stats:blog"
_BLOG_STATS_CACHE_TTL = 300


def 迭代日期(start_date: date, end_date: date) -> list[date]:
    """生成闭区间日期列表。"""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def 哈希客户端IP(ip: str) -> str:
    """对 IP 进行稳定哈希。"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class 待办完成聚合记录:
    """待办完成历史聚合结果。"""

    occurred_on: date
    todo_id: UUID
    title: str
    completed_count: int
    normalized_score: float


@dataclass(frozen=True, slots=True)
class 近期访问聚合记录:
    """最近访问趋势聚合结果。"""

    viewed_on: date
    count: int


def _限制单个待办单日得分(score: float) -> float:
    """将单个待办单日得分限制在 0 到 1 之间。"""
    return round(min(max(score, 0.0), 1.0), 4)


def _构建博客统计可见文章条件(user: 用户 | None):
    """构建博客统计的文章可见性条件。"""
    deleted_clause = 文章.is_deleted.is_(False)
    if user is None:
        return deleted_clause & (文章.status == 文章状态.public)
    return deleted_clause & 文章.status.in_((文章状态.public, 文章状态.login_required))


def _构建最近访问趋势(
    aggregates: Iterable[近期访问聚合记录],
    *,
    start_date: date,
    end_date: date,
) -> list[dict[str, int | str]]:
    """根据聚合结果构建补零后的访问趋势。"""
    counts_by_date = {row.viewed_on: row.count for row in aggregates}
    return [
        {
            "date": current_day.isoformat(),
            "count": counts_by_date.get(current_day, 0),
        }
        for current_day in 迭代日期(start_date, end_date)
    ]


def _构建待办完成历史响应(
    aggregates: list[待办完成聚合记录],
    *,
    start_date: date,
    end_date: date,
) -> 待办完成历史信息:
    """根据聚合结果构建待办完成历史响应。"""
    grouped: dict[date, list[待办完成历史项信息]] = {}
    for row in aggregates:
        normalized_score = _限制单个待办单日得分(row.normalized_score)
        if row.completed_count <= 0 or normalized_score <= 0:
            continue
        item = 待办完成历史项信息(
            todo_id=row.todo_id,
            title=row.title,
            completed_count=row.completed_count,
            normalized_score=normalized_score,
        )
        grouped.setdefault(row.occurred_on, []).append(item)

    days: list[待办完成历史日信息] = []
    max_completed_count = 0
    total_completed_count = 0
    max_score = 0.0
    total_score = 0.0

    for current_day in 迭代日期(start_date, end_date):
        items = grouped.get(current_day, [])
        completed_count = sum(item.completed_count for item in items)
        score = round(sum(item.normalized_score for item in items), 4)
        max_completed_count = max(max_completed_count, completed_count)
        total_completed_count += completed_count
        max_score = max(max_score, score)
        total_score = round(total_score + score, 4)
        days.append(
            待办完成历史日信息(
                date=current_day,
                completed_count=completed_count,
                score=score,
                items=items,
            )
        )

    return 待办完成历史信息(
        start_date=start_date,
        end_date=end_date,
        max_completed_count=max_completed_count,
        total_completed_count=total_completed_count,
        max_score=max_score,
        total_score=total_score,
        days=days,
    )


async def 清除博客统计缓存() -> None:
    """清除博客站点统计缓存。"""
    redis = await get_redis()
    await redis.delete(f"{_BLOG_STATS_CACHE_KEY}:anonymous", f"{_BLOG_STATS_CACHE_KEY}:authenticated")


def _博客统计缓存键(user: 用户 | None) -> str:
    """根据登录态生成博客统计缓存键。"""
    suffix = "authenticated" if user is not None else "anonymous"
    return f"{_BLOG_STATS_CACHE_KEY}:{suffix}"


async def 获取博客统计(db: AsyncSession, *, user: 用户 | None) -> 博客统计:
    """获取博客站点统计。"""
    from app.modules.articles.models import 分类, 标签, 文章标签

    redis = await get_redis()
    cache_key = _博客统计缓存键(user)
    cached = await redis.get(cache_key)
    if cached:
        return 博客统计.model_validate_json(cached)

    visible_article_clause = _构建博客统计可见文章条件(user)

    total_articles = (
        await db.execute(
            select(func.count()).where(
                visible_article_clause
            )
        )
    ).scalar() or 0
    total_categories = (
        await db.execute(
            select(func.count(func.distinct(分类.id)))
            .select_from(文章)
            .join(分类, 文章.category_id == 分类.id)
            .where(visible_article_clause)
        )
    ).scalar() or 0
    total_tags = (
        await db.execute(
            select(func.count(func.distinct(标签.id)))
            .select_from(文章)
            .join(文章标签, 文章标签.article_id == 文章.id)
            .join(标签, 标签.id == 文章标签.tag_id)
            .where(visible_article_clause)
        )
    ).scalar() or 0

    total_words = (
        await db.execute(
            select(func.coalesce(func.sum(文章.word_count), 0)).where(
                visible_article_clause
            )
        )
    ).scalar() or 0

    last_published = (
        await db.execute(
            select(func.max(文章.published_at)).where(
                visible_article_clause
            )
        )
    ).scalar()

    result = 博客统计(
        total_articles=total_articles,
        total_categories=total_categories,
        total_tags=total_tags,
        total_words=total_words,
        last_published_at=last_published,
    )

    await redis.setex(
        cache_key,
        _BLOG_STATS_CACHE_TTL,
        result.model_dump_json(),
    )
    return result


async def 获取仪表盘统计(db: AsyncSession, user: 用户) -> 仪表盘统计:
    """获取用户仪表板统计。"""
    total_articles = (await db.execute(select(func.count()).where(文章.author_id == user.id))).scalar() or 0
    total_views = (
        await db.execute(select(func.coalesce(func.sum(文章.view_count), 0)).where(文章.author_id == user.id))
    ).scalar() or 0
    total_todos = (await db.execute(select(func.count()).where(Todo.user_id == user.id))).scalar() or 0

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=6)
    start_at = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    recent = await db.execute(
        select(
            cast(PageView.created_at, Date).label("viewed_on"),
            func.count(PageView.id).label("view_count"),
        )
        .join(文章, PageView.article_id == 文章.id)
        .where(
            文章.author_id == user.id,
            PageView.created_at >= start_at,
        )
        .group_by("viewed_on")
        .order_by("viewed_on")
    )
    recent_views = _构建最近访问趋势(
        [
            近期访问聚合记录(
                viewed_on=row.viewed_on,
                count=int(row.view_count),
            )
            for row in recent
        ],
        start_date=start_date,
        end_date=today,
    )
    bill_summary = await 获取账单月度汇总(db, user, month=None)

    return 仪表盘统计(
        total_articles=total_articles,
        total_views=total_views,
        total_todos=total_todos,
        current_month_bill_income_cent=bill_summary.income_cent,
        current_month_bill_expense_cent=bill_summary.expense_cent,
        current_month_bill_net_cent=bill_summary.net_cent,
        current_month_bill_record_count=bill_summary.record_count,
        recent_views=recent_views,
    )


async def 获取待办完成历史(
    db: AsyncSession,
    *,
    user: 用户,
    start_date: date,
    end_date: date,
) -> 待办完成历史信息:
    """获取待办完成历史。"""
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="结束日期不能早于开始日期")
    if (end_date - start_date).days > 800:
        raise HTTPException(status_code=422, detail="查询区间不能超过 800 天")

    result = await db.execute(
        select(
            TodoCompletionEvent.occurred_on.label("occurred_on"),
            TodoCompletionEvent.todo_id.label("todo_id"),
            TodoCompletionEvent.todo_title_snapshot.label("title"),
            func.sum(TodoCompletionEvent.delta).label("completed_count"),
            func.sum(TodoCompletionEvent.delta / cast(TodoCompletionEvent.target_count_snapshot, Float)).label(
                "normalized_score"
            ),
        )
        .where(
            TodoCompletionEvent.user_id == user.id,
            TodoCompletionEvent.occurred_on >= start_date,
            TodoCompletionEvent.occurred_on <= end_date,
        )
        .group_by(
            TodoCompletionEvent.occurred_on,
            TodoCompletionEvent.todo_id,
            TodoCompletionEvent.todo_title_snapshot,
        )
        .having(func.sum(TodoCompletionEvent.delta) > 0)
        .order_by(TodoCompletionEvent.occurred_on.asc(), TodoCompletionEvent.todo_title_snapshot.asc())
    )

    aggregates = [
        待办完成聚合记录(
            occurred_on=row.occurred_on,
            todo_id=row.todo_id,
            title=row.title,
            completed_count=int(row.completed_count),
            normalized_score=float(row.normalized_score or 0),
        )
        for row in result
    ]

    return _构建待办完成历史响应(
        aggregates,
        start_date=start_date,
        end_date=end_date,
    )


async def 记录页面浏览(
    db: AsyncSession,
    *,
    body: 页面浏览记录请求,
    client_ip: str,
    user_agent: str,
) -> None:
    """记录页面访问。"""
    page_view = PageView(
        path=body.path,
        article_id=body.article_id,
        ip_hash=哈希客户端IP(client_ip),
        user_agent=user_agent[:500],
    )
    db.add(page_view)


__all__ = [
    "_BLOG_STATS_CACHE_KEY",
    "_BLOG_STATS_CACHE_TTL",
    "_构建待办完成历史响应",
    "_构建最近访问趋势",
    "_构建博客统计可见文章条件",
    "_限制单个待办单日得分",
    "博客统计",
    "仪表盘统计",
    "页面浏览记录请求",
    "待办完成历史信息",
    "获取博客统计",
    "获取仪表盘统计",
    "获取待办完成历史",
    "哈希客户端IP",
    "清除博客统计缓存",
    "迭代日期",
    "记录页面浏览",
    "待办完成聚合记录",
    "近期访问聚合记录",
]
