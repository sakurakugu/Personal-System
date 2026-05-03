"""桌面小工具接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import UserDeviceSession
from app.modules.users.models import User
from app.modules.widget.schemas import WidgetSummaryRead
from app.modules.widget.service import get_widget_summary, validate_widget_access_scope
from app.shared.auth.deps import get_current_user
from app.shared.auth.device_deps import get_current_device_session_optional
from app.shared.db.session import get_db

router = APIRouter(prefix="/widget", tags=["widget"])


@router.get("/summary", response_model=WidgetSummaryRead)
async def widget_summary(
    limit: int = Query(default=5, ge=1, le=20, description="返回的摘要待办数量"),
    current_user: User = Depends(get_current_user),
    current_session: UserDeviceSession | None = Depends(get_current_device_session_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取桌面小工具摘要。"""
    validate_widget_access_scope(current_session)
    return await get_widget_summary(db, user=current_user, limit=limit)
