"""节假日日历服务。"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from chinese_calendar import get_holiday_detail, is_workday


最大向后查找天数 = 366 * 3


@lru_cache(maxsize=4096)
def 获取日期节假日信息(target_date: date) -> tuple[bool, bool, str | None, bool]:
    """返回指定日期的节假日、工作日、名称和是否命中官方数据。"""
    try:
        is_holiday, name = get_holiday_detail(target_date)
        return is_holiday, bool(is_workday(target_date)), name, True
    except NotImplementedError:
        weekday = target_date.weekday()
        return False, weekday < 5, None, False


def 是否节假日(target_date: date) -> bool:
    """判断指定日期是否为法定节假日。"""
    is_holiday, _, _, _ = 获取日期节假日信息(target_date)
    return is_holiday


def 是否工作日(target_date: date) -> bool:
    """判断指定日期是否为法定工作日。"""
    _, is_workday_value, _, _ = 获取日期节假日信息(target_date)
    return is_workday_value


@lru_cache(maxsize=64)
def 获取节假日日历年份(year: int) -> tuple[bool, tuple[date, ...], tuple[date, ...]]:
    """返回指定年份的节假日和调休工作日。"""
    supported = 获取日期节假日信息(date(year, 1, 1))[3]
    if not supported:
        return False, (), ()

    current = date(year, 1, 1)
    end = date(year, 12, 31)
    holidays: list[date] = []
    workdays: list[date] = []

    while current <= end:
        is_holiday, is_workday_value, _, _ = 获取日期节假日信息(current)
        if is_holiday:
            holidays.append(current)
        if is_workday_value and current.weekday() >= 5:
            workdays.append(current)
        current += timedelta(days=1)

    return True, tuple(holidays), tuple(workdays)
