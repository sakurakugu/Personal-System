"""日历相关 Schema。"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class HolidayCalendarYearRead(BaseModel):
    """节假日日历年份响应。"""

    year: int
    supported: bool
    holiday_dates: list[date]
    workday_dates: list[date]
