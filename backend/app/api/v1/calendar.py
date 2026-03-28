"""节假日日历路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import HolidayCalendarYearRead
from app.services.holiday_service import 获取节假日日历年份


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/years/{year}", response_model=HolidayCalendarYearRead)
async def get_holiday_calendar_year(
    year: int = Path(..., ge=2000, le=2100, description="年份"),
    _user: User = Depends(get_current_user),
):
    """
    获取指定年份的法定节假日与调休工作日。

    Args:
        year: 年份
        _user: 当前登录用户

    Returns:
        HolidayCalendarYearRead: 节假日日历数据
    """
    supported, holiday_dates, workday_dates = 获取节假日日历年份(year)
    return HolidayCalendarYearRead(
        year=year,
        supported=supported,
        holiday_dates=list(holiday_dates),
        workday_dates=list(workday_dates),
    )
