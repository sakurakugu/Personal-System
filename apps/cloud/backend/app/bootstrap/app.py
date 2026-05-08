"""FastAPI 应用构建入口。"""

from __future__ import annotations

from app.shared.kernel.config import settings
from app.shared.kernel.logger import setup_logging
from fastapi import FastAPI

from app.bootstrap.lifespan import lifespan
from app.bootstrap.middleware import 注册中间件
from app.bootstrap.router import 注册应用路由

# 首先配置日志（必须在导入其他模块之前）
app_logger, _ = setup_logging(
    app_name="personal-system",
    level="DEBUG" if settings.APP_DEBUG else "INFO",
    sqlalchemy_level="INFO" if settings.APP_DEBUG else "WARNING",
)


def 创建应用() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    enable_api_docs = settings.APP_DEBUG or settings.APP_ENV == "development"
    app = FastAPI(
        title="Sakurakuguの小窝 API",
        version="1.0.0",
        docs_url="/api/docs" if enable_api_docs else None,
        redoc_url="/api/redoc" if enable_api_docs else None,
        openapi_url="/api/openapi.json" if enable_api_docs else None,
        lifespan=lifespan,
    )
    注册中间件(app, app_logger=app_logger)
    注册应用路由(
        app,
        include_dev_auth=settings.APP_DEBUG or settings.APP_ENV == "development",
    )
    return app


app = 创建应用()

__all__ = ["app", "创建应用", "app_logger"]
