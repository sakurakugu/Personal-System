"""文章可见性与写权限。"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import and_, or_

from app.modules.articles.models import 文章, 文章状态
from app.modules.users.models import 用户, 用户角色


def 用户可否阅读文章(article: 文章, user: 用户 | None) -> bool:
    """判断当前用户是否可查看文章。"""
    if article.is_deleted:
        return False
    if article.status == 文章状态.public:
        return True
    if article.status == 文章状态.login_required:
        return user is not None
    if user is None:
        return False
    if article.author_id == user.id:
        return True
    return user.role == 用户角色.admin


def 用户可否在博客看到文章(article: 文章, user: 用户 | None) -> bool:
    """判断当前用户是否可在博客列表中看到文章。"""
    if article.is_deleted:
        return False
    if article.status in (文章状态.public, 文章状态.login_required):
        return article.status == 文章状态.public or user is not None
    return (
        user is not None
        and article.author_id == user.id
        and user.settings is not None
        and user.settings.show_private_articles_on_home
    )


def 构建博客可见文章条件(user: 用户 | None):
    """构建博客列表可见文章条件。"""
    deleted_clause = 文章.is_deleted.is_(False)
    if user is None:
        return deleted_clause & (文章.status == 文章状态.public)
    if user.settings is None or not user.settings.show_private_articles_on_home:
        return deleted_clause & 文章.status.in_((文章状态.public, 文章状态.login_required))
    return deleted_clause & or_(
        文章.status.in_((文章状态.public, 文章状态.login_required)),
        and_(
            文章.status == 文章状态.private,
            文章.author_id == user.id,
        ),
    )


def 确保文章写入权限(article: 文章, user: 用户) -> None:
    """校验当前用户是否可修改文章。"""
    if article.author_id == user.id:
        return
    if user.role == 用户角色.admin:
        return
    raise HTTPException(status_code=403, detail="无权操作")
