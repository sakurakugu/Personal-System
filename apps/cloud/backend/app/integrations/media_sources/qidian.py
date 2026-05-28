# mypy: ignore-errors
"""起点中文网文娱数据源。"""

from __future__ import annotations

import html
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.integrations.media_sources.base import 外部作品候选, 外部文娱数据源, 规范化文本

移动端请求头 = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

搜索结果链接正则 = re.compile(
    r"<a\b(?=[^>]*\bdata-bid=\"(?P<book_id>\d+)\")(?P<attrs>[^>]*)>(?P<body>.*?)</a>",
    re.DOTALL | re.IGNORECASE,
)


class 起点数据源(外部文娱数据源):
    """起点中文网数据源，只读取公开作品元数据。"""

    provider = "qidian"
    base_url = "https://m.qidian.com"

    async def search(self, keyword: str, media_type: str | None) -> list[外部作品候选]:
        """搜索起点作品。"""
        if media_type and media_type not in {"novel", "book"}:
            return []
        url = f"{self.base_url}/so/{quote(keyword)}.html"
        response = await self.client.get(url, headers=移动端请求头)
        response.raise_for_status()
        return self._解析搜索结果(response.text)

    async def get_detail(self, external_id: str) -> 外部作品候选:
        """读取起点作品详情。"""
        if not external_id.isdigit():
            raise httpx.HTTPStatusError(
                "起点作品 ID 格式无效",
                request=httpx.Request("GET", f"{self.base_url}/book/{external_id}/"),
                response=httpx.Response(400),
            )
        response = await self.client.get(f"{self.base_url}/book/{external_id}/", headers=移动端请求头)
        response.raise_for_status()
        return self._解析详情(external_id, response.text)

    def _解析搜索结果(self, text: str) -> list[外部作品候选]:
        """从移动端搜索页解析作品卡片。"""
        items: list[外部作品候选] = []
        seen: set[str] = set()
        for match in 搜索结果链接正则.finditer(text):
            book_id = match.group("book_id")
            if book_id in seen:
                continue
            seen.add(book_id)
            body = match.group("body")
            title = self._清理HTML文本(self._提取首个片段(body, r"<h2\b[^>]*>(.*?)</h2>"))
            if not title:
                title = self._清理HTML文本(self._提取属性(match.group("attrs"), "title")).removesuffix("在线阅读")
            if not title:
                continue
            summary = self._清理HTML文本(self._提取首个片段(body, r"<p\b[^>]*_searchBookDesc_[^>]*>(.*?)</p>"))
            author = self._清理HTML文本(self._提取首个片段(body, r"<p\b[^>]*_searchBookAuthor_[^>]*>(.*?)</p>"))
            tags = self._解析标签(body)
            category = tags[0] if tags else None
            cover_url = self._规范化URL(self._提取图片地址(body))
            items.append(
                外部作品候选(
                    provider=self.provider,
                    external_id=book_id,
                    title=title,
                    media_type="novel",
                    creators=[author] if author else [],
                    summary=summary,
                    description=summary,
                    genres=[category] if category else [],
                    tags=tags[1:],
                    cover_url=cover_url,
                    thumbnail_url=cover_url,
                    external_url=f"https://www.qidian.com/book/{book_id}/",
                    raw={
                        "source": "m.qidian.com search",
                        "tags": tags,
                    },
                )
            )
            if len(items) >= 12:
                break
        return items

    def _解析详情(self, external_id: str, text: str) -> 外部作品候选:
        """从移动端详情页解析 OpenGraph 小说元数据。"""
        soup = BeautifulSoup(text, "html.parser")
        meta = self._读取元标签(soup)
        title = (
            规范化文本(meta.get("og:novel:book_name"))
            or 规范化文本(meta.get("og:title"))
            or external_id
        )
        author = 规范化文本(meta.get("og:novel:author"))
        summary = 规范化文本(meta.get("og:description")) or 规范化文本(meta.get("description"))
        category = 规范化文本(meta.get("og:novel:category"))
        status = 规范化文本(meta.get("og:novel:status"))
        cover_url = self._规范化URL(meta.get("og:image"))
        return 外部作品候选(
            provider=self.provider,
            external_id=external_id,
            title=title,
            media_type="novel",
            creators=[author] if author else [],
            summary=summary,
            description=summary,
            genres=[category] if category else [],
            tags=[status] if status else [],
            cover_url=cover_url,
            thumbnail_url=cover_url,
            external_url=f"https://www.qidian.com/book/{external_id}/",
            raw={
                "source": "m.qidian.com detail",
                "mobile_url": f"{self.base_url}/book/{external_id}/",
                "meta": meta,
            },
        )

    def _读取元标签(self, soup: BeautifulSoup) -> dict[str, str]:
        """读取页面中的 meta 标签。"""
        meta: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if isinstance(key, str) and isinstance(content, str):
                normalized = content.strip()
                if normalized:
                    meta[key.strip()] = normalized
        return meta

    def _解析标签(self, body: str) -> list[str]:
        """解析搜索卡片中的分类、状态和字数标签。"""
        tags_html = self._提取首个片段(body, r"<div\b[^>]*_tags_[^>]*>(.*?)</div>")
        tags: list[str] = []
        for item in re.findall(r"<p\b[^>]*>(.*?)</p>", tags_html, flags=re.DOTALL | re.IGNORECASE):
            text = self._清理HTML文本(item)
            if text:
                tags.append(text)
        return tags

    def _提取图片地址(self, body: str) -> str | None:
        """提取搜索卡片封面地址。"""
        image_match = re.search(r"<img\b[^>]*>", body, flags=re.DOTALL | re.IGNORECASE)
        image_html = image_match.group(0) if image_match else ""
        return self._提取属性(image_html, "data-src") or self._提取属性(image_html, "src")

    def _提取首个片段(self, text: str, pattern: str) -> str:
        """按正则提取第一个分组。"""
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else ""

    def _提取属性(self, text: str, name: str) -> str | None:
        """从 HTML 标签片段中提取属性。"""
        match = re.search(rf"\b{re.escape(name)}=(?P<quote>['\"])(?P<value>.*?)(?P=quote)", text, re.IGNORECASE)
        if not match:
            return None
        return html.unescape(match.group("value").strip())

    def _清理HTML文本(self, value: object) -> str | None:
        """清理搜索结果中的 HTML 文本。"""
        if not isinstance(value, str):
            return None
        text = re.sub(r"<[^>]+>", "", value)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text or None

    def _规范化URL(self, value: object) -> str | None:
        """规范化起点页面里的协议相对 URL。"""
        url = 规范化文本(value)
        if not url:
            return None
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith("/"):
            return f"{self.base_url}{url}"
        return url
