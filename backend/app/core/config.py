"""从环境变量加载的应用配置。

此模块定义了应用的配置类，从 .env 文件加载环境变量。
配置项包括数据库连接、Redis、JWT、MinIO、管理员账户等。
"""

from __future__ import annotations

import json
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    CORS_ORIGINS: str = '["http://localhost:5173"]'  # CORS 允许的源（JSON 数组格式）
    # CORS_ALLOW_ORIGIN_REGEX: str = ""  # CORS 允许的正则匹配（暂不使用）

    @property
    def cors_origins_list(self) -> List[str]:
        """
        将 CORS_ORIGINS JSON 字符串解析为列表。

        Returns:
            List[str]: 允许的源列表
        """
        return json.loads(self.CORS_ORIGINS)

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

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET_KEY: str = "replace-with-a-very-long-random-string"  # 用于签名 JWT 的密钥
    JWT_ALGORITHM: str = "HS256"  # JWT 签名算法
    JWT_ACCESS_EXPIRE_MINUTES: int = 15  # Access Token 过期时间（分钟）
    JWT_REFRESH_EXPIRE_DAYS: int = 7  # Refresh Token 过期时间（天）

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


# 全局配置实例
settings = Settings()
