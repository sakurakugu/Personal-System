"""V1 路由注册模块。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.modules.auth.api import router as auth_router
from app.modules.auth.dev_api import router as auth_dev_router
from app.modules.ai_chat.api import router as ai_chat_router
from app.integrations.holiday.api import router as calendar_router
from app.integrations.rss.api import router as rss_router
from app.modules.announcements.api import router as announcements_router
from app.modules.articles.api import router as articles_router
from app.modules.articles.taxonomy_api import router as cat_tag_router
from app.modules.bills.api import router as bills_router
from app.modules.materials.api import router as materials_router
from app.modules.auth.device_api import router as auth_device_router
from app.modules.auth.mcp_api import router as auth_mcp_router
from app.modules.feed.api import router as feed_router
from app.modules.file_transfer.api import router as file_transfer_router
from app.modules.files.api import router as files_router
from app.modules.friend_links.api import router as friend_links_router
from app.modules.media.api import router as media_router
from app.modules.memos.api import router as memos_router
from app.modules.moments.api import router as moments_router
from app.modules.stats.api import router as stats_router
from app.modules.system.banner_api import router as banner_router
from app.modules.system.api import router as admin_router
from app.modules.todos.api import router as todos_router
from app.modules.users.api import router as users_router
from app.modules.widget.api import router as widget_router

API_V1_PREFIX = "/api/v1"


def register_v1_routers(app: FastAPI, *, include_dev_auth: bool) -> None:
    """注册 V1 版本路由。"""
    routers = (
        health_router,
        auth_router,
        auth_device_router,
        auth_mcp_router,
        ai_chat_router,
        calendar_router,
        users_router,
        articles_router,
        cat_tag_router,
        materials_router,
        memos_router,
        todos_router,
        bills_router,
        file_transfer_router,
        files_router,
        media_router,
        stats_router,
        admin_router,
        widget_router,
        announcements_router,
        friend_links_router,
        feed_router,
        rss_router,
        moments_router,
        banner_router,
    )
    for router in routers:
        app.include_router(router, prefix=API_V1_PREFIX)

    if include_dev_auth:
        app.include_router(auth_dev_router, prefix=API_V1_PREFIX)
