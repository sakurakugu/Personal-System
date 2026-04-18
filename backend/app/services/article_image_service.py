"""文章图片服务兼容入口。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import ArticleImage
from app.models.user import User
from app.modules.articles.image import (
    build_article_image_directory,
    build_article_image_read,
    upload_article_image,
)
from app.modules.articles.permissions import ensure_article_write_permission
from app.modules.articles.queries import get_article_or_404


async def list_article_images(
    db: AsyncSession,
    user: User,
    article_id: str,
):
    """获取当前文章的全部图片。"""
    article = await get_article_or_404(db, article_id)
    ensure_article_write_permission(article, user)

    result = await db.execute(
        select(ArticleImage)
        .where(ArticleImage.article_id == article.id)
        .order_by(ArticleImage.created_at.desc())
    )
    return [build_article_image_read(record) for record in result.scalars().all()]


__all__ = [
    "build_article_image_directory",
    "build_article_image_read",
    "ensure_article_write_permission",
    "get_article_or_404",
    "list_article_images",
    "upload_article_image",
]
