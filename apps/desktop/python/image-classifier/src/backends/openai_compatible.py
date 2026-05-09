from __future__ import annotations

from pathlib import Path

import requests

from .base import BaseClassifierBackend
from ..image_support import encode_image_as_png_data_url
from ..models import ALLOWED_LABELS, BackendConfig, ClassificationResult


SYSTEM_PROMPT = """你是一个图像分类引擎。
请从下面的封闭标签集合中，且只能选一个标签：
- screenshot_text
- cosplay
- anime_art
- meme
- other

标签定义：
- screenshot_text：截图、界面截屏、文档截图、聊天记录截图，或以文字内容为主的图片。
- cosplay：真人扮演虚构角色的照片（包括色情图）。
- anime_art：动漫图片、漫画风插画、非写实的二维绘画作品（包括色情图）。
- meme：表情包、梗图、反应图，或带文字梗的幽默图片。
- other：无法明确判断，或不属于以上任一类别。

只返回 JSON，且必须严格符合下面这个结构：
{"label":"other","confidence":0.0,"reason":""}

规则：
- label 必须是上面五个英文标签之一，不能翻译成中文。
- confidence 必须是 0 到 1 之间的数字。
- reason 必须使用简体中文，简洁说明判断依据。
- 如果不确定，使用 other。
- 不要返回 markdown，不要返回额外说明文字。
"""


class OpenAICompatibleBackend(BaseClassifierBackend):
    def __init__(self, config: BackendConfig):
        self.config = config

    def classify(self, image_path: Path) -> ClassificationResult:
        payload = self._build_payload(image_path)
        response = requests.post(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = self._parse_content(content)
        label = parsed.get("label", "other")
        if label not in ALLOWED_LABELS:
            label = "other"
        confidence = parsed.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(confidence, 1.0))
        reason = str(parsed.get("reason", ""))
        return ClassificationResult(
            image_path=image_path,
            label=label,
            confidence=confidence,
            reason=reason,
            raw_response=content,
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self.config.extra_headers}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _build_payload(self, image_path: Path) -> dict:
        image_url = self._to_data_url(image_path)
        return {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请对这张图片进行分类，只返回 JSON。label 保持英文枚举值，reason 使用简体中文。",
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            "temperature": 0,
            "max_tokens": 256,
            "chat_template_kwargs": {"enable_thinking": False},
        }

    def test_connection(self) -> str:
        response = requests.get(
            f"{self.config.base_url.rstrip('/')}/models",
            headers=self._headers(),
            timeout=min(self.config.timeout_seconds, 15),
        )
        response.raise_for_status()
        data = response.json()
        models = [item.get("id", "") for item in data.get("data", [])]
        if self.config.model and models and self.config.model not in models:
            return (
                f"服务可访问，但未找到模型 {self.config.model}。"
                f" 当前可见模型：{', '.join(models[:8])}"
            )
        return f"连接成功。服务地址：{self.config.base_url}"

    def _to_data_url(self, image_path: Path) -> str:
        return encode_image_as_png_data_url(image_path)

    def _parse_content(self, content: str) -> dict:
        return self._parse_json_response(content)
