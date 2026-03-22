"""数据库迁移脚本 - 添加评论点赞功能。

添加 comment_likes 表和 comments.like_count 列
"""

import asyncio

from sqlalchemy import text

from app.core.database import engine


async def migrate():
    """执行迁移。"""
    async with engine.begin() as conn:
        # 检查 like_count 列是否已存在
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'comments' AND column_name = 'like_count'
        """))
        
        if not result.fetchone():
            # 添加 like_count 列
            await conn.execute(text("""
                ALTER TABLE comments
                ADD COLUMN like_count INTEGER NOT NULL DEFAULT 0
            """))
            print("✓ 添加 like_count 列到 comments 表")
        else:
            print("- like_count 列已存在，跳过")

        # 检查 comment_likes 表是否已存在
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'comment_likes'
        """))
        
        if not result.fetchone():
            # 创建 comment_likes 表
            await conn.execute(text("""
                CREATE TABLE comment_likes (
                    comment_id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (comment_id, user_id),
                    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            print("✓ 创建 comment_likes 表")
        else:
            print("- comment_likes 表已存在，跳过")

        print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
