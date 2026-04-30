"""邮箱工具。"""

from __future__ import annotations

谷歌邮箱域名集合 = frozenset({"gmail.com", "googlemail.com"})


def build_email_identity(email: str) -> str:
    """生成用于判重的邮箱标识。"""
    normalized = email.strip()
    local_part, separator, domain_part = normalized.rpartition("@")
    if not separator:
        return normalized.lower()

    normalized_domain = domain_part.lower()
    if normalized_domain not in 谷歌邮箱域名集合:
        return f"{local_part}@{normalized_domain}"

    normalized_local = local_part.lower()
    plus_index = normalized_local.find("+")
    if plus_index >= 0:
        normalized_local = normalized_local[:plus_index]
    normalized_local = normalized_local.replace(".", "")
    return f"{normalized_local}@gmail.com"
