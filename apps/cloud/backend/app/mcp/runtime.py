"""MCP 工具执行运行时。"""

from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select

from app.mcp.context import MCP调用上下文
from app.mcp.operation_log import 记录MCP操作失败, 记录MCP操作成功
from app.mcp.registry import 获取工具
from app.modules.auth.device_models import 设备会话范围, 用户设备会话
from app.modules.users.models import 用户
from app.shared.db.session import async_session_factory
from app.shared.kernel.logger import get_logger

logger = get_logger(__name__)


def _是否允许调用(scope: 设备会话范围 | None, permission: str) -> bool:
    """判断设备权限是否允许调用工具。"""
    if permission == "readonly":
        return scope in (设备会话范围.mcp_readonly, 设备会话范围.mcp_full) or scope is None
    return scope == 设备会话范围.mcp_full or scope is None


async def 从声明构建MCP上下文(claims: dict[str, Any], *, source: str) -> MCP调用上下文:
    """从 MCP 认证声明构造工具上下文。"""
    user_id = claims.get("user_id")
    session_id = claims.get("session_id")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MCP 令牌缺少用户信息")

    async with async_session_factory() as db:
        result = await db.execute(select(用户).where(用户.id == UUID(user_id), 用户.is_active.is_(True)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

        device_session: 用户设备会话 | None = None
        if isinstance(session_id, str):
            device_session = await db.get(用户设备会话, UUID(session_id))
        return MCP调用上下文(user=user, device_session=device_session, source=source)


async def 执行MCP工具(
    name: str,
    arguments: dict[str, Any],
    context: MCP调用上下文,
) -> dict[str, Any]:
    """执行 MCP 工具并处理权限。"""
    tool = 获取工具(name)
    scope = context.device_session.scope if context.device_session is not None else None
    if not _是否允许调用(scope, tool.permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前 MCP 权限不足")

    logger.info(
        "MCP 工具调用开始 source=%s tool=%s user_id=%s session_id=%s",
        context.source,
        name,
        context.user.id,
        context.device_session.id if context.device_session else None,
    )
    started_at = perf_counter()
    async with async_session_factory() as db:
        context.db = db
        try:
            result = await tool.handler(arguments, context)
            duration_ms = int((perf_counter() - started_at) * 1000)
            operation = None
            already_logged = bool(result.pop("_operation_logged", False))
            if tool.permission == "full" and not already_logged:
                operation = await 记录MCP操作成功(
                    db,
                    user=context.user,
                    device_session=context.device_session,
                    tool_name=name,
                    args_json=arguments,
                    result_json=result,
                    duration_ms=duration_ms,
                )
            await db.commit()
            logger.info(
                "MCP 工具调用完成 source=%s tool=%s user_id=%s session_id=%s duration_ms=%s success=true operation_id=%s",
                context.source,
                name,
                context.user.id,
                context.device_session.id if context.device_session else None,
                duration_ms,
                operation.id if operation else None,
            )
            return result
        except Exception as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)
            await db.rollback()
            if tool.permission == "full":
                async with async_session_factory() as log_db:
                    await 记录MCP操作失败(
                        log_db,
                        user=context.user,
                        device_session=context.device_session,
                        tool_name=name,
                        args_json=arguments,
                        error_message=str(exc),
                        duration_ms=duration_ms,
                    )
                    await log_db.commit()
            logger.exception(
                "MCP 工具调用失败 source=%s tool=%s user_id=%s session_id=%s duration_ms=%s success=false",
                context.source,
                name,
                context.user.id,
                context.device_session.id if context.device_session else None,
                duration_ms,
            )
            raise
        finally:
            context.db = None

