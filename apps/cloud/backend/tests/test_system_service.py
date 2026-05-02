"""系统设置服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, Mock

from app.modules.system.service import read_system_settings_with_updated_at


class SystemServiceTest(unittest.IsolatedAsyncioTestCase):
    """系统设置服务测试。"""

    async def test_未配置时注册默认关闭(self) -> None:
        db = AsyncMock()
        result = Mock()
        scalars = Mock()
        scalars.all.return_value = []
        result.scalars.return_value = scalars
        db.execute.return_value = result

        payload, _ = await read_system_settings_with_updated_at(db)

        self.assertFalse(payload.register_enabled)
        self.assertFalse(payload.comments_enabled)
        self.assertTrue(payload.comments_hidden)


if __name__ == "__main__":
    unittest.main()
