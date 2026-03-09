"""从环境变量加载的应用配置。"""

from __future__ import annotations

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 应用 ──────────────────────────────────────────────
    APP_ENV: str = "production"
    APP_DEBUG: bool = False
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # ── PostgreSQL ───────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://bloguser:change_me_in_production@localhost:5432/blogdb"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET_KEY: str = "replace-with-a-very-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── MinIO ────────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "blog-uploads"
    MINIO_USE_SSL: bool = False
    MINIO_PUBLIC_URL: str = "https://api.sakurakugu.top/files"

    # ── 管理员播种 ─────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@sakurakugu.top"
    ADMIN_PASSWORD: str = "change_me_admin"


settings = Settings()
