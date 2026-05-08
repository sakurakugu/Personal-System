"""应用级路由注册模块。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.public_files import router as public_files_router
from app.api.v1.router import register_v1_routers

API_PREFIX = "/api"


def 注册API路由(app: FastAPI, *, include_dev_auth: bool) -> None:
    """注册应用的全部 API 路由。"""
    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(public_files_router)
    register_v1_routers(app, include_dev_auth=include_dev_auth)
