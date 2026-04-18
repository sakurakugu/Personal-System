"""Alembic env.py – 异步迁移运行器。

此文件是 Alembic 迁移工具的配置入口，负责设置数据库连接并执行迁移。
支持离线（offline）和在线（online）两种迁移模式。
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.shared.db.session import Base

# 导入所有模型以填充元数据
import app.models  # noqa: F401

# Alembic 配置对象，从 alembic.ini 加载配置
config = context.config

# 如果配置文件存在，则配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据，用于生成迁移脚本时对比数据库结构
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    以离线模式运行迁移。

    离线模式下，Alembic 只生成 SQL 语句而不实际执行，适用于：
    - 需要审查迁移 SQL 的场景
    - 无法直接连接数据库的环境
    """
    # 从配置中获取数据库连接 URL
    url = settings.DATABASE_URL
    # 配置 Alembic 上下文，使用字面量绑定（生成实际 SQL）
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # 启用字面量绑定，生成可读的 SQL
        dialect_opts={"paramstyle": "named"},  # 使用命名参数风格
    )
    # 在事务中执行迁移
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    实际执行迁移的核心函数。

    Args:
        connection: SQLAlchemy 数据库连接对象
    """
    # 配置 Alembic 上下文，传入数据库连接和元数据
    context.configure(connection=connection, target_metadata=target_metadata)
    # 在事务中执行迁移
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    异步执行数据库迁移。

    创建异步数据库引擎，建立连接并执行迁移，最后释放资源。
    """
    # 创建异步数据库引擎，pool_pre_ping=True 用于检测连接是否有效
    connectable = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

    # 使用异步上下文管理器管理连接
    async with connectable.connect() as connection:
        # run_sync 将同步的迁移函数包装为异步执行
        await connection.run_sync(do_run_migrations)

    # 释放引擎占用的资源
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    以在线模式运行迁移。

    在线模式下，Alembic 会直接连接数据库并执行迁移操作。
    使用 asyncio 运行异步迁移任务。
    """
    asyncio.run(run_async_migrations())


# 根据 Alembic 上下文判断当前模式（离线或在线）并执行相应逻辑
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
