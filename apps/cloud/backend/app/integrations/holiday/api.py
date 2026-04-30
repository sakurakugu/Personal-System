"""节假日日历路由。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path

from app.api.http_cache import build_conditional_json_response
from app.integrations import holiday as holiday_package
from app.integrations.holiday import service as holiday_service_module
from app.integrations.holiday.schemas import HolidayCalendarYearRead
from app.modules.users.models import User
from app.integrations.holiday.service import 获取节假日日历年份
from app.shared.auth.deps import get_current_user


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/years/{year}", response_model=HolidayCalendarYearRead)
async def get_holiday_calendar_year(
    year: int = Path(..., ge=2000, le=2100, description="年份"),
    if_none_match: Annotated[str | None, Header()] = None,
    if_modified_since: Annotated[str | None, Header()] = None,
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
    payload = HolidayCalendarYearRead(
        year=year,
        supported=supported,
        holiday_dates=list(holiday_dates),
        workday_dates=list(workday_dates),
    )
    module_path = FilePath(holiday_service_module.__file__ or holiday_package.__file__ or "")
    last_modified = datetime.fromtimestamp(module_path.stat().st_mtime, tz=timezone.utc)
    return build_conditional_json_response(
        payload,
        last_modified=last_modified,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
        cache_scope="public",
        max_age=86400,
    )
