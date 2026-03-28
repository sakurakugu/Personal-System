"""统计和分析路由。

此模块提供数据统计接口，包括：
- 用户仪表板统计（文章数、评论数、浏览量等）
- 页面浏览量记录
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Article, Comment, PageView, Todo, TodoCompletionEvent, User
from app.schemas.schemas import DashboardStats, TodoCompletionHistoryDayRead, TodoCompletionHistoryItemRead, TodoCompletionHistoryRead

# 创建路由器，前缀为 /stats，标签为 stats
router = APIRouter(prefix="/stats", tags=["stats"])


def _iter_dates(start_date: date, end_date: date) -> list[date]:
    """生成闭区间日期列表。"""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户仪表板统计数据。

    统计信息包括：
    - 用户文章总数
    - 用户文章收到的评论总数
    - 用户文章总浏览量
    - 用户待办事项总数
    - 最近 7 天浏览量趋势

    Args:
        user: 当前登录用户（依赖注入）
        db: 数据库会话

    Returns:
        DashboardStats: 仪表板统计数据
    """
    # 用户文章总数
    total_articles = (await db.execute(
        select(func.count()).where(Article.author_id == user.id)
    )).scalar() or 0

    # 用户文章评论总数
    total_comments = (await db.execute(
        select(func.count()).select_from(Comment).join(Article).where(Article.author_id == user.id)
    )).scalar() or 0

    # 用户文章总浏览量
    total_views = (await db.execute(
        select(func.coalesce(func.sum(Article.view_count), 0)).where(Article.author_id == user.id)
    )).scalar() or 0

    # 待办事项总数
    total_todos = (await db.execute(
        select(func.count()).where(Todo.user_id == user.id)
    )).scalar() or 0

    # 最近 7 天浏览量
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = await db.execute(
        select(
            cast(PageView.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(PageView.created_at >= seven_days_ago)
        .group_by("date")
        .order_by("date")
    )
    recent_views = [{"date": str(row.date), "count": row.count} for row in recent]

    return DashboardStats(
        total_articles=total_articles,
        total_comments=total_comments,
        total_views=total_views,
        total_todos=total_todos,
        recent_views=recent_views,
    )


@router.get("/todos/completion-history", response_model=TodoCompletionHistoryRead)
async def todo_completion_history(
    start_date: date = Query(..., description="开始日期，格式 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期，格式 YYYY-MM-DD"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取待办完成历史。

    仅基于完成历史事件聚合，因此即使待办进入回收站或被永久删除，
    仍然可以保留当天的完成记录。
    """
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
        day = row.occurred_on
        item = TodoCompletionHistoryItemRead(
            todo_id=row.todo_id,
            title=row.title,
            completed_count=int(row.completed_count),
        )
        grouped.setdefault(day, []).append(item)

    days: list[TodoCompletionHistoryDayRead] = []
    max_completed_count = 0
    total_completed_count = 0
    for day in _iter_dates(start_date, end_date):
        items = grouped.get(day, [])
        completed_count = sum(item.completed_count for item in items)
        max_completed_count = max(max_completed_count, completed_count)
        total_completed_count += completed_count
        days.append(
            TodoCompletionHistoryDayRead(
                date=day,
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


@router.post("/pageview", status_code=204)
async def record_pageview(request: Request, db: AsyncSession = Depends(get_db)):
    """
    记录页面浏览量（由前端调用）。

    记录页面访问信息，包括访问路径、文章 ID、IP 哈希（隐私保护）和 User-Agent。

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        None
    """
    import hashlib
    body = await request.json()
    path = body.get("path", "/")
    article_id = body.get("article_id")
    ip = request.client.host if request.client else "unknown"
    # 对 IP 进行哈希处理，保护用户隐私
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:500]

    pv = PageView(
        path=path,
        article_id=article_id,
        ip_hash=ip_hash,
        user_agent=ua,
    )
    db.add(pv)
