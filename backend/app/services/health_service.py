"""系统健康检查服务兼容入口。"""

from app.modules.system.health import get_health_check

__all__ = ["get_health_check"]
