"""文章内容处理。"""

from __future__ import annotations

from datetime import datetime, timezone


def _strip_code_blocks(text: str) -> str:
    """移除 fenced code blocks 和 inline code。"""
    import re

    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def calculate_word_count(markdown_text: str | None) -> int:
    """计算 Markdown 文章的可读字数。"""
    import re

    from bs4 import BeautifulSoup

    if not markdown_text:
        return 0

    cleaned = _strip_code_blocks(markdown_text)

    import markdown as md_lib

    html = md_lib.markdown(cleaned)
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text(separator=" ")
    plain_text = re.sub(r"\s+", " ", plain_text).strip()

    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", plain_text)
    english_chars = re.findall(r"[a-zA-Z]", plain_text)
    return len(chinese_chars) + len(english_chars)


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)
