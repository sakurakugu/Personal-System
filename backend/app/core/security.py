"""JWT 和密码加密工具。

此模块提供安全相关的工具函数：
- 密码哈希和验证（使用 bcrypt）
- JWT 令牌生成和验证
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings


# ── 密码 ────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    对明文密码进行 bcrypt 哈希。

    Args:
        plain: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配。

    Args:
        plain: 明文密码
        hashed: 哈希密码

    Returns:
        bool: 是否匹配
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT ─────────────────────────────────────────────────

def create_access_token(subject: str, extra: dict | None = None) -> str:
    """
    创建 JWT Access Token。

    Access Token 用于身份验证，有效期较短（默认 15 分钟）。

    Args:
        subject: 令牌主题（通常是用户 ID）
        extra: 额外的声明数据（如用户角色）

    Returns:
        str: 编码后的 JWT 字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    创建 JWT Refresh Token。

    Refresh Token 用于获取新的 Access Token，有效期较长（默认 7 天）。

    Args:
        subject: 令牌主题（通常是用户 ID）

    Returns:
        str: 编码后的 JWT 字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    解码并验证 JWT Token。

    Args:
        token: JWT 字符串

    Returns:
        dict: 令牌载荷数据

    Raises:
        JWTError: 令牌无效或已过期
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
