"""用户资料路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import 用户
from app.modules.users.profile import (
    修改当前用户密码,
    更新当前用户,
)
from app.modules.users.schemas import (
    用户修改密码,
    用户信息,
    用户更新,
)
from app.shared.auth.deps import 获取当前用户
from app.shared.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=用户信息)
async def get_me(user: 用户 = Depends(获取当前用户)):
    """获取当前登录用户的资料。"""
    return user


@router.patch("/me", response_model=用户信息)
async def update_me(
    body: 用户更新,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的资料。"""
    return await 更新当前用户(db, user, body)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def 修改我的密码(
    body: 用户修改密码,
    user: 用户 = Depends(获取当前用户),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户的密码。"""
    await 修改当前用户密码(db, user, body)


__all__ = [
    "router",
]
