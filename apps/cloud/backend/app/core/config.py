"""从环境变量加载的应用配置。

此模块定义了应用的配置类，从 .env 文件加载环境变量。
配置项包括数据库连接、Redis、认证 Cookie、MinIO、管理员账户等。
"""

from __future__ import annotations

import json
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic_settings import BaseSettings, SettingsConfigDict

开发环境默认跨源来源 = [
    "http://localhost",
    "capacitor://localhost",
]

生产环境默认跨源来源 = [
    "https://www.sakurakugu.top",
    "https://sakurakugu.top",
    "http://localhost",
    "http://localhost:1420",
    "capacitor://localhost",
    "http://tauri.localhost",
    "tauri://localhost",
]


class Settings(BaseSettings):
    """
    应用配置类。

    从 .env 文件加载配置，支持类型验证和默认值。
    所有配置项都可以通过环境变量覆盖。
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未定义的配置项
    )

    # ── 应用 ──────────────────────────────────────────────
    APP_ENV: str = "production"  # 应用环境：development / production
    APP_DEBUG: bool = False  # 是否开启调试模式
    APP_TIMEZONE: str = "Asia/Shanghai"  # 应用业务时区
    CORS_ORIGINS: str = ""  # 留空时按环境使用默认 CORS 来源（JSON 数组格式）
    # CORS_ALLOW_ORIGIN_REGEX: str = ""  # CORS 允许的正则匹配（暂不使用）

    @property
    def cors_origins_list(self) -> List[str]:
        """
        返回当前环境下实际生效的 CORS 来源列表。

        Returns:
            List[str]: 允许的源列表
        """
        configured = self.CORS_ORIGINS.strip()
        if configured:
            return json.loads(configured)
        if self.APP_ENV == "development":
            return 开发环境默认跨源来源.copy()
        return 生产环境默认跨源来源.copy()

    @property
    def app_timezone(self) -> ZoneInfo:
        """返回业务统一使用的时区对象。"""
        try:
            return ZoneInfo(self.APP_TIMEZONE)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"无效的 APP_TIMEZONE 配置: {self.APP_TIMEZONE}") from exc

    # @property
    # def cors_allow_origin_regex(self) -> str | None:
        # return self.CORS_ALLOW_ORIGIN_REGEX or None

    # ── PostgreSQL ───────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://bloguser:change_me_in_production@127.0.0.1:5432/blogdb"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # ── 认证 ─────────────────────────────────────────────
    AUTH_SECRET_KEY: str = "replace-with-a-very-long-random-string"  # 认证与文件签名使用的主密钥
    AUTH_SESSION_EXPIRE_DAYS: int = 30  # 登录会话过期时间（天）
    AUTH_SESSION_COOKIE_NAME: str = "session_id"  # Session Cookie 名称
    AUTH_CSRF_COOKIE_NAME: str = "csrf_token"  # CSRF Cookie 名称
    AUTH_CSRF_HEADER_NAME: str = "X-CSRF-Token"  # CSRF 请求头名称
    AUTH_COOKIE_PATH: str = "/"  # 认证 Cookie 生效路径
    AUTH_COOKIE_DOMAIN: str = ""  # 认证 Cookie 域名，留空表示仅当前主机
    AUTH_COOKIE_SAMESITE: str = "lax"  # 认证 Cookie SameSite 策略；原生 App 连接云端时通常需要 none
    AUTH_COOKIE_SECURE: bool = False  # 认证 Cookie 是否仅通过 HTTPS 发送
    AUTH_DEVICE_TOKEN_PREFIX: str = "pst_dev"  # 设备令牌前缀
    AUTH_DEVICE_EXPIRE_DAYS: int = 30  # 桌面端设备会话过期时间（天）
    AUTH_DEVICE_WIDGET_EXPIRE_DAYS: int = 90  # 小工具设备会话过期时间（天）
    FILE_URL_SIGN_SECRET_KEY: str = ""  # 文件访问签名密钥，留空时回退到主认证密钥
    FILE_URL_SIGN_EXPIRE_SECONDS: int = 900  # 文件签名 URL 默认有效期（秒）

    # ── MinIO ────────────────────────────────────────────
    MINIO_ENDPOINT: str = "127.0.0.1:9000"  # MinIO 服务端点
    MINIO_ACCESS_KEY: str = "minioadmin"  # MinIO 访问密钥
    MINIO_SECRET_KEY: str = "minioadmin"  # MinIO 秘密密钥
    MINIO_BUCKET: str = "blog-uploads"  # 文件存储桶名称
    MINIO_USE_SSL: bool = False  # 是否使用 SSL 连接 MinIO
    MINIO_PUBLIC_URL: str = "https://api.sakurakugu.top/files"  # 文件公开访问 URL

    # ── 管理员信息 ─────────────────────────────────────────
    # 初始超级管理员账户（首次启动时自动创建）
    SUPER_ADMIN_USERNAME: str = "superadmin"
    SUPER_ADMIN_EMAIL: str = "superadmin@sakurakugu.top"
    SUPER_ADMIN_PASSWORD: str = "change_me_super_admin"
    
    # 开发模式管理员账户
    DEV_ADMIN_USERNAME: str = "dev_admin"
    DEV_ADMIN_EMAIL: str = "dev_admin@sakurakugu.top"
    DEV_ADMIN_PASSWORD: str = "change_me_dev_admin"
    # 开发模式普通用户账户
    DEV_USER_USERNAME: str = "dev_user"
    DEV_USER_EMAIL: str = "dev_user@sakurakugu.top"
    DEV_USER_PASSWORD: str = "change_me_dev_user"

    # ── 站点信息 ───────────────────────────────────────────
    SITE_URL: str = "https://www.sakurakugu.top"  # 用于友链自动检测

    # ── Twikoo 运维 ───────────────────────────────────────
    TWIKOO_DATA_DIR: str = "/app/twikoo-data"  # Twikoo 数据目录，供后端直接重置密码使用
    TWIKOO_CONTAINER_NAME: str = "personal-system-twikoo-1"  # Twikoo 容器名称
    TWIKOO_CONTAINER_DATA_DIR: str = "/app/data"  # Twikoo 容器内数据目录
    DOCKER_SOCKET_PATH: str = "/var/run/docker.sock"  # Docker Socket 路径，用于容器内重启 Twikoo


# 全局配置实例
settings = Settings()
