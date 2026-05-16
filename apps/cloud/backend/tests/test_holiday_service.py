"""节假日日历服务测试。"""

from __future__ import annotations

import unittest
from datetime import date

from app.integrations.holiday.service import 获取日期节假日信息, 获取节假日日历年份, 是否工作日, 是否节假日


class 节假日服务测试(unittest.TestCase):
    """节假日日历服务测试。"""

    def test_国庆节会被识别为法定节假日(self) -> None:
        target = date(2026, 10, 1)
        self.assertTrue(是否节假日(target))
        self.assertFalse(是否工作日(target))

    def test_国庆调休周六会被识别为工作日(self) -> None:
        target = date(2026, 10, 10)
        self.assertFalse(是否节假日(target))
        self.assertTrue(是否工作日(target))

    def test_年份接口会返回节假日和调休日(self) -> None:
        supported, holiday_dates, workday_dates = 获取节假日日历年份(2026)

        self.assertTrue(supported)
        self.assertIn(date(2026, 10, 1), holiday_dates)
        self.assertIn(date(2026, 10, 10), workday_dates)

    def test_超出官方数据年份会回退到自然日语义(self) -> None:
        is_holiday, is_workday_value, _, supported = 获取日期节假日信息(date(2027, 1, 2))

        self.assertFalse(supported)
        self.assertFalse(is_holiday)
        self.assertFalse(is_workday_value)
