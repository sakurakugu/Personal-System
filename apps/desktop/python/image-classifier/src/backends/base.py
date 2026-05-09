from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ClassificationResult


class BaseClassifierBackend(ABC):
    @abstractmethod
    def classify(self, image_path: Path) -> ClassificationResult:
        raise NotImplementedError

    def test_connection(self) -> str:
        return "当前后端不需要额外连接测试。"

    def _parse_json_response(self, content: str) -> dict:
        cleaned = content.strip()
        candidates = [cleaned, self._strip_code_fences(cleaned)]
        decoder = json.JSONDecoder()

        for candidate in candidates:
            parsed = self._try_load_json_object(candidate)
            if parsed is not None:
                return parsed

            for index, char in enumerate(candidate):
                if char != "{":
                    continue
                try:
                    parsed, _ = decoder.raw_decode(candidate[index:])
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed

        return {"label": "other", "confidence": 0.0, "reason": cleaned}

    def _strip_code_fences(self, content: str) -> str:
        return re.sub(r"```(?:json)?", "", content, flags=re.IGNORECASE).strip()

    def _try_load_json_object(self, content: str) -> dict | None:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None
