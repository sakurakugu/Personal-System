"""统计服务测试。"""

from __future__ import annotations

import unittest
from datetime import date

from app.services.stats_service import hash_client_ip, iter_dates


class StatsServiceTest(unittest.TestCase):
    """统计服务纯逻辑测试。"""

    def test_会生成闭区间日期列表(self) -> None:
        days = iter_dates(date(2026, 3, 28), date(2026, 3, 30))
        self.assertEqual(days, [date(2026, 3, 28), date(2026, 3, 29), date(2026, 3, 30)])

    def test_ip_hash_稳定且长度固定(self) -> None:
        first = hash_client_ip("127.0.0.1")
        second = hash_client_ip("127.0.0.1")
        third = hash_client_ip("192.168.0.1")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertNotEqual(first, third)


if __name__ == "__main__":
    unittest.main()
