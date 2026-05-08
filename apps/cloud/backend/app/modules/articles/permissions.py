"""文章可见性与写权限。"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import and_, or_

from app.modules.articles.models import Article, ArticleStatus
from app.modules.users.models import User, UserRole


def 用户可否阅读文章(article: Article, user: User | None) -> bool:
    """判断当前用户是否可查看文章。"""
    if article.is_deleted:
        return False
    if article.status == ArticleStatus.public:
        return True
    if article.status == ArticleStatus.login_required:
        return user is not None
    if user is None:
        return False
    if article.author_id == user.id:
        return True
    return user.role in (UserRole.admin, UserRole.super_admin)


def 用户可否在博客看到文章(article: Article, user: User | None) -> bool:
    """判断当前用户是否可在博客列表中看到文章。"""
    if article.is_deleted:
        return False
    if article.status in (ArticleStatus.public, ArticleStatus.login_required):
        return article.status == ArticleStatus.public or user is not None
    return (
        user is not None
        and article.author_id == user.id
        and user.settings is not None
        and user.settings.show_private_articles_on_home
    )


def 构建博客可见文章条件(user: User | None):
    """构建博客列表可见文章条件。"""
    deleted_clause = Article.is_deleted.is_(False)
    if user is None:
        return deleted_clause & (Article.status == ArticleStatus.public)
    if user.settings is None or not user.settings.show_private_articles_on_home:
        return deleted_clause & Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
    return deleted_clause & or_(
        Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
        and_(
            Article.status == ArticleStatus.private,
            Article.author_id == user.id,
        ),
    )


def 确保文章写入权限(article: Article, user: User) -> None:
    """校验当前用户是否可修改文章。"""
    if article.author_id == user.id:
        return
    if user.role in (UserRole.admin, UserRole.super_admin):
        return
    raise HTTPException(status_code=403, detail="无权操作")
