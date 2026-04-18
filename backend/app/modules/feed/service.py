"""首页 Feed 模块服务。"""

from app.core.redis import get_redis
from app.modules.feed.models import FeedItem, FeedItemType
from app.modules.feed.schemas import FeedItemRead
from app.modules.articles.schema import build_article_list_item_response
from app.modules.articles.search import build_article_search_clause
from app.modules.articles.models import Article, ArticleStatus, Tag
from app.modules.moments.models import Moment
from app.modules.users.models import User
from app.modules.moments.schemas import MomentPublicRead
from app.schemas.shared import PaginatedResponse

import math
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

_FEED_ENSURE_LOCK_KEY = "feed:ensure_article_feed_items"
_FEED_ENSURE_LOCK_TTL = 300
_FEED_HOME_CACHE_PREFIX = "feed:home:"
_FEED_HOME_CACHE_VERSION_KEY = "feed:home:version"
_FEED_HOME_CACHE_TTL = 120


def _normalize_feed_cache_version(value: str | None) -> str:
    """将缓存版本值规范化为可拼接的字符串。"""
    if not value:
        return "0"
    return value


def _build_feed_home_cache_key(
    page: int,
    page_size: int,
    current_user: User | None,
    *,
    version: str,
) -> str:
    """构建首页 Feed 缓存键。"""
    user_id = str(current_user.id) if current_user else "guest"
    normalized_version = _normalize_feed_cache_version(version)
    return (
        f"{_FEED_HOME_CACHE_PREFIX}v={normalized_version}:"
        f"page={page}:size={page_size}:user={user_id}"
    )


async def _get_feed_home_cache_version() -> str:
    """获取当前首页 Feed 缓存版本。"""
    redis = await get_redis()
    version = await redis.get(_FEED_HOME_CACHE_VERSION_KEY)
    return _normalize_feed_cache_version(version if isinstance(version, str) else None)


async def _try_ensure_article_feed_items(db: AsyncSession) -> None:
    """尝试补建缺失的 Feed 条目。"""
    redis = await get_redis()
    locked = await redis.set(_FEED_ENSURE_LOCK_KEY, "1", nx=True, ex=_FEED_ENSURE_LOCK_TTL)
    if locked:
        await ensure_article_feed_items(db)


async def invalidate_feed_home_cache() -> None:
    """清除首页 Feed 缓存。"""
    redis = await get_redis()
    await redis.incr(_FEED_HOME_CACHE_VERSION_KEY)


def build_feed_visible_article_clause(
    user: User | None,
    *,
    include_own_private: bool = False,
):
    """构建 Feed 中当前用户可见的文章条件。"""
    if user is None:
        return Article.status == ArticleStatus.public
    if include_own_private:
        return or_(
            Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
            and_(
                Article.status == ArticleStatus.private,
                Article.author_id == user.id,
            ),
        )
    if user.settings is None or not user.settings.show_private_articles_on_home:
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
    *,
    include_own_private: bool = False,
) -> dict[UUID, Article]:
    """批量加载 Feed 中的文章。"""
    if not article_ids:
        return {}

    result = await db.execute(
        article_feed_source_query().where(
            Article.id.in_(article_ids),
            build_feed_visible_article_clause(
                current_user,
                include_own_private=include_own_private,
            ),
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


def build_article_feed_item(article: Article, *, sign_cover_url: bool = False) -> FeedItemRead:
    """将文章转换为 Feed 响应项。"""
    return FeedItemRead(
        type="article",
        source_id=article.id,
        published_at=article.published_at or article.created_at,
        article=build_article_list_item_response(article, sign_cover_url=sign_cover_url),
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
    include_own_private: bool = False,
) -> PaginatedResponse:
    """获取首页 Feed 流。"""
    await _try_ensure_article_feed_items(db)
    可见文章条件 = build_feed_visible_article_clause(
        current_user,
        include_own_private=include_own_private,
    )

    can_cache = not (category or tag or search or include_own_private)
    cache_key: str | None = None

    if can_cache:
        cache_version = await _get_feed_home_cache_version()
        cache_key = _build_feed_home_cache_key(
            page,
            page_size,
            current_user,
            version=cache_version,
        )
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return PaginatedResponse.model_validate_json(cached)

    if category or tag or search:
        article_query = article_feed_source_query().where(可见文章条件)
        if category:
            article_query = article_query.where(Article.category.has(slug=category))
        if tag:
            article_query = article_query.where(Article.tags.any(Tag.slug == tag))
        搜索条件 = build_article_search_clause(search, current_user)
        if 搜索条件 is not None:
            article_query = article_query.where(搜索条件)

        total = (await db.execute(select(func.count()).select_from(article_query.subquery()))).scalar() or 0
        result = await db.execute(
            article_query.order_by(func.coalesce(Article.published_at, Article.created_at).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        articles = result.scalars().unique().all()
        article_items = [build_article_feed_item(article, sign_cover_url=True) for article in articles]
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

    articles_by_id = await load_feed_articles(
        db,
        article_ids,
        current_user,
        include_own_private=include_own_private,
    )
    moments_by_id = await load_feed_moments(db, moment_ids)

    items: list[FeedItemRead] = []
    for item in feed_items:
        if item.type == FeedItemType.article:
            article = articles_by_id.get(item.source_id)
            if article is None:
                continue
            items.append(build_article_feed_item(article, sign_cover_url=True))
            continue

        moment = moments_by_id.get(item.source_id)
        if moment is None:
            continue
        items.append(build_moment_feed_item(moment))

    response = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )

    if cache_key:
        redis = await get_redis()
        await redis.setex(cache_key, _FEED_HOME_CACHE_TTL, response.model_dump_json())

    return response


__all__ = [
    "FeedItem",
    "FeedItemRead",
    "FeedItemType",
    "_build_feed_home_cache_key",
    "_get_feed_home_cache_version",
    "_normalize_feed_cache_version",
    "article_feed_source_query",
    "build_article_feed_item",
    "build_feed_visible_article_clause",
    "build_moment_feed_item",
    "delete_feed_item",
    "ensure_article_feed_items",
    "get_feed_item",
    "invalidate_feed_home_cache",
    "list_feed_items",
    "load_feed_articles",
    "load_feed_moments",
    "moment_feed_source_query",
    "sync_article_feed_item",
    "sync_moment_feed_item",
]
