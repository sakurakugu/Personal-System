"""统计分析服务。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Date, Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import PageView
from app.models.article import Article
from app.models.comment import Comment
from app.models.todo import Todo, TodoCompletionEvent
from app.models.user import User
from app.schemas.system import DashboardStats, PageViewRecordRequest, TodoCompletionHistoryDayRead, TodoCompletionHistoryItemRead, TodoCompletionHistoryRead
from app.services.bill_service import get_bill_month_summary


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


def _限制单个待办单日得分(score: float) -> float:
    """将单个待办单日得分限制在 0 到 1 之间。"""
    return round(min(max(score, 0.0), 1.0), 4)


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


async def get_blog_stats(db: AsyncSession) -> "BlogStats":
    """获取博客站点统计（无需登录）。"""
    import re

    from app.models.article import Category, Tag
    from app.schemas.system import BlogStats

    total_articles = (
        await db.execute(
            select(func.count()).where(
                Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
            )
        )
    ).scalar() or 0
    total_categories = (await db.execute(select(func.count()).select_from(Category))).scalar() or 0
    total_tags = (await db.execute(select(func.count()).select_from(Tag))).scalar() or 0

    # 总字数：中文字符 + 英文连续字母（与 Firefly 逻辑保持一致）
    result = await db.execute(
        select(Article.content).where(
            Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
        )
    )
    contents = result.scalars().all()
    total_words = 0
    for content in contents:
        if content:
            text = (
                re.sub(r"```[\s\S]*?```", "", content)
                .replace(r"`[^`]*`", "")
            )
            chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", text))
            english_chars = len(re.findall(r"[a-zA-Z]", text))
            total_words += chinese_chars + english_chars

    last_published = (
        await db.execute(
            select(func.max(Article.published_at)).where(
                Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
            )
        )
    ).scalar()

    return BlogStats(
        total_articles=total_articles,
        total_categories=total_categories,
        total_tags=total_tags,
        total_words=total_words,
        last_published_at=last_published,
    )


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

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = await db.execute(
        select(cast(PageView.created_at, Date).label("date"), func.count().label("count"))
        .where(PageView.created_at >= seven_days_ago)
        .group_by("date")
        .order_by("date")
    )
    recent_views = [{"date": str(row.date), "count": row.count} for row in recent]
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
