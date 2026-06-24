"""文章 AI 辅助服务测试。"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.modules.articles.ai_service import (
    _提取JSON对象,
    _提取润色结果,
    润色正文开始标记,
    润色摘要开始标记,
    润色结束标记,
    生成文章元信息建议,
    润色文章正文,
)
from app.modules.articles.schemas import 文章AI元信息建议请求, 文章AI正文润色请求
from app.modules.users.models import 用户, 用户角色
from app.utils.uuid import generate_uuid7


class 文章AI服务测试(unittest.TestCase):
    """文章 AI 辅助纯逻辑测试。"""

    def test_可从代码围栏中提取JSON对象(self) -> None:
        data = _提取JSON对象('```json\n{"title":"标题","tag_names":["AI"]}\n```')

        self.assertEqual(data["title"], "标题")
        self.assertEqual(data["tag_names"], ["AI"])

    def test_非JSON返回会拒绝(self) -> None:
        with self.assertRaises(HTTPException):
            _提取JSON对象("这不是 JSON")

    def test_润色结果支持包含代码块的Markdown(self) -> None:
        result = _提取润色结果(
            f"{润色摘要开始标记}\n优化表达\n"
            f"{润色正文开始标记}\n"
            "# 标题\n\n```markdown\n# 代码块里的标题\n```\n"
            f"{润色结束标记}"
        )

        self.assertEqual(result.summary, "优化表达")
        self.assertIn("```markdown", result.content)
        self.assertIn("# 代码块里的标题", result.content)


class 文章AI服务异步测试(unittest.IsolatedAsyncioTestCase):
    """文章 AI 辅助异步测试。"""

    def build_user(self) -> 用户:
        """构造测试用户。"""
        return 用户(
            id=generate_uuid7(),
            username="author",
            email="author@example.com",
            password_hash="x",
            role=用户角色.user,
        )

    async def test_元信息建议会校验结构化响应(self) -> None:
        body = 文章AI元信息建议请求(
            title="",
            content="# 原文\n正文",
            excerpt="",
            category_names=["技术"],
            tag_names=["Python"],
        )

        with patch(
            "app.modules.articles.ai_service.生成AI文本回复",
            AsyncMock(return_value='{"title":"新标题","excerpt":"摘要内容","category_name":"技术","tag_names":["Python"],"reason":"依据正文"}'),
        ):
            result = await 生成文章元信息建议(AsyncMock(), self.build_user(), body)

        self.assertEqual(result.title, "新标题")
        self.assertEqual(result.category_name, "技术")
        self.assertEqual(result.tag_names, ["Python"])

    async def test_正文润色会返回完整正文(self) -> None:
        body = 文章AI正文润色请求(
            title="标题",
            content="# 标题\n旧正文",
            excerpt="",
            category_names=[],
            tag_names=[],
        )

        with patch(
            "app.modules.articles.ai_service.生成AI文本回复",
            AsyncMock(
                return_value=(
                    f"{润色摘要开始标记}\n优化表达\n"
                    f"{润色正文开始标记}\n# 标题\n新正文\n"
                    f"{润色结束标记}"
                )
            ),
        ):
            result = await 润色文章正文(AsyncMock(), self.build_user(), body)

        self.assertEqual(result.content, "# 标题\n新正文")
        self.assertEqual(result.summary, "优化表达")
