from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import keyring

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
WIDGET_TOKEN_SERVICE_NAME = "PersonalSystem.DesktopWidget"
WIDGET_TOKEN_USERNAME = "widget-auth-token"


@dataclass(slots=True)
class WidgetConfig:
    api_base_url: str = DEFAULT_API_BASE_URL
    widget_name: str = "Personal System Widget"


def get_config_file_path() -> Path:
    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        base_dir = Path(appdata)
    else:
        base_dir = Path.home() / ".config"
    return base_dir / "PersonalSystem" / "desktop-widget" / "config.json"


def ensure_config_parent_dir() -> Path:
    config_path = get_config_file_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    return config_path


def load_config() -> WidgetConfig:
    config_path = get_config_file_path()
    if not config_path.exists():
        return WidgetConfig()

    raw_data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        return WidgetConfig()

    api_base_url = str(raw_data.get("api_base_url", DEFAULT_API_BASE_URL)).strip()
    widget_name = str(raw_data.get("widget_name", "Personal System Widget")).strip()
    return WidgetConfig(
        api_base_url=api_base_url or DEFAULT_API_BASE_URL,
        widget_name=widget_name or "Personal System Widget",
    )


def save_config(config: WidgetConfig) -> Path:
    config_path = ensure_config_parent_dir()
    config_path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return config_path


def load_auth_token() -> str:
    token = keyring.get_password(WIDGET_TOKEN_SERVICE_NAME, WIDGET_TOKEN_USERNAME)
    return str(token or "").strip()


def save_auth_token(token: str) -> None:
    normalized = token.strip()
    if not normalized:
        delete_auth_token()
        return
    keyring.set_password(WIDGET_TOKEN_SERVICE_NAME, WIDGET_TOKEN_USERNAME, normalized)


def delete_auth_token() -> None:
    try:
        keyring.delete_password(WIDGET_TOKEN_SERVICE_NAME, WIDGET_TOKEN_USERNAME)
    except keyring.errors.PasswordDeleteError:
        return


def mask_token(token: str) -> str:
    normalized = token.strip()
    if not normalized:
        return "未配置"
    if len(normalized) <= 12:
        return normalized
    return f"{normalized[:8]}...{normalized[-4:]}"
