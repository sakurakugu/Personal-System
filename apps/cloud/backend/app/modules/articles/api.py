"""文章 CRUD 路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户, 获取当前用户可选
from app.shared.db.session import get_db

from app.modules.articles.publication import 列出博客管理, 发布博客, 修改博客发布状态, 提交博客发布事务
from app.modules.articles.schemas import 博客发布请求, 博客可见性更新
from app.modules.articles.workflow import 博客查询
from app.modules.articles.models import 博客发布
from fastapi import HTTPException

from app.modules.articles.crud import (
    创建文章 as 创建文章_service,
    创建文章草稿 as 创建文章草稿_service,
    删除文章 as 删除文章_service,
    恢复文章 as 恢复文章_service,
    更新文章 as 更新文章_service,
)
from app.modules.articles.image import (
    删除文章图片 as 删除文章图片_service,
    列出文章图片 as 列出文章图片_service,
    上传文章图片 as 上传文章图片_service,
)
from app.modules.articles.queries import (
    全部文章分类筛选值,
    按标识获取文章,
    获取我的文章 as 获取我的文章_service,
    获取我删除的文章 as 获取我删除的文章_service,
    获取相关和随机文章,
    访客是否已点赞文章,
    按标识点赞文章,
    列出全部文章元数据,
    列出文章 as 列出文章_service,
    列出我删除的文章 as 列出我删除的文章_service,
    列出我的文章 as 列出我的文章_service,
    未分类文章分类筛选值,
    取消按标识点赞文章,
)
from app.modules.articles.schema import 构建文章读取响应
from app.modules.articles.schemas import (
    分类信息,
    文章创建,
    文章草稿创建,
    文章图片信息,
    文章点赞信息,
    文章元数据信息,
    文章导航信息,
    文章信息,
    文章相关响应,
    文章更新,
)
from app.modules.articles.taxonomy import 列出我的有文章分类 as 列出我的有文章分类_service
from app.shared.kernel.pagination import PaginatedResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.delete("/{article_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除文章图片(article_id: str, image_id: str, user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """删除未被文章和发布快照引用的图片。"""
    await 删除文章图片_service(db, user, article_id, image_id)


@router.get("/all-meta", response_model=list[文章元数据信息])
async def list_all_meta(
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有可见文章的最小元数据（用于日历、归档等）。

    Args:
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        list[文章元数据信息]: 文章元数据列表
    """
    articles = await 列出全部文章元数据(db, user=user)
    return [文章元数据信息.model_validate(a) for a in articles]


@router.get("", response_model=PaginatedResponse)
async def 列出文章(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    user: 用户 | None = Depends(获取当前用户可选),
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
    return await 列出文章_service(
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
async def 列出我的文章(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    is_deleted: bool = Query(False, description="是否显示回收站文章"),
    category: str = Query(
        全部文章分类筛选值,
        description=f"文章分类筛选：{全部文章分类筛选值} 为全部，{未分类文章分类筛选值} 为未分类，其他值按分类 ID 筛选",
    ),
    user: 用户 = Depends(获取当前用户),
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
    if is_deleted:
        return await 列出我删除的文章_service(
            db,
            page=page,
            page_size=page_size,
            user=user,
            category_filter=category,
        )
    return await 列出我的文章_service(
        db,
        page=page,
        page_size=page_size,
        user=user,
        category_filter=category,
    )


@router.get("/my/categories", response_model=list[分类信息])
async def 列出我的文章分类(
    is_deleted: bool = Query(False, description="是否统计回收站文章分类"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户有文章的分类列表。"""
    return await 列出我的有文章分类_service(db, user.id, is_deleted=is_deleted)


@router.get("/my/{article_id}", response_model=文章信息)
async def 获取我的文章(
    article_id: str,
    is_deleted: bool = Query(False, description="是否读取回收站文章"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户自己的文章详情。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        文章信息: 文章详情
    """
    if is_deleted:
        return await 获取我删除的文章_service(db, article_id, user)
    return await 获取我的文章_service(db, article_id, user)


@router.get("/blog/manage")
async def 管理博客列表(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    search: str | None = None, state: str = Query("all", pattern="^(all|published|unpublished|changed)$"),
    user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db),
):
    """管理文章对应的博客发布记录。"""
    return await 列出博客管理(db, user, page, page_size, search, state)


@router.get("/blog/{article_id}/snapshot", response_model=文章信息)
async def 预览博客快照(article_id: str, user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """作者预览最近一次发布快照，包括已撤下内容。"""
    result = await db.execute(博客查询().where(博客发布.id == article_id, 博客发布.author_id == user.id))
    blog = result.scalar_one_or_none()
    if blog is None:
        raise HTTPException(status_code=404, detail="没有发布快照")
    return 构建文章读取响应(blog, sign_file_urls=True)


@router.post("/blog/{article_id}/publish")
async def 发布博客快照(article_id: str, body: 博客发布请求, user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """发布或更新完整内容快照。"""
    result = await 发布博客(db, article_id, body, user)
    await 提交博客发布事务(db)
    return result


@router.patch("/blog/{article_id}/visibility")
async def 更新博客可见性(article_id: str, body: 博客可见性更新, user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """只调整访问权限。"""
    result = await 修改博客发布状态(db, article_id, user, visibility=body.visibility)
    await 提交博客发布事务(db)
    return result


@router.post("/blog/{article_id}/withdraw")
async def 撤下博客(article_id: str, user: 用户 = Depends(获取当前用户), db: AsyncSession = Depends(get_db)):
    """撤下博客，保留文章、快照及统计。"""
    result = await 修改博客发布状态(db, article_id, user)
    await 提交博客发布事务(db)
    return result


@router.get("/{slug}", response_model=文章信息)
async def get_article(
    slug: str,
    request: Request,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开文章详情。

    Args:
        slug: 文章 slug
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        文章信息: 当前用户可访问的文章详情
    """
    article = await 按标识获取文章(db, slug, user)
    liked = await 访客是否已点赞文章(article.id, request)
    return 构建文章读取响应(article, sign_file_urls=True, liked=liked)


@router.post("/{slug}/like", response_model=文章点赞信息)
async def like_article(
    slug: str,
    request: Request,
    response: Response,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    点赞文章。

    Args:
        slug: 文章 slug
        request: 当前请求
        response: 当前响应
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        文章点赞信息: 点赞结果
    """
    return await 按标识点赞文章(db, slug, user, request, response)


@router.delete("/{slug}/like", response_model=文章点赞信息)
async def unlike_article(
    slug: str,
    request: Request,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    取消点赞文章。

    Args:
        slug: 文章 slug
        request: 当前请求
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        文章点赞信息: 取消点赞结果
    """
    return await 取消按标识点赞文章(db, slug, user, request)


@router.get("/{slug}/related", response_model=文章相关响应)
async def 获取文章相关(
    slug: str,
    user: 用户 | None = Depends(获取当前用户可选),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文章的相关推荐和随机推荐。

    Args:
        slug: 文章 slug
        user: 当前登录用户，可为空
        db: 数据库会话

    Returns:
        文章相关响应: 相关文章与随机推荐列表
    """
    prev_article, next_article, related, random = await 获取相关和随机文章(db, slug, user)
    return 文章相关响应(
        prev=文章导航信息.model_validate(prev_article) if prev_article is not None else None,
        next=文章导航信息.model_validate(next_article) if next_article is not None else None,
        related=[文章元数据信息.model_validate(a) for a in related],
        random=[文章元数据信息.model_validate(a) for a in random],
    )


@router.post("", response_model=文章信息, status_code=status.HTTP_201_CREATED)
async def 创建文章(
    body: 文章创建,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文章。

    Args:
        body: 文章请求体
        user: 当前登录用户
        db: 数据库会话

    Returns:
        文章信息: 新建文章
    """
    return await 创建文章_service(db, body, user)


@router.post("/draft", response_model=文章信息, status_code=status.HTTP_201_CREATED)
async def 创建文章草稿(
    body: 文章草稿创建 | None = None,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    创建文章草稿占位。

    Args:
        body: 草稿初始化内容
        user: 当前登录用户
        db: 数据库会话

    Returns:
        文章信息: 新建草稿文章
    """
    return await 创建文章草稿_service(db, body, user)


@router.patch("/{article_id}", response_model=文章信息)
async def 更新文章(
    article_id: str,
    body: 文章更新,
    user: 用户 = Depends(获取当前用户),
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
        文章信息: 更新后的文章
    """
    return await 更新文章_service(db, article_id, body, user)


@router.post("/{article_id}/images", response_model=文章图片信息, status_code=status.HTTP_201_CREATED)
async def 上传文章图片(
    article_id: str,
    file: UploadFile,
    user: 用户 = Depends(获取当前用户),
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
        文章图片信息: 图片信息
    """
    return await 上传文章图片_service(db, user, article_id, file)


@router.get("/my/{article_id}/images", response_model=list[文章图片信息])
async def 列出文章图片(
    article_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户文章的全部图片。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        list[文章图片信息]: 图片列表
    """
    return await 列出文章图片_service(db, user, article_id)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def 删除文章(
    article_id: str,
    permanent: bool = Query(False, description="是否永久删除"),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文章。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话
    """
    await 删除文章_service(db, article_id, user, permanent=permanent)


@router.post("/{article_id}/restore", response_model=文章信息)
async def 恢复文章(
    article_id: str,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """
    从回收站恢复文章。

    Args:
        article_id: 文章 ID
        user: 当前登录用户
        db: 数据库会话

    Returns:
        文章信息: 恢复后的文章
    """
    return await 恢复文章_service(db, article_id, user)
