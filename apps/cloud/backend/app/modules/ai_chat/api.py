"""AI 对话路由。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_chat.schemas import (
    AI调用日志列表,
    AI密钥更新,
    AI设置读取,
    AI设置更新,
    AI测试请求,
    AI测试响应,
)
from app.modules.ai_chat.service import (
    列出AI调用日志,
    执行AI测试,
    更新AI密钥,
    更新AI设置,
    流式生成AI回复,
    读取AI设置,
    解析聊天请求,
    预检AI聊天请求,
)
from app.modules.users.models import 用户
from app.shared.auth.deps import 获取当前用户, 要求超级管理员权限
from app.shared.db.session import get_db

router = APIRouter(tags=["ai"])


@router.post("/ai/chat")
async def AI聊天(
    request: Request,
    messages: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """发送 AI 聊天消息。"""
    json_body: dict[str, Any] | None = None
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        json_body = await request.json()
    body, attachment_count = await 解析聊天请求(json_body=json_body, messages_text=messages, files=files)
    await 预检AI聊天请求(db, user, body)
    return StreamingResponse(
        流式生成AI回复(db, user, body, attachment_count=attachment_count),
        media_type="text/event-stream",
    )


@router.get("/admin/ai/settings", response_model=AI设置读取)
async def 获取AI设置(
    _super_admin: 用户 = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
) -> AI设置读取:
    """获取 AI 设置。"""
    return await 读取AI设置(db)


@router.patch("/admin/ai/settings", response_model=AI设置读取)
async def 保存AI设置(
    body: AI设置更新,
    _super_admin: 用户 = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
) -> AI设置读取:
    """保存 AI 设置。"""
    return await 更新AI设置(db, body)


@router.patch("/admin/ai/secret", response_model=AI设置读取)
async def 保存AI密钥(
    body: AI密钥更新,
    _super_admin: 用户 = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
) -> AI设置读取:
    """保存 AI 密钥。"""
    return await 更新AI密钥(db, body)


@router.post("/admin/ai/test", response_model=AI测试响应)
async def 测试AI配置(
    body: AI测试请求,
    user: 用户 = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
) -> AI测试响应:
    """测试 AI 配置。"""
    return await 执行AI测试(db, user, body)


@router.get("/admin/ai/logs", response_model=AI调用日志列表)
async def 获取AI调用日志(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _super_admin: 用户 = Depends(要求超级管理员权限),
    db: AsyncSession = Depends(get_db),
) -> AI调用日志列表:
    """获取 AI 调用日志。"""
    return await 列出AI调用日志(db, page=page, page_size=page_size)
