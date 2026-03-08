"""Stats & analytics routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Article, Comment, PageView, Todo, User
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total articles by this user
    total_articles = (await db.execute(
        select(func.count()).where(Article.author_id == user.id)
    )).scalar() or 0

    # Total comments on user's articles
    total_comments = (await db.execute(
        select(func.count()).select_from(Comment).join(Article).where(Article.author_id == user.id)
    )).scalar() or 0

    # Total views on user's articles
    total_views = (await db.execute(
        select(func.coalesce(func.sum(Article.view_count), 0)).where(Article.author_id == user.id)
    )).scalar() or 0

    # Total todos
    total_todos = (await db.execute(
        select(func.count()).where(Todo.user_id == user.id)
    )).scalar() or 0

    # Views last 7 days (from page_views table)
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


@router.post("/pageview", status_code=204)
async def record_pageview(request: Request, db: AsyncSession = Depends(get_db)):
    """Record a page view (called from frontend)."""
    import hashlib
    body = await request.json()
    path = body.get("path", "/")
    article_id = body.get("article_id")
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:500]

    pv = PageView(
        path=path,
        article_id=article_id,
        ip_hash=ip_hash,
        user_agent=ua,
    )
    db.add(pv)
