"""桌面小工具服务测试。"""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.modules.auth.device_models import 设备会话范围
from app.modules.widget.service import 校验小工具访问范围


class 小组件服务测试(unittest.TestCase):
    """桌面小工具纯逻辑测试。"""

    def test_widget_访问范围校验(self) -> None:
        校验小工具访问范围(None)
        校验小工具访问范围(
            type("Session", (), {"scope": 设备会话范围.full_client})()
        )

        with self.assertRaises(HTTPException) as context:
            校验小工具访问范围(
                type("Session", (), {"scope": "invalid_scope"})()
            )

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
