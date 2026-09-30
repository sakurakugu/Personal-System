"""从文章生成待办或资料。"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.models import 文章, 文章转换记录
from app.modules.articles.permissions import 确保文章写入权限
from app.modules.articles.queries import 获取文章或404
from app.modules.articles.schemas import 文章转待办请求, 文章转资料请求, 文章转换信息
from app.modules.materials.schemas import 资料创建
from app.modules.materials.service import 创建资料
from app.modules.todos.schemas import TodoCreate
from app.modules.todos.service import create_todo
from app.modules.users.models import 用户

logger = logging.getLogger(__name__)


async def _锁定文章(db: AsyncSession, article_id: str, user: 用户) -> 文章:
    await db.execute(select(文章.id).where(文章.id == article_id, 文章.author_id == user.id).with_for_update())
    article = await 获取文章或404(db, article_id)
    确保文章写入权限(article, user)
    return article


async def _记录转换(db: AsyncSession, article: 文章, target_type: str, target_id) -> 文章转换信息:
    record = 文章转换记录(article_id=article.id, target_type=target_type, target_id=target_id)
    db.add(record)
    article.organization_state = "organized"
    article.archived_at = None
    await db.flush()
    logger.info("文章转换完成，文章=%s，目标类型=%s，目标=%s", article.id, target_type, target_id)
    return 文章转换信息.model_validate(record)


async def 文章转待办(db: AsyncSession, article_id: str, user: 用户, body: 文章转待办请求) -> 文章转换信息:
    """复制文章内容生成待办并建立关联。"""
    article = await _锁定文章(db, article_id, user)
    todo = await create_todo(db, user, TodoCreate(**body.model_dump()))
    return await _记录转换(db, article, "todo", todo.id)


async def 文章转资料(db: AsyncSession, article_id: str, user: 用户, body: 文章转资料请求) -> 文章转换信息:
    """复制文章内容生成资料并建立关联。"""
    article = await _锁定文章(db, article_id, user)
    material = await 创建资料(db, user, 资料创建(**body.model_dump()))
    return await _记录转换(db, article, "material", material.id)
