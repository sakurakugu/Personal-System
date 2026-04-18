"""文章 CRUD 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User

from app.modules.articles.crud import (
    create_article as create_article_service,
    create_article_draft as create_article_draft_service,
    delete_article as delete_article_service,
    update_article as update_article_service,
)
from app.modules.articles.image import (
    list_article_images as list_article_images_service,
    upload_article_image as upload_article_image_service,
)
from app.modules.articles.queries import (
    get_article_by_slug,
    get_my_article as get_my_article_service,
    get_related_and_random_articles,
    list_all_article_meta,
    list_articles as list_articles_service,
    list_my_articles as list_my_articles_service,
)
from app.modules.articles.schema import build_article_read_response
from app.modules.articles.schemas import (
    ArticleCreate,
    ArticleDraftCreate,
    ArticleImageRead,
    ArticleMetaRead,
    ArticleNavigationRead,
    ArticleRead,
    ArticleRelatedResponse,
    ArticleUpdate,
)
from app.schemas.shared import PaginatedResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/all-meta", response_model=list[ArticleMetaRead])
async def list_all_meta(
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有可见文章的最小元数据（用于日历、归档等）。

    Args:
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        list[ArticleMetaRead]: 文章元数据列表
    """
    articles = await list_all_article_meta(db, user=user)
    return [ArticleMetaRead.model_validate(a) for a in articles]


@router.get("", response_model=PaginatedResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开文章列表。

    Args:
        page: 页码
        page_size: 每页数量
        category: 分类 slug
        tag: 标签 slug
        search: 搜索词，登录后支持匹配标题、摘要和正文
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页文章数据
    """
    return await list_articles_service(
        db,
        page=page,
        page_size=page_size,
        user=user,
        category=category,
        tag=tag,
        search=search,
        sign_cover_url=True,
    )


@router.get("/my/list", response_model=PaginatedResponse)
async def list_my_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户文章列表。

    Args:
        page: 页码
        page_size: 每页数量
        user: 当前登录用户
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页文章数据
    """
    return await list_my_articles_service(db, page=page, page_size=page_size, user=user)


@router.get("/my/{article_id}", response_model=ArticleRead)
async def get_my_article(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户自己的文章详情。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        ArticleRead: 文章详情
    """
    return await get_my_article_service(db, article_id, user)


@router.get("/{slug}", response_model=ArticleRead)
async def get_article(
    slug: str,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开文章详情。

    Args:
        slug: 文章 slug
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        ArticleRead: 当前用户可访问的文章详情
    """
    article = await get_article_by_slug(db, slug, user)
    return build_article_read_response(article, sign_file_urls=True)


@router.get("/{slug}/related", response_model=ArticleRelatedResponse)
async def get_article_related(
    slug: str,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章的相关推荐和随机推荐。

    Args:
        slug: 文章 slug
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        ArticleRelatedResponse: 相关文章与随机推荐列表
    """
    prev_article, next_article, related, random = await get_related_and_random_articles(db, slug, user)
    return ArticleRelatedResponse(
        prev=ArticleNavigationRead.model_validate(prev_article) if prev_article is not None else None,
        next=ArticleNavigationRead.model_validate(next_article) if next_article is not None else None,
        related=[ArticleMetaRead.model_validate(a) for a in related],
        random=[ArticleMetaRead.model_validate(a) for a in random],
    )


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文章。

    Args:
        body: 文章请求体
        user: 当前登录用户
        db: 数据库会话

    Returns:
        ArticleRead: 新建文章
    """
    return await create_article_service(db, body, user)


@router.post("/draft", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article_draft(
    body: ArticleDraftCreate | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文章草稿占位。

    Args:
        body: 草稿初始化内容
        user: 当前登录用户
        db: 数据库会话

    Returns:
        ArticleRead: 新建草稿文章
    """
    return await create_article_draft_service(db, body, user)


@router.patch("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: str,
    body: ArticleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新文章。

    Args:
        article_id: 文章 ID
        body: 更新请求体
        user: 当前登录用户
        db: 数据库会话

    Returns:
        ArticleRead: 更新后的文章
    """
    return await update_article_service(db, article_id, body, user)


@router.post("/{article_id}/images", response_model=ArticleImageRead, status_code=status.HTTP_201_CREATED)
async def upload_article_image(
    article_id: str,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文章图片。

    Args:
        article_id: 文章 ID
        file: 上传的图片文件
        user: 当前登录用户
        db: 数据库会话

    Returns:
        ArticleImageRead: 图片信息
    """
    return await upload_article_image_service(db, user, article_id, file)


@router.get("/my/{article_id}/images", response_model=list[ArticleImageRead])
async def list_article_images(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户文章的全部图片。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        list[ArticleImageRead]: 图片列表
    """
    return await list_article_images_service(db, user, article_id)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文章。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话
    """
    await delete_article_service(db, article_id, user)
