"""文章相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.article_content import (
    定位正文片段,
    替换正文片段,
    构建正文摘要,
    解析Markdown大纲,
    计算片段哈希,
)
from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.articles.schemas import 文章创建, 文章更新
from app.modules.articles.service import 创建文章, 列出我的文章, 获取我的文章, 更新文章


class 文章列表参数(BaseModel):
    """我的文章列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class 文章ID参数(BaseModel):
    """单篇文章 ID 参数。"""

    article_id: str = Field(description="文章 ID")


class 文章内容读取参数(文章ID参数):
    """文章正文读取参数。"""

    mode: Literal["metadata", "outline", "excerpt", "heading", "line_range", "full"] = Field(
        default="metadata",
        description="读取模式，full 必须显式指定 reason",
    )
    reason: str | None = Field(default=None, description="读取完整正文的原因")
    heading_path: list[str] | None = Field(default=None, description="标题路径")
    start_line: int | None = Field(default=None, ge=1, description="起始行号")
    end_line: int | None = Field(default=None, ge=1, description="结束行号")
    excerpt_length: int = Field(default=500, ge=1, le=5000, description="正文摘录最大长度")


class 文章元信息更新参数(文章ID参数):
    """文章元信息更新参数。"""

    title: str | None = Field(default=None, max_length=300)
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: str | None = None
    tag_ids: list[str] | None = None


class 文章全文替换参数(文章ID参数):
    """文章全文替换参数。"""

    expected_last_edited_at: str = Field(description="调用方读取到的 last_edited_at")
    content: str = Field(description="新的完整 Markdown 正文")


class 文章定位参数(BaseModel):
    """文章局部正文定位参数。"""

    type: Literal["heading", "line_range", "text_anchor"]
    heading_path: list[str] | None = None
    start_line: int | None = None
    end_line: int | None = None
    text: str | None = None
    before_text: str | None = None
    after_text: str | None = None


class 文章局部替换参数(文章ID参数):
    """文章局部正文替换参数。"""

    expected_last_edited_at: str = Field(description="调用方读取到的 last_edited_at")
    target: 文章定位参数
    expected_hash: str = Field(description="当前目标片段 sha256 哈希")
    replacement: str = Field(description="新的 Markdown 片段")


def _获取MCP会话(context: MCP调用上下文):
    """获取当前 MCP 运行时数据库会话。"""
    if context.db is None:
        raise RuntimeError("MCP 工具缺少数据库会话")
    return context.db


def _解析时间戳(value: str) -> datetime:
    """解析 ISO 时间戳。"""
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expected_last_edited_at 格式无效") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _转UTC(value: datetime) -> datetime:
    """将数据库时间戳转为 UTC。"""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _校验最后编辑时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的文章编辑时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "文章已被更新，请重新读取后再修改",
                "current_last_edited_at": actual.isoformat(),
            },
        )


def _文章元信息(article: Any) -> dict[str, Any]:
    """序列化文章元信息，不包含正文。"""
    return {
        "id": str(article.id),
        "title": article.title,
        "slug": article.slug,
        "excerpt": article.excerpt,
        "cover_url": article.cover_url,
        "status": article.status.value if hasattr(article.status, "value") else article.status,
        "view_count": article.view_count,
        "like_count": article.like_count,
        "word_count": article.word_count,
        "category": {
            "id": str(article.category.id),
            "name": article.category.name,
            "slug": article.category.slug,
        }
        if article.category
        else None,
        "tags": [
            {
                "id": str(tag.id),
                "name": tag.name,
                "slug": tag.slug,
            }
            for tag in article.tags
        ],
        "is_deleted": article.is_deleted,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "created_at": article.created_at.isoformat(),
        "last_edited_at": article.last_edited_at.isoformat(),
        "updated_at": article.updated_at.isoformat(),
    }


def _文章撤销快照(article: Any, *, include_content: bool = False) -> dict[str, Any]:
    """构建文章撤销快照。"""
    data = _文章元信息(article)
    data["category_id"] = str(article.category_id) if article.category_id else None
    data["tag_ids"] = [str(tag.id) for tag in article.tags]
    data["content_summary"] = 构建正文摘要(article.content)
    if include_content:
        data["content"] = article.content
    return data


def _元信息更新载荷(args: dict[str, Any]) -> 文章更新:
    """从 MCP 参数构建文章元信息更新载荷。"""
    allowed = {"title", "excerpt", "cover_url", "status", "category_id", "tag_ids"}
    payload = {key: value for key, value in args.items() if key in allowed}
    return 文章更新.model_validate(payload)


async def articles_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户自己的文章列表。"""
    body = 文章列表参数.model_validate(args)
    response = await 列出我的文章(_获取MCP会话(context), page=body.page, page_size=body.page_size, user=context.user)
    return {
        "items": [item.model_dump(mode="json") for item in response.items],
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "pages": response.pages,
    }


async def articles_summary_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取文章元信息和摘要，不返回正文。"""
    body = 文章ID参数.model_validate(args)
    article = await 获取我的文章(_获取MCP会话(context), body.article_id, context.user)
    return _文章元信息(article)


async def articles_outline_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取文章 Markdown 标题大纲。"""
    body = 文章ID参数.model_validate(args)
    article = await 获取我的文章(_获取MCP会话(context), body.article_id, context.user)
    return {
        "article": _文章元信息(article),
        "outline": 解析Markdown大纲(article.content),
        "content_summary": 构建正文摘要(article.content),
    }


async def articles_content_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """按需读取文章正文。"""
    body = 文章内容读取参数.model_validate(args)
    article = await 获取我的文章(_获取MCP会话(context), body.article_id, context.user)
    metadata = _文章元信息(article)

    if body.mode == "metadata":
        return metadata
    if body.mode == "outline":
        return {
            "article": metadata,
            "outline": 解析Markdown大纲(article.content),
            "content_summary": 构建正文摘要(article.content),
        }
    if body.mode == "excerpt":
        content_excerpt = article.content[: body.excerpt_length]
        return {
            "article": metadata,
            "excerpt": article.excerpt,
            "content_excerpt": content_excerpt,
            "content_summary": 构建正文摘要(article.content),
            "excerpt_hash": 计算片段哈希(content_excerpt),
        }
    if body.mode == "heading":
        fragment = 定位正文片段(article.content, {"type": "heading", "heading_path": body.heading_path})
        return {
            "article": metadata,
            "target": fragment.target,
            "content": fragment.content,
            "hash": 计算片段哈希(fragment.content),
            "start_line": fragment.start_line,
            "end_line": fragment.end_line,
        }
    if body.mode == "line_range":
        fragment = 定位正文片段(
            article.content,
            {"type": "line_range", "start_line": body.start_line, "end_line": body.end_line},
        )
        return {
            "article": metadata,
            "target": fragment.target,
            "content": fragment.content,
            "hash": 计算片段哈希(fragment.content),
            "start_line": fragment.start_line,
            "end_line": fragment.end_line,
        }
    if not body.reason or not body.reason.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="读取完整正文必须提供 reason")
    return {
        "article": metadata,
        "content": article.content,
        "hash": 计算片段哈希(article.content),
        "content_summary": 构建正文摘要(article.content),
    }


async def articles_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建文章。"""
    body = 文章创建.model_validate(args)
    article = await 创建文章(_获取MCP会话(context), body, context.user)
    after = _文章撤销快照(article)
    return {
        "summary": f"已创建文章：{article.title}",
        "target": {"type": "article", "id": str(article.id)},
        "undoable": True,
        "undo_tool_name": "articles.delete",
        "after": after,
        "data": _文章元信息(article),
    }


async def articles_metadata_update(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新文章元信息，不修改正文。"""
    body = 文章元信息更新参数.model_validate(args)
    db = _获取MCP会话(context)
    before_article = await 获取我的文章(db, body.article_id, context.user)
    before = _文章撤销快照(before_article)
    article = await 更新文章(db, body.article_id, _元信息更新载荷(args), context.user)
    after = _文章撤销快照(article)
    return {
        "summary": f"已更新文章元信息：{article.title}",
        "target": {"type": "article", "id": str(article.id)},
        "undoable": True,
        "undo_tool_name": "articles.metadata.update",
        "before": before,
        "after": after,
        "data": _文章元信息(article),
    }


async def articles_content_replace(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """替换文章完整正文。"""
    body = 文章全文替换参数.model_validate(args)
    db = _获取MCP会话(context)
    before_article = await 获取我的文章(db, body.article_id, context.user)
    _校验最后编辑时间(before_article.last_edited_at, body.expected_last_edited_at)
    before = _文章撤销快照(before_article, include_content=True)
    article = await 更新文章(db, body.article_id, 文章更新(content=body.content), context.user)
    after = _文章撤销快照(article, include_content=True)
    return {
        "summary": f"已替换文章正文：{article.title}",
        "target": {"type": "article", "id": str(article.id)},
        "undoable": True,
        "undo_tool_name": "articles.content.replace",
        "before": before,
        "after": after,
        "data": {
            "article": _文章元信息(article),
            "content_summary": 构建正文摘要(article.content),
        },
    }


async def articles_content_patch(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """局部替换文章正文。"""
    body = 文章局部替换参数.model_validate(args)
    db = _获取MCP会话(context)
    before_article = await 获取我的文章(db, body.article_id, context.user)
    _校验最后编辑时间(before_article.last_edited_at, body.expected_last_edited_at)
    target = body.target.model_dump(exclude_none=True)
    fragment = 定位正文片段(before_article.content, target)
    current_hash = 计算片段哈希(fragment.content)
    if current_hash != body.expected_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "目标片段哈希不一致，请重新读取后再修改",
                "current_hash": current_hash,
                "current_excerpt": fragment.content[:500],
                "start_line": fragment.start_line,
                "end_line": fragment.end_line,
            },
        )

    before = {
        **_文章撤销快照(before_article),
        "target": fragment.target,
        "fragment": fragment.content,
        "fragment_hash": current_hash,
        "start_index": fragment.start_index,
        "end_index": fragment.end_index,
        "start_line": fragment.start_line,
        "end_line": fragment.end_line,
    }
    new_content = 替换正文片段(before_article.content, fragment, body.replacement)
    article = await 更新文章(db, body.article_id, 文章更新(content=new_content), context.user)
    after = {
        **_文章撤销快照(article),
        "target": fragment.target,
        "fragment": body.replacement,
        "fragment_hash": 计算片段哈希(body.replacement),
        "start_index": fragment.start_index,
        "end_index": fragment.start_index + len(body.replacement),
        "start_line": fragment.start_line,
        "end_line": fragment.start_line + len(body.replacement.splitlines()) - 1,
    }
    return {
        "summary": f"已局部更新文章正文：{article.title}",
        "target": {"type": "article", "id": str(article.id)},
        "undoable": True,
        "undo_tool_name": "articles.content.patch",
        "before": before,
        "after": after,
        "data": {
            "article": _文章元信息(article),
            "target": fragment.target,
            "content_summary": 构建正文摘要(article.content),
            "new_fragment_hash": after["fragment_hash"],
        },
    }


注册工具(
    MCP工具定义(
        name="articles.list",
        description="查询当前用户未删除文章列表，只返回元信息和摘要，不返回正文。",
        input_schema=文章列表参数.model_json_schema(),
        permission="readonly",
        handler=articles_list,
    )
)
注册工具(
    MCP工具定义(
        name="articles.summary.get",
        description="读取当前用户一篇文章的元信息、摘要、标签、分类和编辑时间，不返回正文。",
        input_schema=文章ID参数.model_json_schema(),
        permission="readonly",
        handler=articles_summary_get,
    )
)
注册工具(
    MCP工具定义(
        name="articles.outline.get",
        description="读取当前用户一篇文章的 Markdown 标题大纲和片段哈希，不返回完整正文。",
        input_schema=文章ID参数.model_json_schema(),
        permission="readonly",
        handler=articles_outline_get,
    )
)
注册工具(
    MCP工具定义(
        name="articles.content.get",
        description="按 metadata、outline、excerpt、heading、line_range 或 full 模式读取文章正文。",
        input_schema=文章内容读取参数.model_json_schema(),
        permission="readonly",
        handler=articles_content_get,
    )
)
注册工具(
    MCP工具定义(
        name="articles.create",
        description="为当前用户创建文章，未指定 status 时创建私有文章。",
        input_schema=文章创建.model_json_schema(),
        permission="full",
        handler=articles_create,
    )
)
注册工具(
    MCP工具定义(
        name="articles.metadata.update",
        description="更新当前用户文章的标题、摘要、封面、状态、分类和标签，不修改正文。",
        input_schema=文章元信息更新参数.model_json_schema(),
        permission="full",
        handler=articles_metadata_update,
    )
)
注册工具(
    MCP工具定义(
        name="articles.content.replace",
        description="替换当前用户文章完整正文，必须提供 expected_last_edited_at。",
        input_schema=文章全文替换参数.model_json_schema(),
        permission="full",
        handler=articles_content_replace,
    )
)
注册工具(
    MCP工具定义(
        name="articles.content.patch",
        description="局部替换当前用户文章正文，必须提供 expected_last_edited_at、定位参数和 expected_hash。",
        input_schema=文章局部替换参数.model_json_schema(),
        permission="full",
        handler=articles_content_patch,
    )
)
