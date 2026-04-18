"""V1 路由注册模块。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.admin import router as admin_router
from app.api.v1.announcements import router as announcements_router
from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.banner import router as banner_router
from app.api.v1.bangumi import router as bangumi_router
from app.api.v1.bills import router as bills_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.categories_tags import router as cat_tag_router
from app.api.v1.collections import router as collections_router
from app.api.v1.comments import router as comments_router
from app.api.v1.feed import router as feed_router
from app.api.v1.files import router as files_router
from app.api.v1.friend_links import router as friend_links_router
from app.api.v1.moments import router as moments_router
from app.api.v1.rss import router as rss_router
from app.api.v1.stats import router as stats_router
from app.api.v1.todos import router as todos_router
from app.api.v1.users import router as users_router

API_V1_PREFIX = "/api/v1"


def register_v1_routers(app: FastAPI, *, include_dev_auth: bool) -> None:
    """注册 V1 版本路由。"""
    routers = (
        health_router,
        auth_router,
        calendar_router,
        users_router,
        articles_router,
        cat_tag_router,
        comments_router,
        collections_router,
        todos_router,
        bills_router,
        files_router,
        stats_router,
        admin_router,
        announcements_router,
        friend_links_router,
        feed_router,
        rss_router,
        bangumi_router,
        moments_router,
        banner_router,
    )
    for router in routers:
        app.include_router(router, prefix=API_V1_PREFIX)

    if include_dev_auth:
        from app.api.v1.auth_dev import router as auth_dev_router

        app.include_router(auth_dev_router, prefix=API_V1_PREFIX)
