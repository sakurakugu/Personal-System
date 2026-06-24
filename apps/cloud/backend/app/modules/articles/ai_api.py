"""文章 AI 辅助路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.articles.ai_service import 生成文章元信息建议, 润色文章正文
from app.modules.articles.schemas import (
    文章AI元信息建议请求,
    文章AI元信息建议响应,
    文章AI正文润色请求,
    文章AI正文润色响应,
)
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db
from app.shared.kernel.logger import get_logger

router = APIRouter(prefix="/articles/ai", tags=["articles"])
logger = get_logger(__name__)


@router.post("/suggest-metadata", response_model=文章AI元信息建议响应)
async def 建议文章元信息(
    body: 文章AI元信息建议请求,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
) -> 文章AI元信息建议响应:
    """根据当前编辑内容生成文章元信息建议。"""
    logger.info("文章 AI 元信息接口收到请求 user_id=%s content_length=%s", user.id, len(body.content))
    return await 生成文章元信息建议(db, user, body)


@router.post("/polish-content", response_model=文章AI正文润色响应)
async def AI润色文章正文(
    body: 文章AI正文润色请求,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
) -> 文章AI正文润色响应:
    """根据当前编辑内容润色文章正文。"""
    logger.info("文章 AI 润色接口收到请求 user_id=%s content_length=%s", user.id, len(body.content))
    return await 润色文章正文(db, user, body)
