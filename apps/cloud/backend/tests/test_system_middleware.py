"""系统监控中间件测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.bootstrap.middleware import 注册中间件
from app.shared.kernel.logger import setup_logging


def _构建测试应用() -> FastAPI:
    """构建带监控中间件的最小应用，同时提供被排除和普通两类真实路由。"""
    app = FastAPI()
    logger, _ = setup_logging(
        app_name="test-app",
        level="INFO",
        sqlalchemy_level="WARNING",
    )

    @app.get("/api/v1/system/status")
    async def read_system() -> JSONResponse:
        """与生产一致的系统状态路由，属于监控排除路径。"""
        return JSONResponse({"ok": True})

    @app.get("/api/v1/todos")
    async def read_todos() -> JSONResponse:
        """普通业务路由，应该被监控统计。"""
        return JSONResponse({"ok": True})

    注册中间件(app, app_logger=logger)
    return app


class 系统中间件测试(unittest.TestCase):
    """系统监控中间件测试。"""

    def test_系统状态接口不会写入监控事件(self) -> None:
        """系统状态接口属于监控排除路径，不产生监控事件。"""
        app = _构建测试应用()

        with patch("app.bootstrap.middleware.记录请求事件", AsyncMock()) as record_mock:
            with TestClient(app) as client:
                response = client.get("/api/v1/system/status")

        self.assertEqual(response.status_code, 200)
        record_mock.assert_not_awaited()

    def test_普通接口会写入监控事件(self) -> None:
        """普通接口照常写入监控事件，用于证明排除逻辑只对白名单路径生效。"""
        app = _构建测试应用()

        with patch("app.bootstrap.middleware.记录请求事件", AsyncMock()) as record_mock:
            with TestClient(app) as client:
                response = client.get("/api/v1/todos")

        self.assertEqual(response.status_code, 200)
        record_mock.assert_awaited_once()
        self.assertEqual(record_mock.await_args.kwargs["path"], "/api/v1/todos")
        self.assertEqual(record_mock.await_args.kwargs["status_code"], 200)


if __name__ == "__main__":
    unittest.main()
