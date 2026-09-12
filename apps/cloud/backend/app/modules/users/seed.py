"""启动阶段的用户初始化。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import 哈希密码
from app.modules.users.models import 用户, 构建默认用户设置
from app.shared.kernel.config import settings


async def 首次创建用户(db: AsyncSession) -> None:
    """数据库为空时创建唯一 owner，已有任意用户都不再新增账号。"""
    result = await db.execute(select(用户).limit(1))
    if result.scalar_one_or_none():
        return

    owner = 用户(
        username=settings.ADMIN_USERNAME,
        nickname=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=哈希密码(settings.ADMIN_PASSWORD),
        settings=构建默认用户设置(),
    )
    db.add(owner)
    await db.commit()
    print(f"[seed] 已创建 owner 用户：{settings.ADMIN_USERNAME}")
