"""用户清理逻辑。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import Article, ArticleImage
from app.modules.files.models import File
from app.modules.users.models import User
from app.shared.storage.client import remove_objects_best_effort


async def _list_user_storage_keys(db: AsyncSession, user_id: UUID) -> list[str]:
    """获取用户的全部对象存储键。"""
    file_result = await db.execute(select(File.storage_key).where(File.user_id == user_id))
    article_image_result = await db.execute(
        select(ArticleImage.storage_key)
        .join(Article, ArticleImage.article_id == Article.id)
        .where(Article.author_id == user_id)
    )
    return list(file_result.scalars().all()) + list(article_image_result.scalars().all())


async def delete_user_with_cleanup(db: AsyncSession, user: User) -> None:
    """删除用户，并在提交成功后清理对象存储。"""
    storage_keys = await _list_user_storage_keys(db, user.id)
    await db.delete(user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_objects_best_effort(storage_keys)
