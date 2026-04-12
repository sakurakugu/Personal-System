"""文件访问签名服务。"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from collections.abc import Mapping
from urllib.parse import parse_qsl, quote, unquote, urlsplit, urlunsplit

from app.core.config import settings

文件访问路径前缀 = "/files/"
签名参数名 = "signature"
过期参数名 = "expires"
保留查询参数名 = {签名参数名, 过期参数名}
站内文件链接正则 = re.compile(r"(https?://[^\s\"'<>)]+/files/[^\s\"'<>)]+|/files/[^\s\"'<>)]+)")


def _get_sign_secret() -> str:
    """获取文件签名密钥。"""
    return settings.FILE_URL_SIGN_SECRET_KEY or settings.AUTH_SECRET_KEY


def _normalize_query_params(
    query_params: Mapping[str, str | int | None] | None,
) -> tuple[tuple[str, str], ...]:
    """规范化参与签名的查询参数。"""
    if not query_params:
        return ()

    normalized_items: list[tuple[str, str]] = []
    for key, value in query_params.items():
        if key in 保留查询参数名 or value is None:
            continue
        normalized_items.append((key, str(value)))

    normalized_items.sort(key=lambda item: item[0])
    return tuple(normalized_items)


def _build_signature_payload(
    storage_key: str,
    *,
    expires_at: int,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造参与签名的稳定字符串。"""
    lines = [storage_key, str(expires_at)]
    for key, value in _normalize_query_params(query_params):
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def sign_file_request(
    storage_key: str,
    *,
    expires_at: int,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """为指定文件请求生成签名。"""
    payload = _build_signature_payload(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    return hmac.new(
        _get_sign_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _encode_query_params(query_params: Mapping[str, str]) -> str:
    """将查询参数编码为查询字符串。"""
    return "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}"
        for key, value in query_params.items()
    )


def verify_signed_file_request(
    storage_key: str,
    *,
    expires_at: int | None,
    signature: str | None,
    query_params: Mapping[str, str | int | None] | None = None,
    now_timestamp: int | None = None,
) -> bool:
    """校验文件请求签名是否有效。"""
    if expires_at is None or not signature:
        return False

    current_timestamp = now_timestamp if now_timestamp is not None else int(time.time())
    if expires_at < current_timestamp:
        return False

    expected_signature = sign_file_request(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    return hmac.compare_digest(signature, expected_signature)


def build_signed_file_url(
    storage_key: str,
    *,
    expires_in: int | None = None,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造带签名的站内文件 URL。"""
    normalized_storage_key = quote(storage_key, safe="/")
    expires_at = int(time.time()) + (expires_in or settings.FILE_URL_SIGN_EXPIRE_SECONDS)
    normalized_query_params = dict(_normalize_query_params(query_params))
    normalized_query_params[过期参数名] = str(expires_at)
    normalized_query_params[签名参数名] = sign_file_request(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    query_string = _encode_query_params(normalized_query_params)
    return f"{文件访问路径前缀}{normalized_storage_key}?{query_string}"


def build_public_file_url(
    storage_key: str,
    *,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造不带签名的站内文件 URL。"""
    normalized_storage_key = quote(storage_key, safe="/")
    query_string = _encode_query_params(dict(_normalize_query_params(query_params)))
    if not query_string:
        return f"{文件访问路径前缀}{normalized_storage_key}"
    return f"{文件访问路径前缀}{normalized_storage_key}?{query_string}"


def extract_storage_key_from_file_url(url: str | None) -> str | None:
    """从站内文件 URL 中提取对象存储键。"""
    if not url:
        return None

    parsed = urlsplit(url)
    path = parsed.path
    if not path.startswith(文件访问路径前缀):
        return None
    return unquote(path.removeprefix(文件访问路径前缀))


def sign_managed_file_url(url: str | None, *, expires_in: int | None = None) -> str | None:
    """将站内文件 URL 转换为签名 URL。"""
    if not url:
        return url

    storage_key = extract_storage_key_from_file_url(url)
    if storage_key is None:
        return url

    parsed = urlsplit(url)
    existing_query = {
        key: value
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key not in 保留查询参数名
    }
    signed_url = build_signed_file_url(
        storage_key,
        expires_in=expires_in,
        query_params=existing_query,
    )
    signed_parsed = urlsplit(signed_url)

    if parsed.scheme or parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, signed_parsed.query, parsed.fragment))
    return urlunsplit(("", "", parsed.path, signed_parsed.query, parsed.fragment))


def sign_managed_file_urls_in_text(content: str, *, expires_in: int | None = None) -> str:
    """为文本中的站内文件 URL 批量附加签名。"""
    return 站内文件链接正则.sub(
        lambda match: sign_managed_file_url(match.group(0), expires_in=expires_in) or match.group(0),
        content,
    )
