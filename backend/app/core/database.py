"""异步 SQLAlchemy 引擎和会话工厂。

此模块提供数据库连接和会话管理：
- 异步数据库引擎配置
- 会话工厂和依赖注入函数
- 声明式基类定义
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 创建异步数据库引擎
# echo: 是否输出 SQL 语句（仅在调试模式开启）
# pool_size: 连接池大小
# max_overflow: 连接池溢出上限
# pool_pre_ping: 使用前检查连接是否有效
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

# 创建异步会话工厂
# expire_on_commit=False: 提交后不使对象过期，便于后续访问
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。

    所有 ORM 模型都继承此类，用于元数据管理和表创建。
    """
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    FastAPI 依赖 – 提供异步数据库会话。

    使用上下文管理器确保会话正确关闭，自动处理提交和回滚：
    - 正常完成时提交事务
    - 发生异常时回滚事务并抛出异常

    Yields:
        AsyncSession: 数据库会话对象

    Example:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
