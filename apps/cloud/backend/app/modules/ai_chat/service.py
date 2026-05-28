"""AI 对话服务。"""

from __future__ import annotations

import json
import base64
import hashlib
from collections.abc import AsyncIterator
from datetime import datetime, time, timezone
from time import perf_counter
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_chat.models import AI调用日志, AI设置
from app.modules.ai_chat.schemas import (
    AI聊天消息,
    AI聊天请求,
    AI调用日志列表,
    AI调用日志读取,
    AI密钥更新,
    AI设置读取,
    AI设置更新,
    AI测试请求,
    AI测试响应,
)
from app.modules.users.models import 用户, 用户角色
from app.shared.kernel.config import settings
from app.shared.kernel.logger import get_logger

AI设置主键 = 1
默认AI访问策略 = "login"
默认AI供应商 = "openai_compatible"
默认AI接口地址 = "https://api.openai.com/v1"
默认AI模型 = ""
默认AI最大生成Token = 1024
默认AI超时秒数 = 30.0
默认AI系统提示词 = "你是个人系统里的中文助手，回答要简洁、准确，并优先帮助用户完成实际任务。"
默认AI允许附件 = False
默认AI最大附件大小MB = 10
默认AI用户每日限制 = 10000
logger = get_logger(__name__)


def _当前时间() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def _构建密钥加密器() -> Fernet:
    """用认证主密钥派生 AI 密钥加密器。"""
    digest = hashlib.sha256(settings.AUTH_SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _加密AI密钥(secret: str) -> str:
    """加密 AI 供应商密钥。"""
    return _构建密钥加密器().encrypt(secret.encode("utf-8")).decode("utf-8")


def _解密AI密钥(secret_ciphertext: str) -> str:
    """解密 AI 供应商密钥。"""
    try:
        return _构建密钥加密器().decrypt(secret_ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        logger.warning("AI 密钥解密失败，请重新保存密钥")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI 密钥无法解密，请重新保存") from exc


def _默认设置() -> AI设置:
    """构造默认 AI 设置。"""
    return AI设置(
        id=AI设置主键,
        enabled=False,
        access_policy=默认AI访问策略,
        provider=默认AI供应商,
        base_url=默认AI接口地址,
        model=默认AI模型,
        max_tokens=默认AI最大生成Token,
        timeout_seconds=默认AI超时秒数,
        system_prompt=默认AI系统提示词,
        allow_attachments=默认AI允许附件,
        max_attachment_size_mb=默认AI最大附件大小MB,
        daily_limit_per_user=默认AI用户每日限制,
    )


async def 获取或创建AI设置(db: AsyncSession) -> AI设置:
    """读取 AI 设置，不存在时按环境变量初始化。"""
    result = await db.execute(select(AI设置).where(AI设置.id == AI设置主键))
    setting = result.scalar_one_or_none()
    if setting is not None:
        return setting
    setting = _默认设置()
    db.add(setting)
    await db.flush()
    return setting


def 构建AI设置读取(setting: AI设置) -> AI设置读取:
    """构建不包含明文密钥的 AI 设置响应。"""
    return AI设置读取(
        enabled=setting.enabled,
        access_policy=setting.access_policy,  # type: ignore[arg-type]
        provider=setting.provider,
        base_url=setting.base_url,
        model=setting.model,
        max_tokens=setting.max_tokens,
        timeout_seconds=setting.timeout_seconds,
        system_prompt=setting.system_prompt,
        allow_attachments=setting.allow_attachments,
        max_attachment_size_mb=setting.max_attachment_size_mb,
        daily_limit_per_user=setting.daily_limit_per_user,
        has_secret=bool(setting.secret_ciphertext),
        secret_updated_at=setting.secret_updated_at,
        updated_at=setting.updated_at,
    )


async def 读取AI设置(db: AsyncSession) -> AI设置读取:
    """读取 AI 设置。"""
    return 构建AI设置读取(await 获取或创建AI设置(db))


async def 更新AI设置(db: AsyncSession, body: AI设置更新) -> AI设置读取:
    """更新 AI 设置。"""
    setting = await 获取或创建AI设置(db)
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        if key == "base_url" and isinstance(value, str):
            value = value.rstrip("/")
        setattr(setting, key, value)
    await db.flush()
    return 构建AI设置读取(setting)


async def 更新AI密钥(db: AsyncSession, body: AI密钥更新) -> AI设置读取:
    """更新 AI 供应商密钥。"""
    setting = await 获取或创建AI设置(db)
    setting.secret_ciphertext = _加密AI密钥(body.secret.strip())
    setting.secret_updated_at = _当前时间()
    await db.flush()
    return 构建AI设置读取(setting)


def 校验AI访问权限(setting: AI设置, user: 用户) -> None:
    """按访问策略校验当前用户。"""
    if setting.access_policy == "super_admin" and user.role != 用户角色.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI 对话需要超级管理员权限")
    if setting.access_policy == "admin" and user.role not in (用户角色.admin, 用户角色.super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI 对话需要管理员权限")


def _从消息提取内容(message: AI聊天消息) -> str:
    """从兼容消息格式中提取文本内容。"""
    if message.content:
        return message.content
    if not message.parts:
        return ""
    parts = [part.text.strip() for part in message.parts if part.type == "text" and part.text]
    return "\n".join(part for part in parts if part)


def _构建供应商消息(setting: AI设置, messages: list[AI聊天消息]) -> list[dict[str, str]]:
    """构建 OpenAI 兼容接口消息数组。"""
    provider_messages: list[dict[str, str]] = []
    system_prompt = setting.system_prompt.strip()
    if system_prompt:
        provider_messages.append({"role": "system", "content": system_prompt})
    for message in messages:
        content = _从消息提取内容(message)
        if not content:
            continue
        provider_messages.append({"role": message.role, "content": content})
    if not provider_messages or all(item["role"] != "user" for item in provider_messages):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少用户消息")
    return provider_messages


async def 记录AI调用日志(
    db: AsyncSession,
    *,
    user: 用户 | None,
    setting: AI设置,
    status_value: str,
    duration_ms: int,
    message_count: int,
    attachment_count: int,
    usage: dict[str, Any] | None = None,
    error: Exception | None = None,
) -> None:
    """记录 AI 调用日志。"""
    error_message = str(error) if error else None
    if error_message and len(error_message) > 2000:
        error_message = f"{error_message[:2000]}..."
    db.add(
        AI调用日志(
            user_id=user.id if user else None,
            provider=setting.provider,
            model=setting.model,
            status=status_value,
            prompt_tokens=usage.get("prompt_tokens") if usage else None,
            completion_tokens=usage.get("completion_tokens") if usage else None,
            total_tokens=usage.get("total_tokens") if usage else None,
            duration_ms=duration_ms,
            message_count=message_count,
            attachment_count=attachment_count,
            error_type=type(error).__name__ if error else None,
            error_message=error_message,
        )
    )
    await db.flush()


def _构建供应商请求(setting: AI设置, messages: list[AI聊天消息], *, stream: bool) -> tuple[str, dict[str, Any], dict[str, str]]:
    """构建 OpenAI 兼容聊天请求参数。"""
    if not setting.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI 对话未启用")
    if not setting.secret_ciphertext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI 密钥未配置")
    if not setting.base_url or not setting.model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI 模型配置不完整")

    url = f"{setting.base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": setting.model,
        "messages": _构建供应商消息(setting, messages),
        "max_tokens": setting.max_tokens,
        "stream": stream,
    }
    headers = {
        "Authorization": f"Bearer {_解密AI密钥(setting.secret_ciphertext)}",
        "Content-Type": "application/json",
    }
    return url, payload, headers


async def 校验每日调用额度(db: AsyncSession, setting: AI设置, user: 用户) -> None:
    """校验当前用户每日 AI 调用额度。"""
    if setting.daily_limit_per_user <= 0:
        return
    today_start = datetime.combine(_当前时间().date(), time.min, tzinfo=timezone.utc)
    result = await db.execute(
        select(func.count())
        .select_from(AI调用日志)
        .where(
            AI调用日志.user_id == user.id,
            AI调用日志.created_at >= today_start,
        )
    )
    used_count = int(result.scalar_one() or 0)
    if used_count >= setting.daily_limit_per_user:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="今日 AI 调用次数已用完")


async def 预检AI聊天请求(db: AsyncSession, user: 用户, body: AI聊天请求) -> None:
    """在建立 SSE 响应前校验 AI 聊天请求。"""
    setting = await 获取或创建AI设置(db)
    校验AI访问权限(setting, user)
    await 校验每日调用额度(db, setting, user)
    _构建供应商请求(setting, body.messages, stream=True)


def _编码SSE数据(data: str | dict[str, Any]) -> bytes:
    """编码 SSE data 行。"""
    if isinstance(data, str):
        payload = data
    else:
        payload = json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n".encode("utf-8")


def _提取供应商增量(line: str) -> str:
    """从 OpenAI 兼容 SSE 行提取增量文本。"""
    normalized = line.strip()
    if not normalized.startswith("data:"):
        return ""
    payload = normalized.removeprefix("data:").strip()
    if not payload or payload == "[DONE]":
        return ""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return ""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    delta = choices[0].get("delta")
    if isinstance(delta, dict) and isinstance(delta.get("content"), str):
        return delta["content"]
    return ""


async def 流式生成AI回复(
    db: AsyncSession,
    user: 用户,
    body: AI聊天请求,
    *,
    attachment_count: int,
) -> AsyncIterator[bytes]:
    """以 SSE 形式生成 AI 回复。"""
    setting = await 获取或创建AI设置(db)
    校验AI访问权限(setting, user)
    await 校验每日调用额度(db, setting, user)
    started_at = perf_counter()
    usage: dict[str, Any] | None = None
    logger.info(
        "AI 对话开始 user_id=%s provider=%s model=%s message_count=%s attachment_count=%s",
        user.id,
        setting.provider,
        setting.model,
        len(body.messages),
        attachment_count,
    )
    try:
        url, payload, headers = _构建供应商请求(setting, body.messages, stream=True)
        async with httpx.AsyncClient(timeout=httpx.Timeout(setting.timeout_seconds)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    delta = _提取供应商增量(line)
                    if delta:
                        yield _编码SSE数据({"delta": delta})
        duration_ms = round((perf_counter() - started_at) * 1000)
        await 记录AI调用日志(
            db,
            user=user,
            setting=setting,
            status_value="success",
            duration_ms=duration_ms,
            message_count=len(body.messages),
            attachment_count=attachment_count,
            usage=usage,
        )
        await db.commit()
        logger.info(
            "AI 对话完成 user_id=%s provider=%s model=%s duration_ms=%s",
            user.id,
            setting.provider,
            setting.model,
            duration_ms,
        )
        yield _编码SSE数据("[DONE]")
    except Exception as exc:
        duration_ms = round((perf_counter() - started_at) * 1000)
        await 记录AI调用日志(
            db,
            user=user,
            setting=setting,
            status_value="error",
            duration_ms=duration_ms,
            message_count=len(body.messages),
            attachment_count=attachment_count,
            error=exc,
        )
        await db.commit()
        logger.warning(
            "AI 对话失败 user_id=%s provider=%s model=%s duration_ms=%s error_type=%s",
            user.id,
            setting.provider,
            setting.model,
            duration_ms,
            type(exc).__name__,
            exc_info=True,
        )
        yield _编码SSE数据({"delta": f"AI 请求失败：{exc}"})
        yield _编码SSE数据("[DONE]")


async def 执行AI测试(db: AsyncSession, user: 用户, body: AI测试请求) -> AI测试响应:
    """执行后台 AI 测试请求。"""
    setting = await 获取或创建AI设置(db)
    校验AI访问权限(setting, user)
    await 校验每日调用额度(db, setting, user)
    request_body = AI聊天请求(messages=[AI聊天消息(role="user", content=body.message)])
    started_at = perf_counter()
    logger.info(
        "AI 配置测试开始 user_id=%s provider=%s model=%s",
        user.id,
        setting.provider,
        setting.model,
    )
    try:
        url, payload, headers = _构建供应商请求(setting, request_body.messages, stream=False)
        async with httpx.AsyncClient(timeout=httpx.Timeout(setting.timeout_seconds)) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices", [])
        content = ""
        if choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                content = str(message.get("content") or "")
        duration_ms = round((perf_counter() - started_at) * 1000)
        await 记录AI调用日志(
            db,
            user=user,
            setting=setting,
            status_value="success",
            duration_ms=duration_ms,
            message_count=1,
            attachment_count=0,
            usage=data.get("usage") if isinstance(data.get("usage"), dict) else None,
        )
        logger.info(
            "AI 配置测试完成 user_id=%s provider=%s model=%s duration_ms=%s",
            user.id,
            setting.provider,
            setting.model,
            duration_ms,
        )
        return AI测试响应(content=content or "接口已响应，但没有返回文本。", duration_ms=duration_ms)
    except Exception as exc:
        duration_ms = round((perf_counter() - started_at) * 1000)
        await 记录AI调用日志(
            db,
            user=user,
            setting=setting,
            status_value="error",
            duration_ms=duration_ms,
            message_count=1,
            attachment_count=0,
            error=exc,
        )
        logger.warning(
            "AI 配置测试失败 user_id=%s provider=%s model=%s duration_ms=%s error_type=%s",
            user.id,
            setting.provider,
            setting.model,
            duration_ms,
            type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI 测试失败：{exc}") from exc


async def 解析聊天请求(
    *,
    json_body: dict[str, Any] | None,
    messages_text: str | None,
    files: list[UploadFile] | None,
) -> tuple[AI聊天请求, int]:
    """兼容 JSON 与 multipart/form-data 请求体。"""
    attachment_count = len(files or [])
    if attachment_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前 AI 对话接口暂不支持附件")
    if messages_text is not None:
        try:
            messages_data = json.loads(messages_text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages 不是有效 JSON") from exc
        return AI聊天请求(messages=messages_data), attachment_count
    return AI聊天请求.model_validate(json_body or {}), attachment_count


async def 列出AI调用日志(db: AsyncSession, *, page: int, page_size: int) -> AI调用日志列表:
    """分页列出 AI 调用日志。"""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total_result = await db.execute(select(func.count()).select_from(AI调用日志))
    total = int(total_result.scalar_one() or 0)
    query: Select[tuple[AI调用日志]] = (
        select(AI调用日志)
        .order_by(AI调用日志.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = [AI调用日志读取.model_validate(item) for item in result.scalars().all()]
    pages = (total + page_size - 1) // page_size if total else 0
    return AI调用日志列表(items=items, total=total, page=page, page_size=page_size, pages=pages)
