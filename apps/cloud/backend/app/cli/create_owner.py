"""创建首个 owner 用户的显式命令。"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.security import 哈希密码
from app.modules.users.models import 用户, 用户角色, 构建默认用户设置
from app.shared.db.session import async_session_factory, engine
from app.shared.kernel.config import settings


async def 创建首个Owner() -> bool:
    """仅在 users 为空时创建 owner，返回是否实际创建。"""
    async with async_session_factory() as db:
        result = await db.execute(select(用户).limit(1))
        if result.scalar_one_or_none() is not None:
            return False

        owner = 用户(
            username=settings.ADMIN_USERNAME,
            nickname=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=哈希密码(settings.ADMIN_PASSWORD),
            role=用户角色.admin,
            is_active=True,
            settings=构建默认用户设置(),
        )
        db.add(owner)
        await db.commit()
        return True


async def 主程序() -> int:
    """执行 owner 初始化并释放数据库引擎。"""
    try:
        created = await 创建首个Owner()
        if created:
            print(f"已创建首个 owner 用户：{settings.ADMIN_USERNAME}")
            return 0
        print("创建取消：数据库中已经存在用户，未修改任何数据。")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(主程序()))
