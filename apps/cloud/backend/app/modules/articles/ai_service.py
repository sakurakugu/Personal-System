"""文章 AI 辅助服务。"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_chat.schemas import AI消息Part, AI聊天消息
from app.modules.ai_chat.service import 生成AI文本回复
from app.modules.articles.schemas import (
    文章AI元信息建议请求,
    文章AI元信息建议响应,
    文章AI正文润色请求,
    文章AI正文润色响应,
)
from app.modules.users.models import 用户
from app.shared.kernel.logger import get_logger

logger = get_logger(__name__)

文章AI元信息系统提示词 = (
    "你是个人文章编辑助手。"
    "只输出合法 JSON，不要输出 Markdown 代码围栏。"
    "内容必须使用中文，保留用户原有的事实、语气和 Markdown 结构。"
)
文章AI正文润色系统提示词 = (
    "你是个人文章编辑助手。"
    "内容必须使用中文，保留用户原有的事实、语气和 Markdown 结构。"
    "正文输出必须使用用户要求的分隔符协议，不要输出 JSON，不要输出 Markdown 代码围栏包裹整个结果。"
)
润色摘要开始标记 = "<<<SUMMARY>>>"
润色正文开始标记 = "<<<CONTENT>>>"
润色结束标记 = "<<<END>>>"


def _构建AI用户消息(content: str) -> AI聊天消息:
    """构建可承载长文章内容的用户消息。"""
    return AI聊天消息(role="user", parts=[AI消息Part(type="text", text=content)])


def _截断列表(values: list[str], limit: int) -> list[str]:
    """清理并限制字符串列表。"""
    cleaned: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
        if len(cleaned) >= limit:
            break
    return cleaned


def _提取JSON对象(content: str) -> dict[str, Any]:
    """从 AI 文本中提取 JSON 对象。"""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            logger.warning("文章 AI 返回无法解析为 JSON：%s", content[:500])
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 返回不是有效 JSON")
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            logger.warning("文章 AI 返回 JSON 片段解析失败：%s", content[:500])
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 返回不是有效 JSON") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 返回 JSON 必须是对象")
    return data


def _提取润色结果(content: str) -> 文章AI正文润色响应:
    """从 AI 文本中提取润色摘要和完整 Markdown。"""
    text = content.strip()
    summary_start = text.find(润色摘要开始标记)
    content_start = text.find(润色正文开始标记)
    end = text.rfind(润色结束标记)
    if summary_start >= 0 and content_start > summary_start:
        summary = text[summary_start + len(润色摘要开始标记) : content_start].strip()
        content_end = end if end > content_start else len(text)
        polished_content = text[content_start + len(润色正文开始标记) : content_end].strip()
        if polished_content:
            return 文章AI正文润色响应(content=polished_content, summary=summary)

    # 兼容旧提示词或模型主动返回的合法 JSON；不再要求 Markdown 必须经过 JSON 转义。
    try:
        data = _提取JSON对象(content)
        return 文章AI正文润色响应.model_validate(data)
    except HTTPException:
        if text:
            logger.warning("文章 AI 润色未按协议返回，已将完整响应作为 Markdown 正文处理")
            return 文章AI正文润色响应(content=text, summary="AI 未按固定格式返回，已保留完整响应。")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 润色返回内容为空")


def _构建上下文(body: 文章AI元信息建议请求 | 文章AI正文润色请求) -> str:
    """构建文章上下文文本。"""
    category_names = "、".join(_截断列表(body.category_names, 200)) or "无"
    tag_names = "、".join(_截断列表(body.tag_names, 500)) or "无"
    return (
        f"当前标题：{(body.title or '').strip() or '未填写'}\n"
        f"当前摘要：{(body.excerpt or '').strip() or '未填写'}\n"
        f"已有分类：{category_names}\n"
        f"已有标签：{tag_names}\n"
        "正文如下：\n"
        f"{body.content}"
    )


async def 生成文章元信息建议(
    db: AsyncSession,
    user: 用户,
    body: 文章AI元信息建议请求,
) -> 文章AI元信息建议响应:
    """根据文章正文生成标题、摘要、分类和标签建议。"""
    user_prompt = (
        "请根据文章正文生成元信息。要求：\n"
        "1. 返回 JSON 字段：title、excerpt、category_name、tag_names、reason。\n"
        "2. title 不超过 40 个中文字符，清晰具体。\n"
        "3. excerpt 为 80 到 160 个中文字符，适合博客列表展示。\n"
        "4. category_name 优先从已有分类中选择；确实没有合适分类时返回一个新分类名。\n"
        "5. tag_names 返回 3 到 8 个标签，优先复用已有标签。\n"
        "6. reason 用一句话说明建议依据。\n\n"
        f"{_构建上下文(body)}"
    )
    content = await 生成AI文本回复(
        db,
        user,
        [
            AI聊天消息(role="system", content=文章AI元信息系统提示词),
            _构建AI用户消息(user_prompt),
        ],
        log_name="article_metadata_suggest",
    )
    data = _提取JSON对象(content)
    if isinstance(data.get("tag_names"), list):
        data["tag_names"] = _截断列表([str(item) for item in data["tag_names"]], 12)
    return 文章AI元信息建议响应.model_validate(data)


async def 润色文章正文(
    db: AsyncSession,
    user: 用户,
    body: 文章AI正文润色请求,
) -> 文章AI正文润色响应:
    """润色文章正文并返回完整 Markdown。"""
    logger.info(
        "文章 AI 润色开始 user_id=%s content_length=%s",
        user.id,
        len(body.content),
    )
    user_prompt = (
        "请润色下面的 Markdown 正文。要求：\n"
        f"1. 必须按固定格式返回：先输出 {润色摘要开始标记}，下一行输出一句话摘要；"
        f"再输出 {润色正文开始标记}，下一行开始输出完整润色后的 Markdown；"
        f"最后单独输出 {润色结束标记}。\n"
        "2. Markdown 正文不要做 JSON 转义，不要省略任何段落。\n"
        "3. 保留代码块、图片链接、表格、frontmatter、标题层级和自定义 Markdown 语法。\n"
        "4. 优化病句、错别字、衔接和表达清晰度，不要虚构事实。\n"
        "5. 除固定分隔符、摘要和正文外，不要输出任何解释。\n\n"
        f"{_构建上下文(body)}"
    )
    content = await 生成AI文本回复(
        db,
        user,
        [
            AI聊天消息(role="system", content=文章AI正文润色系统提示词),
            _构建AI用户消息(user_prompt),
        ],
        log_name="article_content_polish",
    )
    result = _提取润色结果(content)
    logger.info(
        "文章 AI 润色完成 user_id=%s result_length=%s summary_length=%s",
        user.id,
        len(result.content),
        len(result.summary),
    )
    return result
