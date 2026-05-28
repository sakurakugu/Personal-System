"""设备认证服务测试。"""

from __future__ import annotations

import unittest

from starlette.requests import Request

from app.modules.auth.device_models import 设备会话范围, 设备会话类型
from app.modules.auth.device_service import (
    构建设备会话过期天数,
    构建设备令牌,
    构建设备令牌哈希,
)
from app.shared.auth.device_deps import 从请求获取Bearer令牌


class 设备认证服务测试(unittest.TestCase):
    """设备认证纯逻辑测试。"""

    @staticmethod
    def _build_request(headers: dict[str, str] | None = None) -> Request:
        raw_headers: list[tuple[bytes, bytes]] = []
        for key, value in (headers or {}).items():
            raw_headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))
        return Request({"type": "http", "headers": raw_headers})

    def test_设备令牌应带固定前缀且哈希长度稳定(self) -> None:
        token = 构建设备令牌()
        self.assertTrue(token.startswith("pst_dev_"))
        self.assertEqual(len(构建设备令牌哈希(token)), 64)

    def test_设备会话使用统一默认有效期(self) -> None:
        self.assertEqual(
            构建设备会话过期天数(
                设备会话类型.desktop,
                设备会话范围.full_client,
            ),
            30,
        )

    def test_bearer_token_可从请求头提取(self) -> None:
        request = self._build_request({"Authorization": "Bearer pst_dev_demo"})
        self.assertEqual(从请求获取Bearer令牌(request), "pst_dev_demo")

        request_without_bearer = self._build_request({"Authorization": "Basic demo"})
        self.assertIsNone(从请求获取Bearer令牌(request_without_bearer))

if __name__ == "__main__":
    unittest.main()
