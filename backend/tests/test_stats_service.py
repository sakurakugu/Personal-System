"""统计服务测试。"""

from __future__ import annotations

import unittest
from datetime import date
from uuid import uuid4

from app.services.stats_service import (
    _构建待办完成历史响应,
    _构建最近访问趋势,
    _限制单个待办单日得分,
    hash_client_ip,
    iter_dates,
    待办完成聚合记录,
    近期访问聚合记录,
)


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

    def test_单个待办单日得分会被限制在零到一之间(self) -> None:
        self.assertEqual(_限制单个待办单日得分(-0.5), 0.0)
        self.assertEqual(_限制单个待办单日得分(0.25), 0.25)
        self.assertEqual(_限制单个待办单日得分(1.5), 1.0)

    def test_完成历史响应会按归一化得分汇总(self) -> None:
        todo_a = uuid4()
        todo_b = uuid4()
        response = _构建待办完成历史响应(
            [
                待办完成聚合记录(
                    occurred_on=date(2026, 4, 1),
                    todo_id=todo_a,
                    title="晨间拉伸",
                    completed_count=1,
                    normalized_score=0.25,
                ),
                待办完成聚合记录(
                    occurred_on=date(2026, 4, 1),
                    todo_id=todo_b,
                    title="喝水",
                    completed_count=5,
                    normalized_score=1.25,
                ),
            ],
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 2),
        )

        self.assertEqual(response.max_completed_count, 6)
        self.assertEqual(response.total_completed_count, 6)
        self.assertEqual(response.max_score, 1.25)
        self.assertEqual(response.total_score, 1.25)
        self.assertEqual(response.days[0].score, 1.25)
        self.assertEqual(response.days[0].items[0].normalized_score, 0.25)
        self.assertEqual(response.days[0].items[1].normalized_score, 1.0)
        self.assertEqual(response.days[1].completed_count, 0)
        self.assertEqual(response.days[1].score, 0.0)

    def test_最近访问趋势会按日期补零(self) -> None:
        trend = _构建最近访问趋势(
            [
                近期访问聚合记录(viewed_on=date(2026, 4, 2), count=3),
                近期访问聚合记录(viewed_on=date(2026, 4, 4), count=1),
            ],
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 4),
        )

        self.assertEqual(
            trend,
            [
                {"date": "2026-04-01", "count": 0},
                {"date": "2026-04-02", "count": 3},
                {"date": "2026-04-03", "count": 0},
                {"date": "2026-04-04", "count": 1},
            ],
        )


if __name__ == "__main__":
    unittest.main()
