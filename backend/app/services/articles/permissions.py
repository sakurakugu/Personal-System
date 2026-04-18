"""文章可见性与写权限。"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import and_, or_

from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole


def can_user_read_article(article: Article, user: User | None) -> bool:
    """判断当前用户是否可查看文章。"""
    if article.status == ArticleStatus.public:
        return True
    if article.status == ArticleStatus.login_required:
        return user is not None
    if user is None:
        return False
    if article.author_id == user.id:
        return True
    return user.role in (UserRole.admin, UserRole.super_admin)


def can_user_see_article_in_blog(article: Article, user: User | None) -> bool:
    """判断当前用户是否可在博客列表中看到文章。"""
    if article.status in (ArticleStatus.public, ArticleStatus.login_required):
        return article.status == ArticleStatus.public or user is not None
    return (
        user is not None
        and article.author_id == user.id
        and user.settings is not None
        and user.settings.show_private_articles_on_home
    )


def build_blog_visible_article_clause(user: User | None):
    """构建博客列表可见文章条件。"""
    if user is None:
        return Article.status == ArticleStatus.public
    if user.settings is None or not user.settings.show_private_articles_on_home:
        return Article.status.in_((ArticleStatus.public, ArticleStatus.login_required))
    return or_(
        Article.status.in_((ArticleStatus.public, ArticleStatus.login_required)),
        and_(
            Article.status == ArticleStatus.private,
            Article.author_id == user.id,
        ),
    )


def ensure_article_write_permission(article: Article, user: User) -> None:
    """校验当前用户是否可修改文章。"""
    if article.author_id == user.id:
        return
    if user.role in (UserRole.admin, UserRole.super_admin):
        return
    raise HTTPException(status_code=403, detail="无权操作")
