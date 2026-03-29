"""统计分析服务。"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import Date, cast, func, select
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

    grouped: dict[date, list[TodoCompletionHistoryItemRead]] = {}
    for row in result:
        item = TodoCompletionHistoryItemRead(
            todo_id=row.todo_id,
            title=row.title,
            completed_count=int(row.completed_count),
        )
        grouped.setdefault(row.occurred_on, []).append(item)

    days: list[TodoCompletionHistoryDayRead] = []
    max_completed_count = 0
    total_completed_count = 0
    for current_day in iter_dates(start_date, end_date):
        items = grouped.get(current_day, [])
        completed_count = sum(item.completed_count for item in items)
        max_completed_count = max(max_completed_count, completed_count)
        total_completed_count += completed_count
        days.append(
            TodoCompletionHistoryDayRead(
                date=current_day,
                completed_count=completed_count,
                items=items,
            )
        )

    return TodoCompletionHistoryRead(
        start_date=start_date,
        end_date=end_date,
        max_completed_count=max_completed_count,
        total_completed_count=total_completed_count,
        days=days,
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
