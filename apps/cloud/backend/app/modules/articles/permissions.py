"""文章写入权限与博客发布可见性。"""

from fastapi import HTTPException

from app.modules.articles.models import 文章, 博客发布
from app.modules.users.models import 用户


def 用户可否阅读文章(article: 文章 | 博客发布, user: 用户 | None) -> bool:
    """文章仅作者可读；博客只开放已发布快照。"""
    if article.is_deleted:
        return False
    if isinstance(article, 文章):
        return user is not None and article.author_id == user.id
    return article.is_published and (article.status == "public" or user is not None)


def 用户可否在博客看到文章(article: 博客发布, user: 用户 | None) -> bool:
    """博客列表遵循发布快照权限。"""
    return 用户可否阅读文章(article, user)


def 构建博客可见文章条件(user: 用户 | None):
    """查询只使用已发布且文章未删除的快照。"""
    condition = 博客发布.is_published.is_(True) & 博客发布.article.has(文章.is_deleted.is_(False))
    if user is None:
        condition &= 博客发布.status == "public"
    return condition


def 确保文章写入权限(article: 文章, user: 用户) -> None:
    """校验当前用户是否可修改文章。"""
    if article.author_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作")
