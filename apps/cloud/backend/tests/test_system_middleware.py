"""系统监控中间件测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.bootstrap.middleware import register_middlewares
from app.shared.kernel.logger import setup_logging


class SystemMiddlewareTest(unittest.TestCase):
    """系统监控中间件测试。"""

    def test_系统状态接口不会写入监控事件(self) -> None:
        app = FastAPI()
        logger, _ = setup_logging(
            app_name="test-app",
            level="INFO",
            sqlalchemy_level="WARNING",
        )

        @app.get("/api/v1/admin/system")
        async def read_system() -> JSONResponse:
            return JSONResponse({"ok": True})

        with patch("app.bootstrap.middleware.record_request_event", AsyncMock()) as record_mock:
            register_middlewares(app, app_logger=logger)
            with TestClient(app) as client:
                response = client.get("/api/v1/admin/system")

        self.assertEqual(response.status_code, 200)
        record_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
