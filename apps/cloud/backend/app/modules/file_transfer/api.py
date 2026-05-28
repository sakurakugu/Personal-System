"""文件中转站 WebSocket 信令路由。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from starlette.websockets import WebSocketState

from app.modules.auth.sessions import get_session
from app.modules.users.models import 用户
from app.shared.db.session import async_session_factory
from app.shared.kernel.logger import get_logger
from app.shared.kernel.config import settings

router = APIRouter(prefix="/file-transfer", tags=["file-transfer"])
logger = get_logger(__name__)


房间ID最小长度 = 4
房间ID最大长度 = 32
设备名称最大长度 = 48
消息类型最大长度 = 48
最大信令载荷字节数 = 64 * 1024


class 加入房间消息(BaseModel):
    """客户端加入文件中转房间的消息。"""

    type: str = Field(pattern="^join$")
    roomId: str = Field(min_length=房间ID最小长度, max_length=房间ID最大长度)
    deviceName: str = Field(min_length=1, max_length=设备名称最大长度)


class 信令消息(BaseModel):
    """客户端转发给房间内指定设备的 WebRTC 信令。"""

    type: str = Field(pattern="^signal$")
    to: str = Field(min_length=1, max_length=64)
    signal: dict[str, Any]


@dataclass
class 中转连接:
    """房间中的一个 WebSocket 连接。"""

    peer_id: str
    room_id: str
    device_name: str
    websocket: WebSocket

    def 公开信息(self) -> dict[str, str]:
        """返回可广播给其他客户端的设备信息。"""
        return {
            "id": self.peer_id,
            "deviceName": self.device_name,
        }


@dataclass
class 中转房间:
    """内存中的文件中转房间。"""

    peers: dict[str, 中转连接] = field(default_factory=dict)


class 文件中转信令中心:
    """维护文件中转房间，并只负责信令转发。"""

    def __init__(self) -> None:
        self._rooms: dict[str, 中转房间] = {}

    async def 加入房间(self, websocket: WebSocket, message: 加入房间消息) -> 中转连接:
        """将 WebSocket 加入指定房间。"""
        peer = 中转连接(
            peer_id=uuid4().hex,
            room_id=message.roomId,
            device_name=message.deviceName.strip(),
            websocket=websocket,
        )
        room = self._rooms.setdefault(message.roomId, 中转房间())
        await self._发送(
            peer,
            {
                "type": "joined",
                "peerId": peer.peer_id,
                "roomId": peer.room_id,
                "peers": [item.公开信息() for item in room.peers.values()],
            },
        )
        room.peers[peer.peer_id] = peer
        await self._广播给房间其他设备(
            peer,
            {
                "type": "peer-joined",
                "peer": peer.公开信息(),
            },
        )
        logger.info(
            "文件中转设备加入房间 room_id=%s peer_id=%s peers=%s",
            peer.room_id,
            peer.peer_id,
            len(room.peers),
        )
        return peer

    async def 离开房间(self, peer: 中转连接 | None) -> None:
        """从房间中移除连接并通知其他设备。"""
        if peer is None:
            return
        room = self._rooms.get(peer.room_id)
        if room is None or peer.peer_id not in room.peers:
            return
        del room.peers[peer.peer_id]
        if not room.peers:
            del self._rooms[peer.room_id]
            logger.info("文件中转房间已清空 room_id=%s", peer.room_id)
            return
        await self._广播给房间其他设备(
            peer,
            {
                "type": "peer-left",
                "peerId": peer.peer_id,
            },
        )
        logger.info(
            "文件中转设备离开房间 room_id=%s peer_id=%s peers=%s",
            peer.room_id,
            peer.peer_id,
            len(room.peers),
        )

    async def 转发信令(self, sender: 中转连接, message: 信令消息) -> None:
        """向同房间目标设备转发 WebRTC 信令。"""
        room = self._rooms.get(sender.room_id)
        recipient = room.peers.get(message.to) if room else None
        if recipient is None:
            await self._发送(
                sender,
                {
                    "type": "signal-error",
                    "message": "目标设备已离线",
                    "to": message.to,
                },
            )
            return
        await self._发送(
            recipient,
            {
                "type": "signal",
                "from": sender.peer_id,
                "signal": message.signal,
            },
        )

    async def _广播给房间其他设备(self, sender: 中转连接, payload: dict[str, Any]) -> None:
        room = self._rooms.get(sender.room_id)
        if room is None:
            return
        for peer_id, peer in list(room.peers.items()):
            if peer_id != sender.peer_id:
                await self._发送(peer, payload)

    async def _发送(self, peer: 中转连接, payload: dict[str, Any]) -> None:
        if peer.websocket.client_state != WebSocketState.CONNECTED:
            return
        await peer.websocket.send_json(payload)


信令中心 = 文件中转信令中心()


def _解析JSON消息(raw_message: str) -> dict[str, Any]:
    if len(raw_message.encode("utf-8")) > 最大信令载荷字节数:
        raise ValueError("信令消息过大")
    payload = json.loads(raw_message)
    if not isinstance(payload, dict):
        raise ValueError("信令消息必须是对象")
    message_type = payload.get("type")
    if not isinstance(message_type, str) or len(message_type) > 消息类型最大长度:
        raise ValueError("信令消息类型无效")
    return payload


async def _发送错误(websocket: WebSocket, message: str) -> None:
    if websocket.client_state == WebSocketState.CONNECTED:
        await websocket.send_json({"type": "error", "message": message})


async def _校验WebSocket登录态(websocket: WebSocket) -> 用户 | None:
    """校验 WebSocket 握手里的登录会话。"""
    session_id = websocket.cookies.get(settings.AUTH_SESSION_COOKIE_NAME)
    session = await get_session(session_id)
    if session is None:
        return None

    try:
        user_id = UUID(session.user_id)
    except ValueError:
        return None

    async with async_session_factory() as db:
        result = await db.execute(select(用户).where(用户.id == user_id, 用户.is_active.is_(True)))
        return result.scalar_one_or_none()


@router.websocket("/ws")
async def 文件中转WebSocket(websocket: WebSocket) -> None:
    """处理文件中转站 WebSocket 信令连接。"""
    await websocket.accept()
    user = await _校验WebSocket登录态(websocket)
    if user is None:
        await _发送错误(websocket, "请先登录后再使用文件中转站")
        await websocket.close(code=1008, reason="unauthorized")
        return
    logger.info("文件中转 WebSocket 登录校验通过 user_id=%s", user.id)
    peer: 中转连接 | None = None
    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                payload = _解析JSON消息(raw_message)
                message_type = payload["type"]
                if message_type == "join":
                    if peer is not None:
                        await _发送错误(websocket, "当前连接已经加入房间")
                        continue
                    join_message = 加入房间消息.model_validate(payload)
                    peer = await 信令中心.加入房间(websocket, join_message)
                    continue
                if peer is None:
                    await _发送错误(websocket, "请先加入房间")
                    continue
                if message_type == "signal":
                    signal_message = 信令消息.model_validate(payload)
                    await 信令中心.转发信令(peer, signal_message)
                    continue
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                await _发送错误(websocket, "未知的信令消息类型")
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                logger.warning("文件中转信令消息无效: %s", exc)
                await _发送错误(websocket, "信令消息格式无效")
    except WebSocketDisconnect:
        pass
    finally:
        await 信令中心.离开房间(peer)
