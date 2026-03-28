"""后台管理服务测试。"""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.services.admin_service import validate_comments_min_role


class AdminServiceTest(unittest.TestCase):
    """后台管理服务纯逻辑测试。"""

    def test_评论最低角色校验(self) -> None:
        self.assertEqual(validate_comments_min_role("guest"), "guest")
        self.assertEqual(validate_comments_min_role("super_admin"), "super_admin")

        with self.assertRaises(HTTPException):
            validate_comments_min_role("owner")


if __name__ == "__main__":
    unittest.main()
