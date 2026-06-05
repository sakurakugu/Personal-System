"""MCP 工具运行上下文。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import 用户设备会话
from app.modules.users.models import 用户


@dataclass(slots=True)
class MCP调用上下文:
    """单次 MCP 工具调用上下文。"""

    user: 用户
    device_session: 用户设备会话 | None
    source: str
    db: AsyncSession | None = None
