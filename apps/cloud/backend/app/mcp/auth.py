"""MCP Bearer Token 校验。"""

from __future__ import annotations

from mcp.server.auth.provider import AccessToken

from app.modules.auth.device_models import 设备会话类型
from app.modules.auth.device_service import 按令牌获取设备会话
from app.shared.db.session import async_session_factory


class 设备令牌校验器:
    """将现有设备令牌适配为 MCP Bearer Token 校验器。"""

    async def verify_token(self, token: str) -> AccessToken | None:
        """校验设备令牌并返回 MCP 访问令牌信息。"""
        async with async_session_factory() as db:
            session = await 按令牌获取设备会话(db, token)
            if session.device_type != 设备会话类型.mcp:
                return None
            scopes = [session.scope.value]
            if session.scope.value == "mcp_full":
                scopes.append("mcp_readonly")
            await db.commit()
            return AccessToken(
                token=token,
                client_id=str(session.id),
                scopes=scopes,
                expires_at=int(session.expires_at.timestamp()),
                subject=str(session.user_id),
                claims={
                    "user_id": str(session.user_id),
                    "session_id": str(session.id),
                },
            )
