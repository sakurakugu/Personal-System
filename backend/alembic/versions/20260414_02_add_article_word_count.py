"""为文章表新增字数统计字段。

Revision ID: 20260414_02
Revises: 20260414_01
Create Date: 2026-04-14 21:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260414_02"
down_revision = "20260414_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构并回填已有数据。"""
    op.add_column(
        "articles",
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 使用 Alembic 的 batch context 直接获取 connection 以回填数据
    connection = op.get_bind()
    articles = connection.execute(
        sa.text("SELECT id, content FROM articles WHERE word_count = 0")
    ).fetchall()

    if articles:
        import re

        from bs4 import BeautifulSoup

        def _calculate_word_count(markdown_text: str | None) -> int:
            if not markdown_text:
                return 0
            text = re.sub(r"```[\s\S]*?```", " ", markdown_text)
            text = re.sub(r"`[^`]*`", " ", text)

            import markdown as md_lib

            html = md_lib.markdown(text)
            soup = BeautifulSoup(html, "html.parser")
            plain_text = soup.get_text(separator=" ")
            plain_text = re.sub(r"\s+", " ", plain_text).strip()

            chinese_chars = re.findall(r"[\u4e00-\u9fa5]", plain_text)
            english_chars = re.findall(r"[a-zA-Z]", plain_text)
            return len(chinese_chars) + len(english_chars)

        for article_id, content in articles:
            word_count = _calculate_word_count(content)
            connection.execute(
                sa.text("UPDATE articles SET word_count = :wc WHERE id = :id"),
                {"wc": word_count, "id": str(article_id)},
            )

    op.alter_column("articles", "word_count", server_default=None)


def downgrade() -> None:
    """回滚数据库结构。"""
    op.drop_column("articles", "word_count")
