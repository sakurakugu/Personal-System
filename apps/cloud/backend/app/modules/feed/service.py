"""首页 Feed 模块服务。"""

from app.core.redis import get_redis
from app.shared.engagement import 包含集合成员
from app.modules.feed.models import FeedItem, FeedItemType
from app.modules.feed.schemas import FeedItemRead
from app.modules.articles.schema import 构建文章列表项响应
from app.modules.articles.search import 构建文章搜索条件
from app.modules.articles.models import Article, ArticleStatus, Tag
from app.modules.moments.models import Moment
from app.modules.moments.presentation import 构建动态公开读取响应
from app.modules.users.models import User
from app.shared.kernel.pagination import PaginatedResponse

import math
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

_FEED_ENSURE_LOCK_KEY = "feed:确保文章Feed条目"
_FEED_ENSURE_LOCK_TTL = 300
_FEED_HOME_CACHE_PREFIX = "feed:home:"
_FEED_HOME_CACHE_VERSION_KEY = "feed:home:version"
_FEED_HOME_CACHE_TTL = 120


def _规范化Feed缓存版本(value: str | None) -> str:
    """将缓存版本值规范化为可拼接的字符串。"""
    if not value:
        return "0"
    return value


def _构建Feed首页缓存键(
    page: int,
    page_size: int,
    current_user: User | None,
    *,
    version: str,
    visitor_id: str | None,
) -> str:
    """构建首页 Feed 缓存键。"""
    user_id = str(current_user.id) if current_user else "guest"
    visitor_segment = visitor_id or "anon"
    normalized_version = _规范化Feed缓存版本(version)
    return (
        f"{_FEED_HOME_CACHE_PREFIX}v={normalized_version}:"
        f"page={page}:size={page_size}:user={user_id}:visitor={visitor_segment}"
    )


async def _获取Feed首页缓存版本() -> str:
    """获取当前首页 Feed 缓存版本。"""
    redis = await get_redis()
    version = await redis.get(_FEED_HOME_CACHE_VERSION_KEY)
    return _规范化Feed缓存版本(version if isinstance(version, str) else None)


async def _尝试确保文章Feed条目(db: AsyncSession) -> None:
    """尝试补建缺失的 Feed 条目。"""
    redis = await get_redis()
    locked = await redis.set(_FEED_ENSURE_LOCK_KEY, "1", nx=True, ex=_FEED_ENSURE_LOCK_TTL)
    if locked:
        await 确保文章Feed条目(db)


async def 清除Feed首页缓存() -> None:
    """清除首页 Feed 缓存。"""
    redis = await get_redis()
    await redis.incr(_FEED_HOME_CACHE_VERSION_KEY)


def 构建Feed可见文章条件(
    user: User | None,
    *,
    include_own_private: bool = False,
):
    """构建 Feed 中当前用户可见的文章条件。"""
    deleted_clause = Article.is_deleted.is_(False)
    if user is None:
        return deleted_clause & (Article.status == ArticleStatus.public)
    if include_own_private:
        return deleted_clause & or_(
            Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
            and_(
                Article.status == ArticleStatus.private,
                Article.author_id == user.id,
            ),
        )
    if user.settings is None or not user.settings.show_private_articles_on_home:
        return deleted_clause & Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
    return deleted_clause & or_(
        Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
        and_(
            Article.status == ArticleStatus.private,
            Article.author_id == user.id,
        ),
    )


def 文章Feed来源查询():
    """构建 Feed 使用的文章查询。"""
    return (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.category),
            selectinload(Article.tags),
        )
    )


def 动态Feed来源查询():
    """构建 Feed 使用的动态查询。"""
    return select(Moment).options(selectinload(Moment.user), selectinload(Moment.images))


async def 获取Feed条目(
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


async def 同步文章Feed条目(db: AsyncSession, article: Article) -> None:
    """同步文章对应的 Feed 条目。"""
    item = await 获取Feed条目(db, FeedItemType.article, article.id)

    if article.is_deleted:
        if item is not None:
            item.is_visible = False
        return

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


async def 确保文章Feed条目(db: AsyncSession) -> None:
    """为缺失 Feed 条目的可见文章补建条目。"""
    result = await db.execute(
        select(Article).where(
            Article.is_deleted.is_(False),
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


async def 同步动态Feed条目(db: AsyncSession, moment: Moment) -> None:
    """同步动态对应的 Feed 条目。"""
    item = await 获取Feed条目(db, FeedItemType.moment, moment.id)

    if moment.is_deleted or not moment.is_published or moment.published_at is None:
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


async def 删除Feed条目(
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


async def 加载Feed文章(
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
        文章Feed来源查询().where(
            Article.id.in_(article_ids),
            Article.is_deleted.is_(False),
            构建Feed可见文章条件(
                current_user,
                include_own_private=include_own_private,
            ),
        )
    )
    articles = result.scalars().unique().all()
    return {article.id: article for article in articles}


async def 加载Feed动态(db: AsyncSession, moment_ids: list[UUID]) -> dict[UUID, Moment]:
    """批量加载 Feed 中的动态。"""
    if not moment_ids:
        return {}

    result = await db.execute(
        动态Feed来源查询().where(
            Moment.id.in_(moment_ids),
            Moment.is_published.is_(True),
            Moment.is_deleted.is_(False),
        )
    )
    moments = result.scalars().unique().all()
    return {moment.id: moment for moment in moments}


def 构建文章Feed条目(article: Article, *, sign_cover_url: bool = False) -> FeedItemRead:
    """将文章转换为 Feed 响应项。"""
    return FeedItemRead(
        type="article",
        source_id=article.id,
        published_at=article.published_at or article.created_at,
        article=构建文章列表项响应(article, sign_cover_url=sign_cover_url),
    )


async def 构建动态Feed条目(
    moment: Moment,
    *,
    visitor_id: str | None = None,
) -> FeedItemRead:
    """将动态转换为 Feed 响应项。"""
    liked = False
    if visitor_id:
        liked = await 包含集合成员(f"like:moment:{moment.id}", visitor_id)
    return FeedItemRead(
        type="moment",
        source_id=moment.id,
        published_at=moment.published_at or moment.created_at,
        moment=构建动态公开读取响应(moment, liked=liked),
    )


async def 列出Feed条目(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    current_user: User | None,
    category: str | None,
    tag: str | None,
    search: str | None,
    include_own_private: bool = False,
    visitor_id: str | None = None,
) -> PaginatedResponse:
    """获取首页 Feed 流。"""
    await _尝试确保文章Feed条目(db)
    可见文章条件 = 构建Feed可见文章条件(
        current_user,
        include_own_private=include_own_private,
    )

    can_cache = not (category or tag or search or include_own_private)
    cache_key: str | None = None

    if can_cache:
        cache_version = await _获取Feed首页缓存版本()
        cache_key = _构建Feed首页缓存键(
            page,
            page_size,
            current_user,
            version=cache_version,
            visitor_id=visitor_id,
        )
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return PaginatedResponse.model_validate_json(cached)

    if category or tag or search:
        文章查询 = 文章Feed来源查询().where(可见文章条件)
        if category:
            文章查询 = 文章查询.where(Article.category.has(slug=category))
        if tag:
            文章查询 = 文章查询.where(Article.tags.any(Tag.slug == tag))
        搜索条件 = 构建文章搜索条件(search, current_user)
        if 搜索条件 is not None:
            文章查询 = 文章查询.where(搜索条件)

        total = (await db.execute(select(func.count()).select_from(文章查询.subquery()))).scalar() or 0
        result = await db.execute(
            文章查询.order_by(func.coalesce(Article.published_at, Article.created_at).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        articles = result.scalars().unique().all()
        article_items = [构建文章Feed条目(article, sign_cover_url=True) for article in articles]
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

    articles_by_id = await 加载Feed文章(
        db,
        article_ids,
        current_user,
        include_own_private=include_own_private,
    )
    moments_by_id = await 加载Feed动态(db, moment_ids)

    items: list[FeedItemRead] = []
    for item in feed_items:
        if item.type == FeedItemType.article:
            article = articles_by_id.get(item.source_id)
            if article is None:
                continue
            items.append(构建文章Feed条目(article, sign_cover_url=True))
            continue

        moment = moments_by_id.get(item.source_id)
        if moment is None:
            continue
        items.append(await 构建动态Feed条目(moment, visitor_id=visitor_id))

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
    "_构建Feed首页缓存键",
    "_获取Feed首页缓存版本",
    "_规范化Feed缓存版本",
    "文章Feed来源查询",
    "构建文章Feed条目",
    "构建Feed可见文章条件",
    "构建动态Feed条目",
    "删除Feed条目",
    "确保文章Feed条目",
    "获取Feed条目",
    "清除Feed首页缓存",
    "列出Feed条目",
    "加载Feed文章",
    "加载Feed动态",
    "动态Feed来源查询",
    "同步文章Feed条目",
    "同步动态Feed条目",
]
