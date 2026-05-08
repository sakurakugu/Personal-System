"""应用启动配置测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.bootstrap.app import 创建应用


class AppBootstrapTest(unittest.TestCase):
    """应用启动配置测试。"""

    def test_开发环境开启接口文档(self) -> None:
        with patch("app.bootstrap.app.settings.APP_ENV", "development"), patch(
            "app.bootstrap.app.settings.APP_DEBUG", False
        ):
            app = 创建应用()

        self.assertEqual(app.docs_url, "/api/docs")
        self.assertEqual(app.redoc_url, "/api/redoc")
        self.assertEqual(app.openapi_url, "/api/openapi.json")

    def test_生产环境关闭接口文档(self) -> None:
        with patch("app.bootstrap.app.settings.APP_ENV", "production"), patch(
            "app.bootstrap.app.settings.APP_DEBUG", False
        ):
            app = 创建应用()

        self.assertIsNone(app.docs_url)
        self.assertIsNone(app.redoc_url)
        self.assertIsNone(app.openapi_url)


if __name__ == "__main__":
    unittest.main()
