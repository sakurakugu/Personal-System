"""公告和友链软删除测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from app.modules.announcements.service import 应用公告删除状态, 恢复公告删除状态
from app.modules.friend_links.service import 应用友链删除状态, 恢复友链删除状态


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class 公告友链软删除测试(unittest.TestCase):
    """验证公告和友链删除状态辅助函数。"""

    def test_公告删除状态可恢复(self) -> None:
        announcement = SimpleNamespace(is_deleted=False, deleted_at=None)
        deleted_time = utc_dt(2026, 5, 29, 13, 0)

        应用公告删除状态(announcement, now=deleted_time)

        self.assertTrue(announcement.is_deleted)
        self.assertEqual(announcement.deleted_at, deleted_time)

        恢复公告删除状态(announcement)

        self.assertFalse(announcement.is_deleted)
        self.assertIsNone(announcement.deleted_at)

    def test_友链删除状态可恢复(self) -> None:
        friend_link = SimpleNamespace(is_deleted=False, deleted_at=None)
        deleted_time = utc_dt(2026, 5, 29, 13, 5)

        应用友链删除状态(friend_link, now=deleted_time)

        self.assertTrue(friend_link.is_deleted)
        self.assertEqual(friend_link.deleted_at, deleted_time)

        恢复友链删除状态(friend_link)

        self.assertFalse(friend_link.is_deleted)
        self.assertIsNone(friend_link.deleted_at)


if __name__ == "__main__":
    unittest.main()
