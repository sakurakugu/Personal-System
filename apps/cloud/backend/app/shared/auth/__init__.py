"""认证共享能力。"""

from app.shared.auth.deps import 获取当前用户, 获取当前用户可选, 要求当前用户
from app.shared.auth.device_deps import 获取当前设备会话, 获取当前设备会话可选, 要求设备权限范围

__all__ = [
    "获取当前用户",
    "获取当前用户可选",
    "获取当前设备会话",
    "获取当前设备会话可选",
    "要求当前用户",
    "要求设备权限范围",
]
