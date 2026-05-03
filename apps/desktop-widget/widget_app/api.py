from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request


@dataclass(slots=True)
class TokenVerificationResult:
    ok: bool
    detail: str
    username: str | None = None
    pending_count: int = 0
    overdue_count: int = 0
    due_today_count: int = 0


def normalize_api_base(raw_value: str) -> str:
    value = raw_value.strip().rstrip("/")
    if not value:
        return "http://127.0.0.1:8000/api/v1"
    return value


def verify_widget_token(*, api_base_url: str, token: str) -> TokenVerificationResult:
    normalized_api_base = normalize_api_base(api_base_url)
    normalized_token = token.strip()
    if not normalized_token:
        return TokenVerificationResult(ok=False, detail="未提供小工具凭证")

    target_url = f"{normalized_api_base}/widget/summary"
    req = request.Request(
        target_url,
        headers={
            "Authorization": f"Bearer {normalized_token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with request.urlopen(req, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                return TokenVerificationResult(ok=False, detail="小工具摘要响应格式错误")
            username = str(payload.get("username", "")).strip() or None
            pending_count = int(payload.get("pending_count", 0) or 0)
            overdue_count = int(payload.get("overdue_count", 0) or 0)
            due_today_count = int(payload.get("due_today_count", 0) or 0)
            detail = f"摘要验证通过，待办 {pending_count} 项，今日到期 {due_today_count} 项"
            if overdue_count > 0:
                detail += f"，已逾期 {overdue_count} 项"
            if username:
                detail = f"{detail}，当前用户：{username}"
            return TokenVerificationResult(
                ok=True,
                detail=detail,
                username=username,
                pending_count=pending_count,
                overdue_count=overdue_count,
                due_today_count=due_today_count,
            )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        if body:
            return TokenVerificationResult(ok=False, detail=f"验证失败：{exc.code} {body}")
        return TokenVerificationResult(ok=False, detail=f"验证失败：HTTP {exc.code}")
    except error.URLError as exc:
        return TokenVerificationResult(ok=False, detail=f"请求失败：{exc.reason}")
