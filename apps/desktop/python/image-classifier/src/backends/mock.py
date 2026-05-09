from __future__ import annotations

import hashlib
from pathlib import Path

from .base import BaseClassifierBackend
from ..models import ALLOWED_LABELS, ClassificationResult


class MockClassifierBackend(BaseClassifierBackend):
    def classify(self, image_path: Path) -> ClassificationResult:
        digest = hashlib.md5(str(image_path).encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % len(ALLOWED_LABELS)
        label = ALLOWED_LABELS[index]
        confidence = 0.45 + (int(digest[8:12], 16) % 40) / 100
        return ClassificationResult(
            image_path=image_path,
            label=label,
            confidence=min(confidence, 0.99),
            reason="这是模拟后端生成的结果，用于验证界面和批处理流程。",
            raw_response=digest,
        )

    def test_connection(self) -> str:
        return "模拟后端可用，无需连接远程服务。"
