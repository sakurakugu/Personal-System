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
from app.modules.articles.models import Article, ArticleStatus
from app.models.comment import Comment
from app.models.todo import Todo, TodoCompletionEvent
from app.models.user import User
from app.modules.stats.models import PageView
from app.modules.stats.schemas import (
    BlogStats,
    DashboardStats,
    PageViewRecordRequest,
    TodoCompletionHistoryDayRead,
    TodoCompletionHistoryItemRead,
    TodoCompletionHistoryRead,
)
from app.modules.bills.service import get_bill_month_summary

_BLOG_STATS_CACHE_KEY = "stats:blog"
_BLOG_STATS_CACHE_TTL = 300


def iter_dates(start_date: date, end_date: date) -> list[date]:
    """生成闭区间日期列表。"""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def hash_client_ip(ip: str) -> str:
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
        for current_day in iter_dates(start_date, end_date)
    ]


def _构建待办完成历史响应(
    aggregates: list[待办完成聚合记录],
    *,
    start_date: date,
    end_date: date,
) -> TodoCompletionHistoryRead:
    """根据聚合结果构建待办完成历史响应。"""
    grouped: dict[date, list[TodoCompletionHistoryItemRead]] = {}
    for row in aggregates:
        normalized_score = _限制单个待办单日得分(row.normalized_score)
        if row.completed_count <= 0 or normalized_score <= 0:
            continue
        item = TodoCompletionHistoryItemRead(
            todo_id=row.todo_id,
            title=row.title,
            completed_count=row.completed_count,
            normalized_score=normalized_score,
        )
        grouped.setdefault(row.occurred_on, []).append(item)

    days: list[TodoCompletionHistoryDayRead] = []
    max_completed_count = 0
    total_completed_count = 0
    max_score = 0.0
    total_score = 0.0

    for current_day in iter_dates(start_date, end_date):
        items = grouped.get(current_day, [])
        completed_count = sum(item.completed_count for item in items)
        score = round(sum(item.normalized_score for item in items), 4)
        max_completed_count = max(max_completed_count, completed_count)
        total_completed_count += completed_count
        max_score = max(max_score, score)
        total_score = round(total_score + score, 4)
        days.append(
            TodoCompletionHistoryDayRead(
                date=current_day,
                completed_count=completed_count,
                score=score,
                items=items,
            )
        )

    return TodoCompletionHistoryRead(
        start_date=start_date,
        end_date=end_date,
        max_completed_count=max_completed_count,
        total_completed_count=total_completed_count,
        max_score=max_score,
        total_score=total_score,
        days=days,
    )


async def invalidate_blog_stats_cache() -> None:
    """清除博客站点统计缓存。"""
    redis = await get_redis()
    await redis.delete(_BLOG_STATS_CACHE_KEY)


async def get_blog_stats(db: AsyncSession) -> BlogStats:
    """获取博客站点统计。"""
    from app.modules.articles.models import Category, Tag

    redis = await get_redis()
    cached = await redis.get(_BLOG_STATS_CACHE_KEY)
    if cached:
        return BlogStats.model_validate_json(cached)

    total_articles = (
        await db.execute(
            select(func.count()).where(
                Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
            )
        )
    ).scalar() or 0
    total_categories = (await db.execute(select(func.count()).select_from(Category))).scalar() or 0
    total_tags = (await db.execute(select(func.count()).select_from(Tag))).scalar() or 0

    total_words = (
        await db.execute(
            select(func.coalesce(func.sum(Article.word_count), 0)).where(
                Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
            )
        )
    ).scalar() or 0

    last_published = (
        await db.execute(
            select(func.max(Article.published_at)).where(
                Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
            )
        )
    ).scalar()

    result = BlogStats(
        total_articles=total_articles,
        total_categories=total_categories,
        total_tags=total_tags,
        total_words=total_words,
        last_published_at=last_published,
    )

    await redis.setex(
        _BLOG_STATS_CACHE_KEY,
        _BLOG_STATS_CACHE_TTL,
        result.model_dump_json(),
    )
    return result


async def get_dashboard_stats(db: AsyncSession, user: User) -> DashboardStats:
    """获取用户仪表板统计。"""
    total_articles = (await db.execute(select(func.count()).where(Article.author_id == user.id))).scalar() or 0
    total_comments = (
        await db.execute(select(func.count()).select_from(Comment).join(Article).where(Article.author_id == user.id))
    ).scalar() or 0
    total_views = (
        await db.execute(select(func.coalesce(func.sum(Article.view_count), 0)).where(Article.author_id == user.id))
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
        .join(Article, PageView.article_id == Article.id)
        .where(
            Article.author_id == user.id,
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
    bill_summary = await get_bill_month_summary(db, user, month=None)

    return DashboardStats(
        total_articles=total_articles,
        total_comments=total_comments,
        total_views=total_views,
        total_todos=total_todos,
        current_month_bill_income_cent=bill_summary.income_cent,
        current_month_bill_expense_cent=bill_summary.expense_cent,
        current_month_bill_net_cent=bill_summary.net_cent,
        current_month_bill_record_count=bill_summary.record_count,
        recent_views=recent_views,
    )


async def get_todo_completion_history(
    db: AsyncSession,
    *,
    user: User,
    start_date: date,
    end_date: date,
) -> TodoCompletionHistoryRead:
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


async def record_pageview(
    db: AsyncSession,
    *,
    body: PageViewRecordRequest,
    client_ip: str,
    user_agent: str,
) -> None:
    """记录页面访问。"""
    page_view = PageView(
        path=body.path,
        article_id=body.article_id,
        ip_hash=hash_client_ip(client_ip),
        user_agent=user_agent[:500],
    )
    db.add(page_view)


__all__ = [
    "_BLOG_STATS_CACHE_KEY",
    "_BLOG_STATS_CACHE_TTL",
    "_构建待办完成历史响应",
    "_构建最近访问趋势",
    "_限制单个待办单日得分",
    "BlogStats",
    "DashboardStats",
    "PageViewRecordRequest",
    "TodoCompletionHistoryRead",
    "get_blog_stats",
    "get_dashboard_stats",
    "get_todo_completion_history",
    "hash_client_ip",
    "invalidate_blog_stats_cache",
    "iter_dates",
    "record_pageview",
    "待办完成聚合记录",
    "近期访问聚合记录",
]
