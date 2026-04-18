"""应用路由装配入口。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import register_api_routers


def register_application_routers(app: FastAPI, *, include_dev_auth: bool) -> None:
    """注册应用全部路由。"""
    register_api_routers(app, include_dev_auth=include_dev_auth)
