"""FastAPI 应用构建入口。"""

from __future__ import annotations

from app.shared.kernel.config import settings
from app.shared.kernel.logger import setup_logging
from fastapi import FastAPI

from app.bootstrap.lifespan import lifespan
from app.bootstrap.middleware import register_middlewares
from app.bootstrap.router import register_application_routers

# 首先配置日志（必须在导入其他模块之前）
app_logger, _ = setup_logging(
    app_name="web-system",
    level="DEBUG" if settings.APP_DEBUG else "INFO",
    sqlalchemy_level="INFO" if settings.APP_DEBUG else "WARNING",
)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    app = FastAPI(
        title="Sakurakuguの小窝 API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    register_middlewares(app, app_logger=app_logger)
    register_application_routers(
        app,
        include_dev_auth=settings.APP_DEBUG or settings.APP_ENV == "development",
    )
    return app


app = create_app()

__all__ = ["app", "create_app", "app_logger"]
