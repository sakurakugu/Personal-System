"""共享校验入口。"""

from app.core.validation import 请求校验异常处理器

已注销后缀 = "（已注销）"


def 校验用户名(value: str) -> str:
    """规范化并校验用户名。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("用户名不能为空")
    if 已注销后缀 in normalized:
        raise ValueError(f"用户名不能包含保留标记 {已注销后缀}")
    return normalized


__all__ = ["请求校验异常处理器", "校验用户名"]
