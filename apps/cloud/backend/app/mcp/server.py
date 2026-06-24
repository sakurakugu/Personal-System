"""云端 MCP Server。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from mcp.server.auth.middleware.auth_context import auth_context_var, get_access_token
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp import types
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from app.mcp.auth import 设备令牌校验器
from app.mcp.registry import 列出工具
from app.mcp.runtime import 从声明构建MCP上下文, 执行MCP工具
from app.mcp import tools as _tools  # noqa: F401

MCP令牌校验器 = 设备令牌校验器()
mcp_server: Server[Any, Any] = Server(
    "personal-system-cloud",
    instructions="通过受限工具读取和操作个人系统云端能力。",
)


@mcp_server.list_tools()
async def _列出MCP工具() -> list[types.Tool]:
    """列出 MCP 工具。"""
    return [
        types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.input_schema,
        )
        for tool in 列出工具()
    ]


@mcp_server.call_tool()
async def _调用MCP工具(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """调用 MCP 工具。"""
    access_token = get_access_token()
    if access_token is None or access_token.claims is None:
        raise ValueError("未提供 MCP 访问令牌")
    runtime_context = await 从声明构建MCP上下文(access_token.claims, source="mcp_http")
    return await 执行MCP工具(name, arguments, runtime_context)


mcp_session_manager = StreamableHTTPSessionManager(
    mcp_server,
    json_response=True,
    stateless=True,
)


class MCP鉴权ASGI应用:
    """给 Streamable HTTP MCP 请求增加 Bearer 设备令牌鉴权。"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """处理 MCP HTTP 请求。"""
        if scope["type"] != "http":
            await mcp_session_manager.handle_request(scope, receive, send)
            return

        token = self._提取令牌(scope)
        access_token = await MCP令牌校验器.verify_token(token) if token else None
        if access_token is None:
            await self._发送鉴权错误(send, 401, "invalid_token", "Authentication required")
            return
        if "mcp_readonly" not in access_token.scopes:
            await self._发送鉴权错误(send, 403, "insufficient_scope", "Required scope: mcp_readonly")
            return

        context_token = auth_context_var.set(AuthenticatedUser(access_token))
        try:
            await mcp_session_manager.handle_request(scope, receive, send)
        finally:
            auth_context_var.reset(context_token)

    @staticmethod
    def _提取令牌(scope: Scope) -> str | None:
        """从 ASGI scope 提取 Bearer Token。"""
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        authorization = headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            return None
        token = authorization[7:].strip()
        return token or None

    @staticmethod
    async def _发送鉴权错误(send: Send, status_code: int, error: str, description: str) -> None:
        """发送 MCP 鉴权错误响应。"""
        body = f'{{"error":"{error}","error_description":"{description}"}}'.encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"www-authenticate", f'Bearer error="{error}"'.encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


mcp_session_manager_context: Any | None = None


async def 启动MCP会话管理器() -> None:
    """启动 MCP Streamable HTTP 会话管理器。"""
    global mcp_session_manager_context
    if mcp_session_manager_context is not None:
        return
    mcp_session_manager_context = mcp_session_manager.run()
    await mcp_session_manager_context.__aenter__()


async def 停止MCP会话管理器() -> None:
    """停止 MCP Streamable HTTP 会话管理器。"""
    global mcp_session_manager_context
    if mcp_session_manager_context is None:
        return
    context = mcp_session_manager_context
    mcp_session_manager_context = None
    await context.__aexit__(None, None, None)


def 注册MCP服务(app: FastAPI) -> None:
    """将 MCP 服务挂载到 FastAPI 应用。"""
    mcp_app = MCP鉴权ASGI应用()
    app.router.routes.append(Route("/mcp", endpoint=mcp_app, methods=["GET", "POST", "DELETE"]))
