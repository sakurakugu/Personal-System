"""友链服务兼容入口。"""

from app.modules.friend_links.service import (
    approve_friend_link,
    check_backlink,
    contains_backlink,
    create_friend_link,
    delete_friend_link,
    exchange_friend_link,
    get_friend_link_or_404,
    list_friend_link_categories,
    list_friend_links,
    list_public_friend_links,
    normalize_domain,
    parse_friend_link_status,
    reject_friend_link,
    update_friend_link,
)

__all__ = [
    "approve_friend_link",
    "check_backlink",
    "contains_backlink",
    "create_friend_link",
    "delete_friend_link",
    "exchange_friend_link",
    "get_friend_link_or_404",
    "list_friend_link_categories",
    "list_friend_links",
    "list_public_friend_links",
    "normalize_domain",
    "parse_friend_link_status",
    "reject_friend_link",
    "update_friend_link",
]
