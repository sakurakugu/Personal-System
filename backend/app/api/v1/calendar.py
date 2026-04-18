"""节假日日历路由兼容入口。"""

from app.integrations.holiday.api import get_holiday_calendar_year, router

__all__ = ["get_holiday_calendar_year", "router"]
