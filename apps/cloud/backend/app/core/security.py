"""密码加密工具。

此模块提供安全相关的工具函数：
- 密码哈希和验证（使用 bcrypt）
"""

from __future__ import annotations

import bcrypt


# ── 密码 ────────────────────────────────────────────────

def 哈希密码(plain: str) -> str:
    """
    对明文密码进行 bcrypt 哈希。

    Args:
        plain: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def 验证密码(plain: str, hashed: str) -> bool:
    """
    验证明文密码与散列后的密码是否匹配。

    Args:
        plain: 明文密码
        hashed: 哈希密码

    Returns:
        bool: 是否匹配
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

