"""文章内容处理。"""

from __future__ import annotations

from datetime import datetime, timezone
import re


def _去除代码块(text: str) -> str:
    """移除 fenced code blocks 和 inline code。"""
    import re

    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def 计算字数(markdown_text: str | None) -> int:
    """计算 Markdown 文章的可读字数。"""
    from bs4 import BeautifulSoup

    if not markdown_text:
        return 0

    cleaned = _去除代码块(markdown_text)

    import markdown as md_lib

    html = md_lib.markdown(cleaned)
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text(separator=" ")
    plain_text = re.sub(r"\s+", " ", plain_text).strip()

    chinese_chars = re.findall(r"[\u4e00-\u9fa5]", plain_text)
    english_chars = re.findall(r"[a-zA-Z]", plain_text)
    return len(chinese_chars) + len(english_chars)


def 从Markdown首行提取标题(markdown_text: str | None) -> str:
    """提取 Markdown 首个非空行作为标题，并移除常见前缀标记。"""
    if not markdown_text:
        return ""

    for raw_line in markdown_text.replace("\ufeff", "").splitlines():
        title = raw_line.strip()
        if not title:
            continue

        previous_title = ""
        while title and title != previous_title:
            previous_title = title
            title = re.sub(r"^(?:>\s*)+", "", title).strip()
            title = re.sub(r"^#{1,6}(?:\s+|$)", "", title).strip()

        title = re.sub(r"\s+#{1,}\s*$", "", title).strip()
        return title

    return ""


def utcnow() -> datetime:
    """返回当前 UTC 时间。"""
    return datetime.now(timezone.utc)
