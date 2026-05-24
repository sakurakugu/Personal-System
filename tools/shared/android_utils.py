"""Android 构建工具：Java / SDK 检测、签名、目标选择。"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

from .config import (
    ANDROID_MIN_JAVA_MAJOR,
    ANDROID_SIGNING_OPTIONAL_KEYS,
    ANDROID_SIGNING_REQUIRED_KEYS,
    PHONE_ENV_EXAMPLE_FILE,
    PHONE_ENV_FILE,
)
from .dependency_manager import 解析Cap命令
from .env_utils import 读取键值文件, 设置_键值文件, 清理环境变量值, 解析路径_相对项目根目录
from .process_manager import 读取JSON输出, 获取本机局域网IP
from .terminal import echo


def 解析Gradlew命令(android_dir: Path) -> list[str]:
    if os.name == "nt":
        gradlew_path = android_dir / "gradlew.bat"
    else:
        gradlew_path = android_dir / "gradlew"
    if gradlew_path.exists():
        return [str(gradlew_path)]
    raise RuntimeError("未找到命令: gradlew（请先确认 Android 原生工程已初始化）")


def 获取AndroidLocalProperties(android_dir: Path) -> Path:
    return android_dir / "local.properties"


def 是否安卓模拟器(target_id: str) -> bool:
    return target_id.startswith("emulator-")


# ---------------------------------------------------------------------------
# Java 检测
# ---------------------------------------------------------------------------

def 解析JavaMajor版本(version: str) -> Optional[int]:
    raw = version.strip().strip('"')
    if not raw:
        return None
    parts = raw.split(".")
    if not parts or not parts[0].isdigit():
        return None
    major = int(parts[0])
    if major == 1 and len(parts) > 1 and parts[1].isdigit():
        return int(parts[1])
    return major


def 读取JavaRelease信息(java_home: Path) -> Dict[str, str]:
    release_file = java_home / "release"
    if not release_file.exists():
        return {}
    return 读取键值文件(release_file)


def 获取JavaMajor版本(java_home: Path) -> Optional[int]:
    release_info = 读取JavaRelease信息(java_home)
    version = release_info.get("JAVA_VERSION")
    if not version:
        return None
    return 解析JavaMajor版本(version)


def 获取Java环境变量候选目录() -> list[Path]:
    candidates: list[tuple[int, str, Path]] = []
    ignored_keys = {
        "_JAVA_OPTIONS", "JAVA_TOOL_OPTIONS", "JAVA_OPTS", "GRADLE_OPTS",
    }
    for raw_key, raw_value in os.environ.items():
        key = raw_key.strip()
        value = raw_value.strip()
        upper_key = key.upper()
        if not value or upper_key in ignored_keys:
            continue
        if "JAVA" not in upper_key and "JDK" not in upper_key:
            continue
        priority = 2
        if "21" in upper_key:
            priority = 0
        elif "JAVA_HOME" in upper_key or "JDK_HOME" in upper_key:
            priority = 1
        candidates.append((priority, upper_key, Path(value).expanduser()))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return [path for _, _, path in candidates]


def 获取Java候选目录() -> list[Path]:
    from .dependency_manager import 去重路径列表
    candidates: list[Path] = []
    java_home = os.environ.get("JAVA_HOME", "").strip()
    if java_home:
        candidates.append(Path(java_home).expanduser())
    candidates.extend(获取Java环境变量候选目录())
    home_dir = Path.home()
    candidates.extend([
        Path("C:/Software/Deps/Java/jdk-21"),
        Path("C:/Program Files/Android/Android Studio/jbr"),
        home_dir / "AppData" / "Local" / "Programs" / "Android Studio" / "jbr",
    ])
    java_deps_dir = Path("C:/Software/Deps/Java")
    if java_deps_dir.exists():
        candidates.extend(sorted(java_deps_dir.glob("jdk*")))
    return 去重路径列表(candidates)


def 是否有效Java目录(java_home: Path) -> bool:
    return java_home.exists() and (java_home / "bin" / ("java.exe" if os.name == "nt" else "java")).exists()


def 获取AndroidJava目录() -> Path:
    env_java_home = os.environ.get("JAVA_HOME", "").strip()
    if env_java_home:
        env_candidate = Path(env_java_home).expanduser()
        if 是否有效Java目录(env_candidate):
            env_major = 获取JavaMajor版本(env_candidate)
            if env_major is not None and env_major >= ANDROID_MIN_JAVA_MAJOR:
                return env_candidate.resolve()

    exact_match: Optional[Path] = None
    compatible_matches: list[tuple[int, Path]] = []

    for candidate in 获取Java候选目录():
        if not 是否有效Java目录(candidate):
            continue
        major = 获取JavaMajor版本(candidate)
        if major is None or major < ANDROID_MIN_JAVA_MAJOR:
            continue
        resolved = candidate.resolve()
        if major == ANDROID_MIN_JAVA_MAJOR and exact_match is None:
            exact_match = resolved
            continue
        compatible_matches.append((major, resolved))

    if exact_match is not None:
        return exact_match

    if compatible_matches:
        compatible_matches.sort(key=lambda item: item[0])
        return compatible_matches[0][1]

    tried = "\n".join(f"- {candidate}" for candidate in 获取Java候选目录())
    raise RuntimeError(
        f"未找到可用于 Android 构建的 Java {ANDROID_MIN_JAVA_MAJOR}+。\n"
        "请先安装 JDK 21 或更高版本，或手动设置 JAVA_HOME。\n"
        f"已检查路径:\n{tried}"
    )


def 确保AndroidJava配置(env: Dict[str, str]) -> Path:
    java_home = 获取AndroidJava目录()
    env["JAVA_HOME"] = str(java_home)
    java_bin = java_home / "bin"
    current_path = env.get("PATH", "")
    env["PATH"] = f"{java_bin}{os.pathsep}{current_path}" if current_path else str(java_bin)
    return java_home


# ---------------------------------------------------------------------------
# Android SDK 检测
# ---------------------------------------------------------------------------

def 反转义Properties路径(value: str) -> str:
    return value.replace("\\:", ":").replace("\\\\", "\\")


def 标准化Properties路径(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def 是有效AndroidSDK目录(path: Path) -> bool:
    return path.exists() and path.is_dir() and ((path / "platform-tools").exists() or (path / "platforms").exists())


def 获取AndroidSDK候选路径(android_dir: Path) -> list[Path]:
    from .dependency_manager import 去重路径列表
    candidates: list[Path] = []
    local_props = 读取键值文件(获取AndroidLocalProperties(android_dir))
    local_sdk = local_props.get("sdk.dir")
    if local_sdk:
        candidates.append(Path(反转义Properties路径(local_sdk)).expanduser())

    for env_key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        raw_value = os.environ.get(env_key, "").strip()
        if raw_value:
            candidates.append(Path(raw_value).expanduser())

    home_dir = Path.home()
    candidates.extend([
        home_dir / "AppData" / "Local" / "Android" / "Sdk",
        home_dir / "Android" / "Sdk",
        Path("C:/Android/Sdk"),
    ])
    return 去重路径列表(candidates)


def 获取AndroidSDK目录(android_dir: Path) -> Path:
    for candidate in 获取AndroidSDK候选路径(android_dir):
        if 是有效AndroidSDK目录(candidate):
            return candidate.resolve()

    tried = "\n".join(f"- {candidate}" for candidate in 获取AndroidSDK候选路径(android_dir))
    raise RuntimeError(
        "未找到可用的 Android SDK。\n"
        "请先安装 Android Studio / Android SDK，或手动设置 ANDROID_HOME / ANDROID_SDK_ROOT。\n"
        f"已检查路径:\n{tried}"
    )


def 确保AndroidSDK配置(env: Dict[str, str], android_dir: Path) -> Path:
    sdk_dir = 获取AndroidSDK目录(android_dir)
    env["ANDROID_HOME"] = str(sdk_dir)
    env["ANDROID_SDK_ROOT"] = str(sdk_dir)

    local_properties = 获取AndroidLocalProperties(android_dir)
    local_properties.parent.mkdir(parents=True, exist_ok=True)
    changed = 设置_键值文件(local_properties, "sdk.dir", 标准化Properties路径(sdk_dir))
    if changed:
        echo(f"已自动配置 Android SDK: {sdk_dir}")

    return sdk_dir


# ---------------------------------------------------------------------------
# 目标选择
# ---------------------------------------------------------------------------

def 获取安卓目标列表(app_dir: Path, env: Optional[Dict[str, str]] = None) -> list[dict]:
    cap_cmd = 解析Cap命令(app_dir)
    result = subprocess.run(
        [*cap_cmd, "run", "android", "--list", "--json"],
        check=True,
        cwd=app_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    targets = 读取JSON输出(result.stdout)
    if not isinstance(targets, list):
        raise RuntimeError("Android 目标列表格式错误")
    return [item for item in targets if isinstance(item, dict)]


def 选择安卓目标(app_dir: Path, target_id: Optional[str], *, env: Optional[Dict[str, str]] = None) -> dict:
    targets = 获取安卓目标列表(app_dir, env=env)
    if not targets:
        raise RuntimeError("未检测到可用的 Android 设备或模拟器")

    if target_id:
        for item in targets:
            if str(item.get("id", "")) == target_id:
                return item
        raise RuntimeError(f"未找到指定的 Android 目标: {target_id}")

    simulators = [item for item in targets if 是否安卓模拟器(str(item.get("id", "")))]
    if simulators:
        return simulators[0]
    return targets[0]


def 解析手机端访问主机(*, target: dict, phone_host: Optional[str]) -> str:
    if phone_host:
        return phone_host
    target_id = str(target.get("id", ""))
    if 是否安卓模拟器(target_id):
        return "10.0.2.2"
    return 获取本机局域网IP()


# ---------------------------------------------------------------------------
# 签名配置
# ---------------------------------------------------------------------------

def 合并Android签名配置(env: Dict[str, str]) -> bool:
    env_map: Dict[str, str] = {}
    if PHONE_ENV_FILE.exists():
        env_map = 读取键值文件(PHONE_ENV_FILE, strip_quotes=True)
    elif PHONE_ENV_EXAMPLE_FILE.exists():
        env_map = 读取键值文件(PHONE_ENV_EXAMPLE_FILE, strip_quotes=True)
    signing_values: Dict[str, str] = {}

    for key in (*ANDROID_SIGNING_REQUIRED_KEYS, *ANDROID_SIGNING_OPTIONAL_KEYS):
        raw_value = 清理环境变量值(env.get(key, "")) or 清理环境变量值(env_map.get(key, ""))
        if raw_value:
            signing_values[key] = raw_value

    present_required = [key for key in ANDROID_SIGNING_REQUIRED_KEYS if signing_values.get(key)]
    if not present_required:
        return False

    missing_required = [key for key in ANDROID_SIGNING_REQUIRED_KEYS if not signing_values.get(key)]
    if missing_required:
        missing_text = "、".join(missing_required)
        raise RuntimeError(f"Android Release 签名配置不完整，缺少: {missing_text}")

    store_file = 解析路径_相对项目根目录(signing_values["ANDROID_SIGNING_STORE_FILE"])
    if not store_file.exists():
        raise RuntimeError(f"未找到 Android 签名文件: {store_file}")

    env["ANDROID_SIGNING_STORE_FILE"] = str(store_file)
    env["ANDROID_SIGNING_STORE_PASSWORD"] = signing_values["ANDROID_SIGNING_STORE_PASSWORD"]
    env["ANDROID_SIGNING_KEY_ALIAS"] = signing_values["ANDROID_SIGNING_KEY_ALIAS"]
    env["ANDROID_SIGNING_KEY_PASSWORD"] = signing_values["ANDROID_SIGNING_KEY_PASSWORD"]

    store_type = signing_values.get("ANDROID_SIGNING_STORE_TYPE", "").strip()
    if store_type:
        env["ANDROID_SIGNING_STORE_TYPE"] = store_type

    return True
