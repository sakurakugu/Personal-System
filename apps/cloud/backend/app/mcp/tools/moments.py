"""动态相关 MCP 工具。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.mcp.context import MCP调用上下文
from app.mcp.registry import MCP工具定义, 注册工具
from app.modules.feed.service import 清除Feed首页缓存, 同步动态Feed条目
from app.modules.moments.models import 动态
from app.modules.moments.permissions import 确保动态写入权限
from app.modules.moments.presentation import 构建动态读取响应
from app.modules.moments.schemas import 动态信息
from app.modules.moments.service import (
    删除动态,
    动态查询,
    获取已删动态或404,
    获取草稿,
    获取动态或404,
    恢复动态,
    刷新动态最后编辑时间,
)


class 动态列表参数(BaseModel):
    """我的动态列表查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    is_deleted: bool = Field(default=False, description="是否查询回收站")
    include_drafts: bool = Field(default=True, description="是否包含未发布草稿")


class 动态ID参数(BaseModel):
    """单条动态 ID 参数。"""

    moment_id: str = Field(description="动态 ID")
    is_deleted: bool = Field(default=False, description="是否读取回收站动态")


class 动态创建参数(BaseModel):
    """创建动态参数。"""

    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)
    is_published: bool = Field(default=False, description="是否直接发布，默认创建未发布动态")


class 动态更新参数(BaseModel):
    """普通动态更新参数。"""

    moment_id: str = Field(description="动态 ID")
    expected_last_edited_at: str = Field(description="调用方读取到的 last_edited_at")
    title: str | None = Field(default=None, max_length=100)
    content: str | None = Field(default=None, max_length=1000)
    is_published: bool | None = Field(default=None, description="发布状态，true 发布，false 转为未发布")


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


def 校验动态最后编辑时间(actual: datetime, expected: str) -> None:
    """校验调用方读取的动态编辑时间仍然有效。"""
    if _转UTC(actual) != _解析时间戳(expected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "动态已被更新，请重新读取后再修改",
                "current_last_edited_at": actual.isoformat(),
            },
        )


def _动态读取(moment: 动态) -> dict[str, Any]:
    """将动态 ORM 对象转为稳定 JSON。"""
    return 动态信息.model_validate(构建动态读取响应(moment)).model_dump(mode="json")


def _动态快照(moment: 动态) -> dict[str, Any]:
    """构建动态撤销快照。"""
    return {
        "id": str(moment.id),
        "title": moment.title,
        "content": moment.content,
        "is_published": moment.is_published,
        "view_count": moment.view_count,
        "like_count": moment.like_count,
        "user_id": str(moment.user_id),
        "is_deleted": moment.is_deleted,
        "deleted_at": moment.deleted_at.isoformat() if moment.deleted_at else None,
        "published_at": moment.published_at.isoformat() if moment.published_at else None,
        "created_at": moment.created_at.isoformat(),
        "last_edited_at": moment.last_edited_at.isoformat(),
        "updated_at": moment.updated_at.isoformat(),
        "image_ids": [str(image.id) for image in sorted(moment.images, key=lambda item: (item.sort_order, item.created_at))],
    }


async def 获取我的动态或404(context: MCP调用上下文, moment_id: str) -> 动态:
    """获取当前用户未删除动态。"""
    db = _获取MCP会话(context)
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, context.user)
    return moment


async def _重新加载动态(context: MCP调用上下文, moment_id: str, *, is_deleted: bool = False) -> 动态:
    """重新加载动态并带上图片关系。"""
    db = _获取MCP会话(context)
    query = 动态查询().where(
        动态.id == moment_id,
        动态.user_id == context.user.id,
        动态.is_deleted.is_(is_deleted),
    )
    result = await db.execute(query)
    moment = result.scalar_one_or_none()
    if moment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")
    return moment


async def _列出我的全部动态(
    context: MCP调用上下文,
    *,
    page: int,
    page_size: int,
    is_deleted: bool,
    include_drafts: bool,
) -> dict[str, Any]:
    """查询当前用户动态，未删除列表默认包含草稿和已发布动态。"""
    db = _获取MCP会话(context)
    query = 动态查询().where(
        动态.user_id == context.user.id,
        动态.is_deleted.is_(is_deleted),
    )
    if is_deleted:
        query = query.order_by(动态.deleted_at.desc(), 动态.created_at.desc())
    else:
        if not include_drafts:
            query = query.where(动态.is_published.is_(True))
        query = query.order_by(func.coalesce(动态.published_at, 动态.created_at).desc())

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().unique().all()
    return {
        "items": [_动态读取(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total else 0,
    }


async def _确保可设为草稿(db, moment: 动态, user) -> None:
    """确保当前用户没有另一条未发布未删除动态。"""
    draft = await 获取草稿(db, user)
    if draft is not None and draft.id != moment.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前用户已经有未发布动态草稿")


async def 应用动态MCP更新(db, moment: 动态, body: 动态更新参数, *, user=None) -> 动态:
    """应用 MCP 普通动态更新。"""
    changed = False
    publish_state_changed = False

    if body.title is not None and moment.title != body.title:
        moment.title = body.title
        changed = True
    if body.content is not None and moment.content != body.content:
        moment.content = body.content
        changed = True
    if body.is_published is not None and moment.is_published != body.is_published:
        if not body.is_published:
            if user is None:
                raise RuntimeError("动态转草稿缺少当前用户")
            await _确保可设为草稿(db, moment, user)
        now = datetime.now(timezone.utc)
        moment.is_published = body.is_published
        moment.published_at = now if body.is_published else None
        刷新动态最后编辑时间(moment, now=now)
        changed = True
        publish_state_changed = True

    if changed and not publish_state_changed:
        刷新动态最后编辑时间(moment)

    if changed:
        await 同步动态Feed条目(db, moment)
        await db.flush()
        await 清除Feed首页缓存()

    return moment


async def moments_list(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """查询当前用户动态列表。"""
    body = 动态列表参数.model_validate(args)
    return await _列出我的全部动态(
        context,
        page=body.page,
        page_size=body.page_size,
        is_deleted=body.is_deleted,
        include_drafts=body.include_drafts,
    )


async def moments_get(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """读取单条动态详情。"""
    body = 动态ID参数.model_validate(args)
    moment = await _重新加载动态(context, body.moment_id, is_deleted=body.is_deleted)
    return _动态读取(moment)


async def moments_create(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """创建动态。"""
    body = 动态创建参数.model_validate(args)
    db = _获取MCP会话(context)
    if not body.is_published and await 获取草稿(db, context.user) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前用户已经有未发布动态草稿")

    now = datetime.now(timezone.utc)
    moment = 动态(
        title=body.title,
        content=body.content,
        is_published=body.is_published,
        user_id=context.user.id,
        published_at=now if body.is_published else None,
        last_edited_at=now,
    )
    db.add(moment)
    await db.flush()
    if moment.is_published:
        await 同步动态Feed条目(db, moment)
        await db.flush()
        await 清除Feed首页缓存()

    reloaded = await _重新加载动态(context, str(moment.id))
    after = _动态快照(reloaded)
    return {
        "summary": f"已创建动态：{reloaded.title or '无标题'}",
        "target": {"type": "moment", "id": str(reloaded.id)},
        "undoable": True,
        "undo_tool_name": "moments.delete",
        "after": after,
        "data": _动态读取(reloaded),
    }


async def moments_update(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """更新动态普通字段。"""
    body = 动态更新参数.model_validate(args)
    db = _获取MCP会话(context)
    moment = await 获取我的动态或404(context, body.moment_id)
    校验动态最后编辑时间(moment.last_edited_at, body.expected_last_edited_at)
    before = _动态快照(await _重新加载动态(context, body.moment_id))
    if body.is_published is False:
        await _确保可设为草稿(db, moment, context.user)
    moment = await 应用动态MCP更新(db, moment, body, user=context.user)
    reloaded = await _重新加载动态(context, str(moment.id))
    after = _动态快照(reloaded)
    return {
        "summary": f"已更新动态：{reloaded.title or '无标题'}",
        "target": {"type": "moment", "id": str(reloaded.id)},
        "undoable": True,
        "undo_tool_name": "moments.update",
        "before": before,
        "after": after,
        "data": _动态读取(reloaded),
    }


async def moments_delete(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """软删除动态。"""
    body = 动态ID参数.model_validate(args)
    db = _获取MCP会话(context)
    moment = await 获取我的动态或404(context, body.moment_id)
    before = _动态快照(await _重新加载动态(context, body.moment_id))
    title = moment.title or "无标题"
    await 删除动态(db, body.moment_id, context.user, permanent=False)
    deleted = await _重新加载动态(context, body.moment_id, is_deleted=True)
    return {
        "summary": f"已移入回收站：{title}",
        "target": {"type": "moment", "id": str(deleted.id)},
        "undoable": True,
        "undo_tool_name": "moments.restore",
        "before": before,
        "after": _动态快照(deleted),
    }


async def moments_restore(args: dict[str, Any], context: MCP调用上下文) -> dict[str, Any]:
    """从回收站恢复动态。"""
    body = 动态ID参数.model_validate(args)
    before_moment = await 获取已删动态或404(_获取MCP会话(context), body.moment_id)
    确保动态写入权限(before_moment, context.user)
    if not before_moment.is_published:
        await _确保可设为草稿(_获取MCP会话(context), before_moment, context.user)
    before = _动态快照(await _重新加载动态(context, body.moment_id, is_deleted=True))
    restored = await 恢复动态(_获取MCP会话(context), body.moment_id, context.user)
    reloaded = await _重新加载动态(context, str(restored.id))
    after = _动态快照(reloaded)
    return {
        "summary": f"已恢复动态：{reloaded.title or '无标题'}",
        "target": {"type": "moment", "id": str(reloaded.id)},
        "undoable": True,
        "undo_tool_name": "moments.delete",
        "before": before,
        "after": after,
        "data": _动态读取(reloaded),
    }


注册工具(
    MCP工具定义(
        name="moments.list",
        description="查询当前用户动态列表，默认包含未删除的草稿和已发布动态。",
        input_schema=动态列表参数.model_json_schema(),
        permission="readonly",
        handler=moments_list,
    )
)
注册工具(
    MCP工具定义(
        name="moments.get",
        description="读取当前用户的一条动态详情。",
        input_schema=动态ID参数.model_json_schema(),
        permission="readonly",
        handler=moments_get,
    )
)
注册工具(
    MCP工具定义(
        name="moments.create",
        description="为当前用户创建动态，未指定 is_published 时创建未发布动态。",
        input_schema=动态创建参数.model_json_schema(),
        permission="full",
        handler=moments_create,
    )
)
注册工具(
    MCP工具定义(
        name="moments.update",
        description="更新当前用户动态的标题、正文或发布状态，必须提供 expected_last_edited_at。",
        input_schema=动态更新参数.model_json_schema(),
        permission="full",
        handler=moments_update,
    )
)
注册工具(
    MCP工具定义(
        name="moments.delete",
        description="将当前用户的一条动态移入回收站，不执行永久删除。",
        input_schema=动态ID参数.model_json_schema(),
        permission="full",
        handler=moments_delete,
    )
)
注册工具(
    MCP工具定义(
        name="moments.restore",
        description="从回收站恢复当前用户的一条动态。",
        input_schema=动态ID参数.model_json_schema(),
        permission="full",
        handler=moments_restore,
    )
)
