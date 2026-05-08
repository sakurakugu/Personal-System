"""应用路由装配入口。"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import 注册API路由


def 注册应用路由(app: FastAPI, *, include_dev_auth: bool) -> None:
    """注册应用全部路由。"""
    注册API路由(app, include_dev_auth=include_dev_auth)
