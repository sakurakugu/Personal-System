"""桌面小工具接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.device_models import 用户设备会话
from app.modules.users.models import 用户
from app.modules.widget.schemas import WidgetPublicSummaryRead, WidgetSummaryRead
from app.modules.widget.service import 获取公开小工具摘要, 获取小工具摘要, 校验小工具访问范围
from app.shared.auth.deps import 获取当前用户可选
from app.shared.auth.device_deps import 获取当前设备会话可选
from app.shared.db.session import get_db

router = APIRouter(prefix="/widget", tags=["widget"])


@router.get("/summary", response_model=WidgetSummaryRead | WidgetPublicSummaryRead)
async def widget_summary(
    limit: int = Query(default=5, ge=1, le=20, description="返回的摘要待办数量"),
    current_user: 用户 | None = Depends(获取当前用户可选),
    current_session: 用户设备会话 | None = Depends(获取当前设备会话可选),
    db: AsyncSession = Depends(get_db),
):
    """获取桌面小工具摘要。"""
    校验小工具访问范围(current_session)
    if current_user is None:
        return await 获取公开小工具摘要(db, limit=limit)
    return await 获取小工具摘要(db, user=current_user, limit=limit)
