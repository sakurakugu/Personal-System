"""用户清理逻辑。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import Article, ArticleImage
from app.models.comment import Comment
from app.modules.files.models import File
from app.modules.users.models import User
from app.services.storage_service import remove_objects_best_effort

已注销后缀 = "（已注销）"


def build_deleted_comment_name(user: User) -> str:
    """生成评论中的已注销用户名快照。"""
    base_name = (user.nickname or user.username).strip() or user.username.strip() or "用户"
    max_base_length = max(1, 100 - len(已注销后缀))
    return f"{base_name[:max_base_length]}{已注销后缀}"


async def _anonymize_user_comments(user: User, db: AsyncSession) -> None:
    """将用户历史评论匿名化。"""
    result = await db.execute(select(Comment).where(Comment.user_id == user.id))
    comments = result.scalars().all()
    if not comments:
        return

    deleted_name = build_deleted_comment_name(user)
    for comment in comments:
        comment.user = None
        comment.user_id = None
        comment.guest_name = deleted_name


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
    await _anonymize_user_comments(user, db)
    await db.delete(user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_objects_best_effort(storage_keys)
