"""桌面小工具服务测试。"""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.modules.auth.device_models import DeviceSessionScope
from app.modules.widget.service import validate_widget_access_scope


class WidgetServiceTest(unittest.TestCase):
    """桌面小工具纯逻辑测试。"""

    def test_widget_访问范围校验(self) -> None:
        validate_widget_access_scope(None)
        validate_widget_access_scope(
            type("Session", (), {"scope": DeviceSessionScope.widget_basic})()
        )
        validate_widget_access_scope(
            type("Session", (), {"scope": DeviceSessionScope.full_client})()
        )

        with self.assertRaises(HTTPException) as context:
            validate_widget_access_scope(
                type("Session", (), {"scope": "invalid_scope"})()
            )

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
