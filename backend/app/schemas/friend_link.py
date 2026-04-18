"""友链 Schema 兼容入口。"""

from app.modules.friend_links.schemas import (
    FriendLinkCreate,
    FriendLinkExchangeRequest,
    FriendLinkPublicRead,
    FriendLinkRead,
    FriendLinkUpdate,
)

__all__ = [
    "FriendLinkCreate",
    "FriendLinkExchangeRequest",
    "FriendLinkPublicRead",
    "FriendLinkRead",
    "FriendLinkUpdate",
]
