"""用户清理逻辑。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import 文章, 文章图片
from app.modules.files.models import File
from app.modules.users.models import 用户
from app.shared.storage.client import 尽力删除多个对象


async def _列出用户存储键(db: AsyncSession, user_id: UUID) -> list[str]:
    """获取用户的全部对象存储键。"""
    file_result = await db.execute(select(File.storage_key).where(File.user_id == user_id))
    article_image_result = await db.execute(
        select(文章图片.storage_key)
        .join(文章, 文章图片.article_id == 文章.id)
        .where(文章.author_id == user_id)
    )
    return list(file_result.scalars().all()) + list(article_image_result.scalars().all())


async def 删除用户并清理(db: AsyncSession, user: 用户) -> None:
    """删除用户，并在提交成功后清理对象存储。"""
    storage_keys = await _列出用户存储键(db, user.id)
    await db.delete(user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    尽力删除多个对象(storage_keys)
