"""站内文件链接签名能力。"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from collections.abc import Mapping
from urllib.parse import parse_qsl, quote, unquote, urlsplit, urlunsplit

from app.shared.kernel.config import settings

文件访问路径前缀 = "/files/"
签名参数名 = "signature"
过期参数名 = "expires"
保留查询参数名 = {签名参数名, 过期参数名}
站内文件链接正则 = re.compile(r"(https?://[^\s\"'<>)]+/files/[^\s\"'<>)]+|/files/[^\s\"'<>)]+)")


def _获取签名密钥() -> str:
    """获取文件签名密钥。"""
    return settings.FILE_URL_SIGN_SECRET_KEY or settings.AUTH_SECRET_KEY


def _规范化查询参数(
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


def _构建签名载荷(
    storage_key: str,
    *,
    expires_at: int,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造参与签名的稳定字符串。"""
    lines = [storage_key, str(expires_at)]
    for key, value in _规范化查询参数(query_params):
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def 签署文件请求(
    storage_key: str,
    *,
    expires_at: int,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """为指定文件请求生成签名。"""
    payload = _构建签名载荷(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    return hmac.new(
        _获取签名密钥().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _编码查询参数(query_params: Mapping[str, str]) -> str:
    """将查询参数编码为查询字符串。"""
    return "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}"
        for key, value in query_params.items()
    )


def 验证已签署文件请求(
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

    expected_signature = 签署文件请求(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    return hmac.compare_digest(signature, expected_signature)


def 构建签名文件URL(
    storage_key: str,
    *,
    expires_in: int | None = None,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造带签名的站内文件 URL。"""
    normalized_storage_key = quote(storage_key, safe="/")
    expires_at = int(time.time()) + (expires_in or settings.FILE_URL_SIGN_EXPIRE_SECONDS)
    normalized_query_params = dict(_规范化查询参数(query_params))
    normalized_query_params[过期参数名] = str(expires_at)
    normalized_query_params[签名参数名] = 签署文件请求(
        storage_key,
        expires_at=expires_at,
        query_params=query_params,
    )
    query_string = _编码查询参数(normalized_query_params)
    return f"{文件访问路径前缀}{normalized_storage_key}?{query_string}"


def 构建公开文件URL(
    storage_key: str,
    *,
    query_params: Mapping[str, str | int | None] | None = None,
) -> str:
    """构造不带签名的站内文件 URL。"""
    normalized_storage_key = quote(storage_key, safe="/")
    query_string = _编码查询参数(dict(_规范化查询参数(query_params)))
    if not query_string:
        return f"{文件访问路径前缀}{normalized_storage_key}"
    return f"{文件访问路径前缀}{normalized_storage_key}?{query_string}"


def 从文件URL提取存储键(url: str | None) -> str | None:
    """从站内文件 URL 中提取对象存储键。"""
    if not url:
        return None

    parsed = urlsplit(url)
    path = parsed.path
    if not path.startswith(文件访问路径前缀):
        return None
    return unquote(path.removeprefix(文件访问路径前缀))


def 签署托管文件URL(url: str | None, *, expires_in: int | None = None) -> str | None:
    """将站内文件 URL 转换为签名 URL。"""
    if not url:
        return url

    storage_key = 从文件URL提取存储键(url)
    if storage_key is None:
        return url

    parsed = urlsplit(url)
    existing_query = {
        key: value
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key not in 保留查询参数名
    }
    signed_url = 构建签名文件URL(
        storage_key,
        expires_in=expires_in,
        query_params=existing_query,
    )
    signed_parsed = urlsplit(signed_url)

    if parsed.scheme or parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, signed_parsed.query, parsed.fragment))
    return urlunsplit(("", "", parsed.path, signed_parsed.query, parsed.fragment))


def 签署文本中托管文件URL(content: str, *, expires_in: int | None = None) -> str:
    """为文本中的站内文件 URL 批量附加签名。"""
    return 站内文件链接正则.sub(
        lambda match: 签署托管文件URL(match.group(0), expires_in=expires_in) or match.group(0),
        content,
    )
