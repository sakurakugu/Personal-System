"""项目路径与常量。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLOUD_DIR = ROOT_DIR / "apps" / "cloud"
BACKEND_DIR = CLOUD_DIR / "backend"
FRONTEND_DIR = CLOUD_DIR / "frontend"
PHONE_DIR = ROOT_DIR / "apps" / "phone"
PHONE_ENV_FILE = PHONE_DIR / ".env"
PHONE_ENV_EXAMPLE_FILE = PHONE_DIR / ".env.example"
DESKTOP_DIR = ROOT_DIR / "apps" / "desktop"
DESKTOP_PYTHON_RUNTIME_DIR = DESKTOP_DIR / "python-runtime"
COMPOSE_FILE = CLOUD_DIR / "docker-compose.yml"
CLOUD_ENV_FILE = CLOUD_DIR / ".env"
CLOUD_ENV_EXAMPLE_FILE = CLOUD_DIR / ".env.example"
STATE_DIR = ROOT_DIR / ".cache" / ".dev"
STATE_HISTORY_DIR = STATE_DIR / "history"
STATE_FILE = STATE_DIR / "config.json"
BACKEND_LOG = STATE_DIR / "backend.log"
FRONTEND_LOG = STATE_DIR / "frontend.log"
PHONE_LOG = STATE_DIR / "phone.log"
DESKTOP_LOG = STATE_DIR / "desktop.log"
FRONTEND_DEV_PORT = 5173
PHONE_DEV_PORT = 5174
DESKTOP_DEV_PORT = 5175
ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"
ANDROID_MIN_JAVA_MAJOR = 21
ANDROID_SIGNING_REQUIRED_KEYS = (
    "ANDROID_SIGNING_STORE_FILE",
    "ANDROID_SIGNING_STORE_PASSWORD",
    "ANDROID_SIGNING_KEY_ALIAS",
    "ANDROID_SIGNING_KEY_PASSWORD",
)
ANDROID_SIGNING_OPTIONAL_KEYS = (
    "ANDROID_SIGNING_STORE_TYPE",
)
DEFAULT_ANDROID_ARCHITECTURES = ("armeabi-v7a", "arm64-v8a", "x86", "x86_64")
APK_ARCH_CONFIG = {
    "all": {"label": "全部", "architectures": DEFAULT_ANDROID_ARCHITECTURES, "suffix": "all"},
    "x86-all": {"label": "x86全部", "architectures": ("x86", "x86_64"), "suffix": "x86-all"},
    "arm64-all": {"label": "arm64全部", "architectures": ("arm64-v8a", "armeabi-v7a"), "suffix": "arm64-all"},
    "x86": {"label": "x86", "architectures": ("x86",), "suffix": "x86"},
    "x86_64": {"label": "x86_64", "architectures": ("x86_64",), "suffix": "x86_64"},
    "arm-v8a": {"label": "arm-v8a", "architectures": ("arm64-v8a",), "suffix": "arm-v8a"},
    "arm-v7a": {"label": "arm-v7a", "architectures": ("armeabi-v7a",), "suffix": "arm-v7a"},
}
APK_FULL_BUILD_ORDER = [
    "all", "x86-all", "arm64-all", "x86", "x86_64", "arm-v8a", "arm-v7a",
]
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
