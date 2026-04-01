"""首页 Feed 流服务。"""

from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus, Tag
from app.models.feed import FeedItem, FeedItemType
from app.models.moment import Moment
from app.models.user import User
from app.schemas.article import ArticleListItem
from app.schemas.feed import FeedItemRead
from app.schemas.moment import MomentPublicRead
from app.schemas.shared import PaginatedResponse


def build_feed_visible_article_clause(user: User | None):
    """构建 Feed 中当前用户可见的文章条件。"""
    if user is None:
        return Article.status == ArticleStatus.public
    if not user.show_private_articles_on_home:
        return Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
    return or_(
        Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
        and_(
            Article.status == ArticleStatus.private,
            Article.author_id == user.id,
        ),
    )


def article_feed_source_query():
    """构建 Feed 使用的文章查询。"""
    return (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.category),
            selectinload(Article.tags),
        )
    )


def moment_feed_source_query():
    """构建 Feed 使用的动态查询。"""
    return select(Moment).options(selectinload(Moment.user))


async def get_feed_item(
    db: AsyncSession,
    item_type: FeedItemType,
    source_id: UUID,
) -> FeedItem | None:
    """按来源获取 Feed 条目。"""
    result = await db.execute(
        select(FeedItem).where(
            FeedItem.type == item_type,
            FeedItem.source_id == source_id,
        )
    )
    return result.scalar_one_or_none()


async def sync_article_feed_item(db: AsyncSession, article: Article) -> None:
    """同步文章对应的 Feed 条目。"""
    item = await get_feed_item(db, FeedItemType.article, article.id)

    if article.status in (ArticleStatus.public, ArticleStatus.login_required):
        条目时间 = article.published_at
    else:
        条目时间 = article.created_at

    if 条目时间 is None:
        if item is not None:
            item.is_visible = False
        return

    if item is None:
        db.add(
            FeedItem(
                type=FeedItemType.article,
                source_id=article.id,
                author_id=article.author_id,
                is_visible=True,
                published_at=条目时间,
            )
        )
        return

    item.author_id = article.author_id
    item.is_visible = True
    item.published_at = 条目时间


async def ensure_article_feed_items(db: AsyncSession) -> None:
    """为缺失 Feed 条目的可见文章补建条目。"""
    result = await db.execute(
        select(Article).where(
            or_(
                and_(
                    Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
                    Article.published_at.is_not(None),
                ),
                Article.status == ArticleStatus.private,
            ),
            ~Article.id.in_(
                select(FeedItem.source_id).where(FeedItem.type == FeedItemType.article)
            ),
        )
    )
    articles = result.scalars().all()
    for article in articles:
        db.add(
            FeedItem(
                type=FeedItemType.article,
                source_id=article.id,
                author_id=article.author_id,
                is_visible=True,
                published_at=article.published_at or article.created_at,
            )
        )
    if articles:
        await db.flush()


async def sync_moment_feed_item(db: AsyncSession, moment: Moment) -> None:
    """同步动态对应的 Feed 条目。"""
    item = await get_feed_item(db, FeedItemType.moment, moment.id)

    if not moment.is_published or moment.published_at is None:
        if item is not None:
            item.is_visible = False
        return

    if item is None:
        db.add(
            FeedItem(
                type=FeedItemType.moment,
                source_id=moment.id,
                author_id=moment.user_id,
                is_visible=True,
                published_at=moment.published_at,
            )
        )
        return

    item.author_id = moment.user_id
    item.is_visible = True
    item.published_at = moment.published_at


async def delete_feed_item(
    db: AsyncSession,
    item_type: FeedItemType,
    source_id: UUID,
) -> None:
    """删除来源对应的 Feed 条目。"""
    await db.execute(
        delete(FeedItem).where(
            FeedItem.type == item_type,
            FeedItem.source_id == source_id,
        )
    )


async def load_feed_articles(
    db: AsyncSession,
    article_ids: list[UUID],
    current_user: User | None,
) -> dict[UUID, Article]:
    """批量加载 Feed 中的文章。"""
    if not article_ids:
        return {}

    result = await db.execute(
        article_feed_source_query().where(
            Article.id.in_(article_ids),
            build_feed_visible_article_clause(current_user),
        )
    )
    articles = result.scalars().unique().all()
    return {article.id: article for article in articles}


async def load_feed_moments(db: AsyncSession, moment_ids: list[UUID]) -> dict[UUID, Moment]:
    """批量加载 Feed 中的动态。"""
    if not moment_ids:
        return {}

    result = await db.execute(
        moment_feed_source_query().where(
            Moment.id.in_(moment_ids),
            Moment.is_published.is_(True),
        )
    )
    moments = result.scalars().unique().all()
    return {moment.id: moment for moment in moments}


def build_article_feed_item(article: Article) -> FeedItemRead:
    """将文章转换为 Feed 响应项。"""
    return FeedItemRead(
        type="article",
        source_id=article.id,
        published_at=article.published_at or article.created_at,
        article=ArticleListItem.model_validate(article),
    )


def build_moment_feed_item(moment: Moment) -> FeedItemRead:
    """将动态转换为 Feed 响应项。"""
    return FeedItemRead(
        type="moment",
        source_id=moment.id,
        published_at=moment.published_at or moment.created_at,
        moment=MomentPublicRead.model_validate(moment),
    )


async def list_feed_items(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    current_user: User | None,
    category: str | None,
    tag: str | None,
    search: str | None,
) -> PaginatedResponse:
    """获取首页 Feed 流。"""
    await ensure_article_feed_items(db)
    可见文章条件 = build_feed_visible_article_clause(current_user)

    if category or tag or search:
        article_query = article_feed_source_query().where(可见文章条件)
        if category:
            article_query = article_query.where(Article.category.has(slug=category))
        if tag:
            article_query = article_query.where(Article.tags.any(Tag.slug == tag))
        if search:
            article_query = article_query.where(Article.title.ilike(f"%{search}%"))

        total = (await db.execute(select(func.count()).select_from(article_query.subquery()))).scalar() or 0
        result = await db.execute(
            article_query.order_by(func.coalesce(Article.published_at, Article.created_at).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        articles = result.scalars().unique().all()
        article_items = [build_article_feed_item(article) for article in articles]
        return PaginatedResponse(
            items=article_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        )

    可见文章来源子查询 = select(Article.id).where(可见文章条件)

    if current_user is None:
        query = select(FeedItem).where(
            FeedItem.type == FeedItemType.article,
            FeedItem.is_visible.is_(True),
            FeedItem.source_id.in_(可见文章来源子查询),
        )
    else:
        query = select(FeedItem).where(
            (FeedItem.type == FeedItemType.moment) & FeedItem.is_visible.is_(True)
            | (
                (FeedItem.type == FeedItemType.article)
                & FeedItem.is_visible.is_(True)
                & FeedItem.source_id.in_(可见文章来源子查询)
            )
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(FeedItem.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    feed_items = result.scalars().all()

    article_ids = [item.source_id for item in feed_items if item.type == FeedItemType.article]
    moment_ids = [item.source_id for item in feed_items if item.type == FeedItemType.moment]

    articles_by_id = await load_feed_articles(db, article_ids, current_user)
    moments_by_id = await load_feed_moments(db, moment_ids)

    items: list[FeedItemRead] = []
    for item in feed_items:
        if item.type == FeedItemType.article:
            article = articles_by_id.get(item.source_id)
            if article is None:
                continue
            items.append(build_article_feed_item(article))
            continue

        moment = moments_by_id.get(item.source_id)
        if moment is None:
            continue
        items.append(build_moment_feed_item(moment))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
