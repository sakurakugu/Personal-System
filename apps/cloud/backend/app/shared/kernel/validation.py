"""共享校验入口。"""

from app.core.validation import request_validation_exception_handler

已注销后缀 = "（已注销）"


def validate_username(value: str) -> str:
    """规范化并校验用户名。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("用户名不能为空")
    if 已注销后缀 in normalized:
        raise ValueError(f"用户名不能包含保留标记 {已注销后缀}")
    return normalized


__all__ = ["request_validation_exception_handler", "validate_username"]
