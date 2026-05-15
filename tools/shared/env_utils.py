""".env 文件与环境变量工具。"""

from __future__ import annotations

import os
import secrets
import urllib.request
from pathlib import Path
from typing import Dict, Optional

from .config import (
    CLOUD_ENV_EXAMPLE_FILE,
    CLOUD_ENV_FILE,
    ELECTRON_BUILDER_BINARIES_MIRROR,
    ELECTRON_MIRROR,
    PHONE_ENV_EXAMPLE_FILE,
    PHONE_ENV_FILE,
    ROOT_DIR,
)
from .terminal import echo


def 获取代理环境变量(base_env: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    proxies = urllib.request.getproxies()
    proxy_keys = {
        "http": ("HTTP_PROXY", "http_proxy"),
        "https": ("HTTPS_PROXY", "https_proxy"),
        "all": ("ALL_PROXY", "all_proxy"),
        "no": ("NO_PROXY", "no_proxy"),
    }
    for scheme, keys in proxy_keys.items():
        value = env.get(keys[0]) or env.get(keys[1]) or proxies.get(scheme)
        if value:
            for key in keys:
                env[key] = value
    return env


def 获取桌面端环境变量(base_env: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = 获取代理环境变量(base_env)
    electron_cache_dir = ROOT_DIR / ".cache" / "electron"
    electron_builder_cache_dir = ROOT_DIR / ".cache" / "electron-builder"
    electron_cache_dir.mkdir(parents=True, exist_ok=True)
    electron_builder_cache_dir.mkdir(parents=True, exist_ok=True)
    env.setdefault("ELECTRON_MIRROR", ELECTRON_MIRROR)
    env.setdefault("ELECTRON_CACHE", str(electron_cache_dir))
    env.setdefault("ELECTRON_BUILDER_BINARIES_MIRROR", ELECTRON_BUILDER_BINARIES_MIRROR)
    env.setdefault("ELECTRON_BUILDER_CACHE", str(electron_builder_cache_dir))
    return env


def 确保_env_文件() -> bool:
    if CLOUD_ENV_FILE.exists():
        return False
    echo("未找到 apps/cloud/.env，正在从 apps/cloud/.env.example 复制")
    import shutil
    shutil.copyfile(CLOUD_ENV_EXAMPLE_FILE, CLOUD_ENV_FILE)
    return True


def 确保手机端_env_文件() -> bool:
    if PHONE_ENV_FILE.exists() or not PHONE_ENV_EXAMPLE_FILE.exists():
        return False
    echo("未找到 apps/phone/.env，正在从 apps/phone/.env.example 复制")
    import shutil
    shutil.copyfile(PHONE_ENV_EXAMPLE_FILE, PHONE_ENV_FILE)
    return True


def 更新_env_键值(path: Path, key: str, value: str) -> bool:
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    updated = False
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        current_key = raw.split("=", 1)[0].strip()
        if current_key == key:
            lines[idx] = f"{key}={value}"
            updated = True
            break
    if updated:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return updated


def 读取键值文件(path: Path, *, strip_quotes: bool = False) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if strip_quotes and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        data[key] = value
    return data


def 设置_键值文件(path: Path, key: str, value: str) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    normalized = f"{key}={value}"
    updated = False
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        current_key = raw.split("=", 1)[0].strip()
        if current_key != key:
            continue
        if raw == normalized:
            return False
        lines[idx] = normalized
        updated = True
        break
    if not updated:
        lines.append(normalized)
        updated = True
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return updated


def 自动生成认证密钥() -> None:
    env_file = CLOUD_ENV_FILE
    env_map = 读取键值文件(env_file, strip_quotes=True)
    current = env_map.get("AUTH_SECRET_KEY", "")
    if current != "replace-with-a-very-long-random-string":
        return
    new_key = secrets.token_hex(32)
    if 更新_env_键值(env_file, "AUTH_SECRET_KEY", new_key):
        echo("已自动生成认证签名密钥")


def 解析路径_相对项目根目录(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (ROOT_DIR / candidate).resolve()
