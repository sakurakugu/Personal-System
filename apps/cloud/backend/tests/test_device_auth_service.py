"""设备认证服务测试。"""

from __future__ import annotations

import unittest

from fastapi import HTTPException
from starlette.requests import Request

from app.modules.auth.device_models import DeviceSessionScope, DeviceSessionType
from app.modules.auth.device_service import (
    build_device_session_expire_days,
    build_device_token,
    build_device_token_hash,
    validate_widget_token_issue_source,
    validate_device_scope,
)
from app.shared.auth.device_deps import get_bearer_token_from_request


class DeviceAuthServiceTest(unittest.TestCase):
    """设备认证纯逻辑测试。"""

    @staticmethod
    def _build_request(headers: dict[str, str] | None = None) -> Request:
        raw_headers: list[tuple[bytes, bytes]] = []
        for key, value in (headers or {}).items():
            raw_headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))
        return Request({"type": "http", "headers": raw_headers})

    def test_设备令牌应带固定前缀且哈希长度稳定(self) -> None:
        token = build_device_token()
        self.assertTrue(token.startswith("pst_dev_"))
        self.assertEqual(len(build_device_token_hash(token)), 64)

    def test_widget_scope_仅允许_widget_设备(self) -> None:
        validate_device_scope(DeviceSessionType.widget, DeviceSessionScope.widget_basic)

        with self.assertRaises(HTTPException) as context:
            validate_device_scope(DeviceSessionType.desktop, DeviceSessionScope.widget_basic)

        self.assertEqual(context.exception.status_code, 400)

    def test_不同设备类型会映射不同默认有效期(self) -> None:
        self.assertEqual(
            build_device_session_expire_days(
                DeviceSessionType.desktop,
                DeviceSessionScope.full_client,
            ),
            30,
        )
        self.assertEqual(
            build_device_session_expire_days(
                DeviceSessionType.widget,
                DeviceSessionScope.widget_basic,
            ),
            90,
        )

    def test_bearer_token_可从请求头提取(self) -> None:
        request = self._build_request({"Authorization": "Bearer pst_dev_demo"})
        self.assertEqual(get_bearer_token_from_request(request), "pst_dev_demo")

        request_without_bearer = self._build_request({"Authorization": "Basic demo"})
        self.assertIsNone(get_bearer_token_from_request(request_without_bearer))

    def test_仅_full_client_来源可签发_widget_凭证(self) -> None:
        validate_widget_token_issue_source(None)
        validate_widget_token_issue_source(
            type("Session", (), {"scope": DeviceSessionScope.full_client})()
        )

        with self.assertRaises(HTTPException) as context:
            validate_widget_token_issue_source(
                type("Session", (), {"scope": DeviceSessionScope.widget_basic})()
            )

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
