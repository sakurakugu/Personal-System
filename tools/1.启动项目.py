"""跨平台本地开发启动器。

start:       docker 依赖 + 后端/前端热重载
stop:        停止后端/前端 + docker 依赖
restart:     停止后启动
status:      显示进程和 docker 状态
db-upgrade:  更新数据库到最新迁移
--phone:     单独启动 apps/phone 的 Android 手机端热更新
--apk:       构建 apps/phone 的 Android 安装包
--help:      查看所有命令
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
CLOUD_DIR = ROOT_DIR / "apps" / "cloud"
BACKEND_DIR = CLOUD_DIR / "backend"
FRONTEND_DIR = CLOUD_DIR / "frontend"
PHONE_DIR = ROOT_DIR / "apps" / "phone"
COMPOSE_FILE = CLOUD_DIR / "docker-compose.yml"
CLOUD_ENV_FILE = CLOUD_DIR / ".env"
CLOUD_ENV_EXAMPLE_FILE = CLOUD_DIR / ".env.example"
SCRIPT_NAME = Path(__file__).name
STATE_DIR = ROOT_DIR / ".cache" / ".dev"
STATE_FILE = STATE_DIR / "config.json"
BACKEND_LOG = STATE_DIR / "backend.log"
FRONTEND_LOG = STATE_DIR / "frontend.log"
PHONE_LOG = STATE_DIR / "phone.log"
FRONTEND_DEV_PORT = 5173
PHONE_DEV_PORT = 5174
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
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"


def echo(msg: str) -> None:
    print(f"==> {msg}")


def 支持彩色输出() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def 格式化状态符号(symbol: str, color: str) -> str:
    if not 支持彩色输出():
        return symbol
    return f"{color}\033[1m{symbol}{ANSI_RESET}"


def 格式化状态行(symbol: str, msg: str, *, color: str, 宽度: int, 结果: str = "") -> str:
    主体 = msg.ljust(宽度)
    if 结果:
        主体 = f"{主体} {结果}"
    return f" {格式化状态符号(symbol, color)} {主体}"


def 开始单行状态(msg: str, *, 宽度: int) -> None:
    line = 格式化状态行("-", msg, color=ANSI_YELLOW, 宽度=宽度)
    if sys.stdout.isatty():
        print(line, end="\r", flush=True)
        return
    print(line)


def 结束单行状态(msg: str, *, 宽度: int, 结果: str, 成功: bool = True) -> None:
    symbol = "✓" if 成功 else "x"
    color = ANSI_GREEN if 成功 else ANSI_RED
    line = 格式化状态行(symbol, msg, color=color, 宽度=宽度, 结果=结果)
    if sys.stdout.isatty():
        print(f"\r\033[2K{line}", flush=True)
        return
    print(line)


def 查找命令(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"未找到命令: {name}")


def 确保_git_hooks_已启用() -> None:
    """检查并启用 git hooks。"""
    # 检查 .githooks 目录是否存在
    githooks_dir = ROOT_DIR / ".githooks"
    if not githooks_dir.exists():
        return

    # 获取当前 hooks 路径
    result = subprocess.run(
        ["git", "config", "core.hooksPath"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    current_path = result.stdout.strip() if result.returncode == 0 else ""

    # 如果已经设置为 .githooks，则跳过
    if current_path == ".githooks":
        return

    echo("启用 git hooks")
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        check=True,
        cwd=ROOT_DIR,
    )

    # 非 Windows 系统需要添加执行权限
    if os.name != "nt":
        for hook_file in githooks_dir.iterdir():
            if hook_file.is_file():
                subprocess.run(
                    ["chmod", "+x", str(hook_file)],
                    check=False,
                    cwd=ROOT_DIR,
                )


def 解析_dotenv(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        data[key] = value
    return data


def 确保_env_文件() -> bool:
    if CLOUD_ENV_FILE.exists():
        return False
    echo("未找到 apps/cloud/.env，正在从 apps/cloud/.env.example 复制")
    shutil.copyfile(CLOUD_ENV_EXAMPLE_FILE, CLOUD_ENV_FILE)
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


def 读取_键值文件(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        data[key.strip()] = value.strip()
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
    env_map = 解析_dotenv(env_file)
    current = env_map.get("AUTH_SECRET_KEY", "")
    if current != "replace-with-a-very-long-random-string":
        return
    new_key = secrets.token_hex(32)
    if 更新_env_键值(env_file, "AUTH_SECRET_KEY", new_key):
        echo("已自动生成认证签名密钥")


def 组合_env_参数() -> list[str]:
    env_file = CLOUD_ENV_FILE if CLOUD_ENV_FILE.exists() else CLOUD_ENV_EXAMPLE_FILE
    return ["--env-file", str(env_file)]


def 组合_compose_命令(*args: str) -> list[str]:
    return ["docker", "compose", "--file", str(COMPOSE_FILE), *组合_env_参数(), *args]


def 提取进程_pid(state: dict) -> tuple[int, int]:
    processes = state.get("processes")
    if not isinstance(processes, dict):
        return 0, 0
    backend_pid = int(processes.get("backend", 0))
    frontend_pid = int(processes.get("frontend", 0))
    return backend_pid, frontend_pid


def 提取手机端前端_pid(state: dict) -> int:
    processes = state.get("processes")
    if not isinstance(processes, dict):
        return 0
    return int(processes.get("phone_frontend", 0))


def 存在进程(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def 停止进程(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except KeyboardInterrupt:
            pass
        return

    killpg = getattr(os, "killpg", None)
    if callable(killpg):
        try:
            killpg(pid, signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except Exception:
            pass

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def 清理手机端状态() -> None:
    保存手机端前端状态(0)
    保存手机端状态(None)


def 停止手机端开发进程(*, state: Optional[dict] = None, 显示未找到提示: bool = True) -> None:
    try:
        current_state = state if state is not None else 读取状态()
        if current_state is None:
            if 显示未找到提示:
                print("未找到手机端开发进程记录。")
            清理手机端状态()
            return

        phone_frontend_pid = 提取手机端前端_pid(current_state)
        if phone_frontend_pid > 0:
            if 存在进程(phone_frontend_pid):
                停止进程(phone_frontend_pid)
                print(f"已停止 phone_frontend (PID={phone_frontend_pid})")
            else:
                print(f"phone_frontend 已停止 (PID={phone_frontend_pid})")

        清理手机端状态()
    except KeyboardInterrupt:
        清理手机端状态()


def 停止开发版进程() -> None:
    try:
        state = 读取状态()
        if state is None:
            print("未找到本地开发进程记录。")
            return

        backend_pid, frontend_pid = 提取进程_pid(state)

        for name, pid in (("backend", backend_pid), ("frontend", frontend_pid)):
            if pid <= 0:
                continue
            if 存在进程(pid):
                停止进程(pid)
                print(f"已停止 {name} (PID={pid})")
            else:
                print(f"{name} 已停止 (PID={pid})")

        保存状态(0, 0)
        停止手机端开发进程(state=state, 显示未找到提示=False)
    except KeyboardInterrupt:
        pass


def 后端_python_路径(use_venv: bool) -> Path:
    if use_venv:
        if os.name == "nt":
            return BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        else:
            return BACKEND_DIR / ".venv" / "bin" / "python"

    return Path(sys.executable)


def 确保后端环境(use_venv: bool) -> None:
    py = 后端_python_路径(use_venv)
    requirements_txt = BACKEND_DIR / "requirements.txt"

    if use_venv and not py.exists():
        echo("创建后端虚拟环境")
        subprocess.run(
            [sys.executable, "-m", "venv", str(BACKEND_DIR / ".venv")],
            check=True,
        )

    # 检查 requirements.txt 是否存在
    if not requirements_txt.exists():
        raise RuntimeError(f"未找到 requirements.txt: {requirements_txt}")

    # 计算当前 requirements.txt 的哈希
    current_hash = 计算文件哈希(requirements_txt)
    state = 读取状态()
    saved_hash = state.get("hash", {}).get("backend_requirements") if state else None

    # 如果依赖未变化，跳过安装
    if saved_hash == current_hash:
        return

    if saved_hash is None:
        echo("首次安装后端依赖")
    else:
        echo("检测到 requirements.txt 变化，重新安装后端依赖")

    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        check=True,
        cwd=BACKEND_DIR,
    )

    # 保存新的哈希值到状态文件
    state = 读取状态() or {}
    state["hash"] = state.get("hash", {})
    state["hash"]["backend_requirements"] = current_hash
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    echo("后端依赖安装完成")


def 计算文件哈希(path: Path) -> str:
    import hashlib
    content = path.read_bytes()
    return hashlib.md5(content).hexdigest()


def 读取状态() -> Optional[dict]:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except KeyboardInterrupt:
        return None


def 保存状态(backend_pid: int, frontend_pid: int, package_hash: Optional[str] = None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = 读取状态() or {}
    processes = state.get("processes")
    if not isinstance(processes, dict):
        processes = {}
    processes["backend"] = backend_pid
    processes["frontend"] = frontend_pid
    state["processes"] = processes
    if package_hash is not None:
        state["hash"] = state.get("hash", {})
        state["hash"]["frontend_package"] = package_hash
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def 保存手机端前端状态(phone_frontend_pid: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = 读取状态() or {}
    processes = state.get("processes")
    if not isinstance(processes, dict):
        processes = {}
    processes["phone_frontend"] = phone_frontend_pid
    state["processes"] = processes
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def 保存手机端状态(mobile: Optional[dict]) -> None:
    state = 读取状态()
    if state is None and mobile is None:
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = state or {}
    if mobile is None:
        state.pop("mobile", None)
    else:
        state["mobile"] = mobile
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

def 确保_node_应用依赖(app_dir: Path, *, hash_key: str, label: str) -> None:
    node_modules = app_dir / "node_modules"
    package_json = app_dir / "package.json"
    
    # 检查 package.json 是否存在
    if not package_json.exists():
        raise RuntimeError(f"未找到 package.json: {package_json}")
    
    # 计算当前 package.json 的哈希
    current_hash = 计算文件哈希(package_json)
    state = 读取状态()
    saved_hash = state.get("hash", {}).get(hash_key) if state else None
    
    # 如果 node_modules 存在且 package.json 未变化，跳过安装
    if node_modules.exists() and saved_hash == current_hash:
        return
    
    if not node_modules.exists():
        echo(f"首次安装{label}依赖")
    elif saved_hash != current_hash:
        echo(f"检测到 {label} package.json 变化，重新安装依赖")
    
    npm_cmd = 解析_npm_命令()
    subprocess.run([*npm_cmd, "install"], check=True, cwd=app_dir)
    
    # 保存新的哈希值到状态文件
    state = 读取状态() or {}
    state["hash"] = state.get("hash", {})
    state["hash"][hash_key] = current_hash
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    echo(f"{label}依赖安装完成")


def 确保前端依赖() -> None:
    确保_node_应用依赖(FRONTEND_DIR, hash_key="frontend_package", label="前端")


def 确保手机端依赖() -> None:
    确保_node_应用依赖(PHONE_DIR, hash_key="phone_package", label="手机端")


def 解析_npm_命令() -> list[str]:
    if os.name == "nt":
        for name in ("npm.cmd", "npm.exe", "npm"):
            path = shutil.which(name)
            if path:
                return [path]
        raise RuntimeError("未找到命令: npm（请确认 Node.js 安装目录已加入 PATH）")
    查找命令("npm")
    return ["npm"]


def 解析_cap_命令(app_dir: Path) -> list[str]:
    if os.name == "nt":
        cap_path = app_dir / "node_modules" / ".bin" / "cap.cmd"
    else:
        cap_path = app_dir / "node_modules" / ".bin" / "cap"
    if cap_path.exists():
        return [str(cap_path)]
    raise RuntimeError("未找到命令: cap（请先执行前端依赖安装）")


def 解析_gradlew_命令(android_dir: Path) -> list[str]:
    if os.name == "nt":
        gradlew_path = android_dir / "gradlew.bat"
    else:
        gradlew_path = android_dir / "gradlew"
    if gradlew_path.exists():
        return [str(gradlew_path)]
    raise RuntimeError("未找到命令: gradlew（请先确认 Android 原生工程已初始化）")


def 获取_android_local_properties(android_dir: Path) -> Path:
    return android_dir / "local.properties"


def 是否安卓模拟器(target_id: str) -> bool:
    return target_id.startswith("emulator-")


def 解析_java_major_版本(version: str) -> Optional[int]:
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


def 读取_java_release_信息(java_home: Path) -> Dict[str, str]:
    release_file = java_home / "release"
    if not release_file.exists():
        return {}
    return 读取_键值文件(release_file)


def 获取_java_major_版本(java_home: Path) -> Optional[int]:
    release_info = 读取_java_release_信息(java_home)
    version = release_info.get("JAVA_VERSION")
    if not version:
        return None
    return 解析_java_major_版本(version)


def 获取_java_环境变量候选目录() -> list[Path]:
    candidates: list[tuple[int, str, Path]] = []
    ignored_keys = {
        "_JAVA_OPTIONS",
        "JAVA_TOOL_OPTIONS",
        "JAVA_OPTS",
        "GRADLE_OPTS",
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


def 获取_java_候选目录() -> list[Path]:
    candidates: list[Path] = []

    java_home = os.environ.get("JAVA_HOME", "").strip()
    if java_home:
        candidates.append(Path(java_home).expanduser())

    candidates.extend(获取_java_环境变量候选目录())

    home_dir = Path.home()
    candidates.extend([
        Path("C:/Software/Deps/Java/jdk-21"),
        Path("C:/Program Files/Android/Android Studio/jbr"),
        home_dir / "AppData" / "Local" / "Programs" / "Android Studio" / "jbr",
    ])

    java_deps_dir = Path("C:/Software/Deps/Java")
    if java_deps_dir.exists():
        candidates.extend(sorted(java_deps_dir.glob("jdk*")))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(candidate)
    return unique


def 是否有效_java_目录(java_home: Path) -> bool:
    return java_home.exists() and (java_home / "bin" / ("java.exe" if os.name == "nt" else "java")).exists()


def 获取_android_java_目录() -> Path:
    env_java_home = os.environ.get("JAVA_HOME", "").strip()
    if env_java_home:
        env_candidate = Path(env_java_home).expanduser()
        if 是否有效_java_目录(env_candidate):
            env_major = 获取_java_major_版本(env_candidate)
            if env_major is not None and env_major >= ANDROID_MIN_JAVA_MAJOR:
                return env_candidate.resolve()

    exact_match: Optional[Path] = None
    compatible_matches: list[tuple[int, Path]] = []

    for candidate in 获取_java_候选目录():
        if not 是否有效_java_目录(candidate):
            continue
        major = 获取_java_major_版本(candidate)
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

    tried = "\n".join(f"- {candidate}" for candidate in 获取_java_候选目录())
    raise RuntimeError(
        f"未找到可用于 Android 构建的 Java {ANDROID_MIN_JAVA_MAJOR}+。\n"
        "请先安装 JDK 21 或更高版本，或手动设置 JAVA_HOME。\n"
        f"已检查路径:\n{tried}"
    )


def 确保_android_java_配置(env: Dict[str, str]) -> Path:
    java_home = 获取_android_java_目录()
    env["JAVA_HOME"] = str(java_home)
    java_bin = java_home / "bin"
    current_path = env.get("PATH", "")
    env["PATH"] = f"{java_bin}{os.pathsep}{current_path}" if current_path else str(java_bin)
    return java_home


def 反转义_properties_路径(value: str) -> str:
    return value.replace("\\:", ":").replace("\\\\", "\\")


def 标准化_properties_路径(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def 是有效_android_sdk_目录(path: Path) -> bool:
    return path.exists() and path.is_dir() and ((path / "platform-tools").exists() or (path / "platforms").exists())


def 获取_android_sdk_候选路径(android_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    local_props = 读取_键值文件(获取_android_local_properties(android_dir))
    local_sdk = local_props.get("sdk.dir")
    if local_sdk:
        candidates.append(Path(反转义_properties_路径(local_sdk)).expanduser())

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

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(candidate)
    return unique


def 获取_android_sdk_目录(android_dir: Path) -> Path:
    for candidate in 获取_android_sdk_候选路径(android_dir):
        if 是有效_android_sdk_目录(candidate):
            return candidate.resolve()

    tried = "\n".join(f"- {candidate}" for candidate in 获取_android_sdk_候选路径(android_dir))
    raise RuntimeError(
        "未找到可用的 Android SDK。\n"
        "请先安装 Android Studio / Android SDK，或手动设置 ANDROID_HOME / ANDROID_SDK_ROOT。\n"
        f"已检查路径:\n{tried}"
    )


def 确保_android_sdk_配置(env: Dict[str, str], android_dir: Path) -> Path:
    sdk_dir = 获取_android_sdk_目录(android_dir)
    env["ANDROID_HOME"] = str(sdk_dir)
    env["ANDROID_SDK_ROOT"] = str(sdk_dir)

    local_properties = 获取_android_local_properties(android_dir)
    local_properties.parent.mkdir(parents=True, exist_ok=True)
    changed = 设置_键值文件(local_properties, "sdk.dir", 标准化_properties_路径(sdk_dir))
    if changed:
        echo(f"已自动配置 Android SDK: {sdk_dir}")

    return sdk_dir


def 获取本机局域网_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass

    hostname = socket.gethostname()
    try:
        for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, socket.AF_INET):
            raw_ip = sockaddr[0]
            if isinstance(raw_ip, str) and raw_ip and not raw_ip.startswith("127."):
                return raw_ip
    except OSError as exc:
        raise RuntimeError("无法自动探测本机局域网 IP，请使用 --host 手动指定") from exc

    raise RuntimeError("无法自动探测本机局域网 IP，请使用 --host 手动指定")


def 等待_http_服务(url: str, timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    raise RuntimeError(f"等待服务超时: {url}")


def 检查_http_服务(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, TimeoutError):
        return False


def 读取_json_输出(stdout: str) -> list[dict]:
    content = stdout.strip()
    if not content:
        return []
    return json.loads(content)


def 获取安卓目标列表(app_dir: Path, env: Optional[Dict[str, str]] = None) -> list[dict]:
    cap_cmd = 解析_cap_命令(app_dir)
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
    targets = 读取_json_输出(result.stdout)
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

    return 获取本机局域网_ip()


def 启动安卓手机端(*, app_dir: Path, phone_target: Optional[str], phone_host: Optional[str], phone_port: int) -> dict:
    android_dir = app_dir / "android"
    if not android_dir.exists():
        raise RuntimeError("未找到 Android 原生工程，请先确认 Capacitor Android 已初始化")

    等待_http_服务(f"http://127.0.0.1:{phone_port}", timeout=60)

    cap_cmd = 解析_cap_命令(app_dir)
    env = os.environ.copy()
    sdk_dir = 确保_android_sdk_配置(env, android_dir)
    java_home = 确保_android_java_配置(env)

    target = 选择安卓目标(app_dir, phone_target, env=env)
    is_emulator = 是否安卓模拟器(str(target.get("id", "")))
    requested_host = 解析手机端访问主机(target=target, phone_host=phone_host)
    live_reload_host = requested_host
    forward_ports_args: list[str] = []

    if not is_emulator and not phone_host:
        live_reload_host = "localhost"
        forward_ports_args = ["--forwardPorts", f"{phone_port}:{phone_port}"]

    server_url = f"http://{live_reload_host}:{phone_port}"

    echo(
        "正在启动 Android 手机端"
        f"（目标: {target.get('name', '未知目标')} / {target.get('id', '未知 ID')}，"
        f"开发服务器: {server_url}，SDK: {sdk_dir}，JAVA: {java_home}）"
    )
    if forward_ports_args:
        echo(f"已为真机启用 adb reverse 端口转发: {phone_port}:{phone_port}")

    mobile_info = {
        "target_id": str(target.get("id", "")),
        "target_name": str(target.get("name", "未知目标")),
        "server_url": server_url,
    }

    subprocess.run(
        [
            *cap_cmd,
            "run",
            "android",
            "--target",
            str(target.get("id", "")),
            "--live-reload",
            "--host",
            live_reload_host,
            "--port",
            str(phone_port),
            *forward_ports_args,
        ],
        check=True,
        cwd=app_dir,
        env=env,
    )

    保存手机端状态(mobile_info)
    echo(f"Android 手机端已接入前端热更新: {server_url}")
    return mobile_info


def 确保手机端开发服务已启动(phone_port: int) -> int:
    service_url = f"http://127.0.0.1:{phone_port}"
    if 检查_http_服务(service_url):
        return 0

    npm_cmd = 解析_npm_命令()
    echo(f"未检测到手机端开发服务，正在启动 apps/phone（端口 {phone_port}）")
    phone_cmd = [*npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", str(phone_port), "--strictPort"]
    phone_proc = 启动并转发日志(phone_cmd, PHONE_DIR, PHONE_LOG, force_color=True)

    try:
        等待_http_服务(service_url, timeout=60)
    except Exception as exc:
        停止进程(phone_proc.pid)
        raise RuntimeError(f"手机端开发服务启动失败，请检查日志: {PHONE_LOG}") from exc

    保存手机端前端状态(phone_proc.pid)
    echo(f"手机端开发服务已启动: {service_url}")
    return phone_proc.pid


def 获取_android_apk_输出目录(build_variant: str) -> Path:
    return PHONE_DIR / "android" / "app" / "build" / "outputs" / "apk" / build_variant


def 查找最新_android_apk(build_variant: str) -> Path:
    output_dir = 获取_android_apk_输出目录(build_variant)
    candidates = [path for path in output_dir.glob("*.apk") if path.is_file()]
    if not candidates:
        raise RuntimeError(f"未找到 {build_variant} 构建产物，请检查 Gradle 输出目录: {output_dir}")
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0]


def 打开文件资源管理器(path: Path) -> None:
    target = path.resolve()
    if os.name == "nt":
        arg = f"/select,{target}" if target.is_file() else str(target)
        subprocess.Popen(["explorer.exe", arg])
        return

    opener = shutil.which("open") or shutil.which("xdg-open")
    if opener:
        subprocess.Popen([opener, str(target.parent if target.is_file() else target)])


def 解析路径_相对项目根目录(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (ROOT_DIR / candidate).resolve()


def 合并_android_签名配置(env: Dict[str, str]) -> bool:
    env_map = 解析_dotenv(CLOUD_ENV_FILE)
    signing_values: Dict[str, str] = {}

    for key in (*ANDROID_SIGNING_REQUIRED_KEYS, *ANDROID_SIGNING_OPTIONAL_KEYS):
        raw_value = env.get(key, "").strip() or env_map.get(key, "").strip()
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


def 构建安卓安装包(*, build_variant: str) -> Path:
    if build_variant not in {"debug", "release"}:
        raise RuntimeError(f"不支持的 Android 构建类型: {build_variant}")

    android_dir = PHONE_DIR / "android"
    if not android_dir.exists():
        raise RuntimeError("未找到 apps/phone/android 原生工程，请先在 apps/phone 初始化 Capacitor Android")

    确保手机端依赖()

    npm_cmd = 解析_npm_命令()
    cap_cmd = 解析_cap_命令(PHONE_DIR)
    gradlew_cmd = 解析_gradlew_命令(android_dir)
    env = os.environ.copy()
    sdk_dir = 确保_android_sdk_配置(env, android_dir)
    java_home = 确保_android_java_配置(env)
    env["VITE_ENABLE_DEVELOPER_LOGIN"] = "true" if build_variant == "debug" else "false"
    env["VITE_ENABLE_API_ENV_SWITCH"] = "true" if build_variant == "debug" else "false"
    has_release_signing = 合并_android_签名配置(env) if build_variant == "release" else False

    variant_label = "Debug" if build_variant == "debug" else "Release"
    gradle_task = f"assemble{variant_label}"

    echo(f"正在构建手机端静态资源（Android {variant_label}）")
    subprocess.run([*npm_cmd, "run", "build"], check=True, cwd=PHONE_DIR, env=env)

    if build_variant == "release":
        sign_text = "已签名" if has_release_signing else "未签名"
        echo(f"正在同步 Android 原生工程（SDK: {sdk_dir}，JAVA: {java_home}，Release: {sign_text}）")
    else:
        echo(f"正在同步 Android 原生工程（SDK: {sdk_dir}，JAVA: {java_home}）")
    subprocess.run([*cap_cmd, "sync", "android"], check=True, cwd=PHONE_DIR, env=env)

    echo(f"正在执行 Android 安装包构建: {gradle_task}")
    subprocess.run([*gradlew_cmd, gradle_task], check=True, cwd=android_dir, env=env)

    apk_path = 查找最新_android_apk(build_variant)
    echo(f"Android 安装包构建成功: {apk_path}")
    打开文件资源管理器(apk_path)
    return apk_path

def 启动_docker_desktop() -> None:
    if os.name != "nt":
        return

    docker_paths = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
    ]

    for path in docker_paths:
        if Path(path).exists():
            echo("Docker 未运行，正在启动 Docker Desktop")
            subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

    raise RuntimeError("未找到 Docker Desktop，请手动启动 Docker。")

def docker_是否运行() -> bool:
    """检查 Docker 是否在运行"""
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def 检查_docker_运行() -> None:
    if docker_是否运行():
        return

    启动_docker_desktop()

    echo("等待 Docker 启动...")

    for _ in range(30):
        if docker_是否运行():
            echo("Docker 已启动")
            return

        import time
        time.sleep(2)

    raise RuntimeError("Docker 启动超时，请手动检查 Docker Desktop。")

def 等待_docker_compose_服务就绪(service: str, timeout: int = 60) -> None:
    """等待 docker compose 服务对应容器进入可用状态。"""
    deadline = time.monotonic() + timeout
    last_status = "unknown"

    while time.monotonic() < deadline:
        result = subprocess.run(
            组合_compose_命令("ps", "-q", service),
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        container_id = result.stdout.strip()
        if not container_id:
            time.sleep(1)
            continue

        inspect = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                container_id,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        status = inspect.stdout.strip()
        if status:
            last_status = status

        if status in {"healthy", "running"}:
            return

        time.sleep(1)

    raise RuntimeError(f"等待服务就绪超时: {service}（最后状态: {last_status}）")

def 镜像存在(image: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def 验证_docker_镜像(images: list[str]) -> None:
    宽度 = max(len(f"检查镜像: {image}") for image in images)
    for image in images:
        msg = f"检查镜像: {image}"
        开始单行状态(msg, 宽度=宽度)
        if 镜像存在(image):
            结束单行状态(msg, 宽度=宽度, 结果="（已存在）")
            continue

        result = subprocess.run(
            ["docker", "pull", image],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            结束单行状态(msg, 宽度=宽度, 结果="（拉取失败）", 成功=False)
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                "无法拉取 Docker 镜像。\n"
                f"镜像: {image}\n"
                f"错误: {stderr}"
            )
        结束单行状态(msg, 宽度=宽度, 结果="（已拉取）")


def 启动并转发日志(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    env_patch: Optional[Dict[str, str]] = None,
    force_color: bool = False,
) -> subprocess.Popen:
    relay_env_patch: Dict[str, str] = {}
    if env_patch:
        relay_env_patch.update(env_patch)
    if force_color:
        relay_env_patch.update(
            {
                "FORCE_COLOR": "1",
                "PY_COLORS": "1",
                "CLICOLOR_FORCE": "1",
                "TERM": "xterm-256color",
            }
        )
        relay_env_patch.pop("NO_COLOR", None)

    relay_cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "__relay__",
        "--relay-cwd",
        str(cwd),
        "--relay-log",
        str(log_path),
        "--relay-cmd-json",
        json.dumps(cmd, ensure_ascii=False),
    ]
    if relay_env_patch:
        relay_cmd.extend(["--relay-env-json", json.dumps(relay_env_patch, ensure_ascii=False)])

    if os.name == "nt":
        return subprocess.Popen(
            relay_cmd,
            cwd=ROOT_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

    setsid = getattr(os, "setsid", None)
    return subprocess.Popen(
        relay_cmd,
        cwd=ROOT_DIR,
        preexec_fn=setsid if callable(setsid) else None,
    )


def 运行日志转发模式(args: argparse.Namespace) -> int:
    if not args.relay_cwd or not args.relay_log or not args.relay_cmd_json:
        raise RuntimeError("日志转发模式参数不完整")

    cmd = json.loads(args.relay_cmd_json)
    if not isinstance(cmd, list) or not all(isinstance(item, str) for item in cmd):
        raise RuntimeError("日志转发命令格式错误")

    env = os.environ.copy()
    if args.relay_env_json:
        env_patch = json.loads(args.relay_env_json)
        if not isinstance(env_patch, dict):
            raise RuntimeError("日志转发环境变量格式错误")
        env.update({str(k): str(v) for k, v in env_patch.items()})

    process = subprocess.Popen(
        cmd,
        cwd=args.relay_cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    assert process.stdout is not None
    Path(args.relay_log).parent.mkdir(parents=True, exist_ok=True)
    with open(args.relay_log, "a", encoding="utf-8") as log_fp:
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log_fp.write(ANSI_ESCAPE_RE.sub("", line))
            log_fp.flush()

    return process.wait()

def 启动开发版(use_venv: bool) -> None:
    os.chdir(ROOT_DIR)
    查找命令("git")
    查找命令("docker")
    查找命令(sys.executable)
    npm_cmd = 解析_npm_命令()

    确保_git_hooks_已启用()

    echo("检查 Docker 状态")
    检查_docker_运行()

    确保_env_文件()

    env_map = 解析_dotenv(CLOUD_ENV_FILE)
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    minio_key = env_map.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = env_map.get("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket = env_map.get("MINIO_BUCKET", "blog-uploads")
    minio_public_url = env_map.get("MINIO_PUBLIC_URL", "http://localhost:8000/files")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@127.0.0.1:15432/{postgres_db}"

    compose_path = COMPOSE_FILE
    验证_docker_compose_镜像(compose_path)

    echo("开始安装 docker 依赖: postgres redis minio twikoo")
    subprocess.run(组合_compose_命令("up", "-d", "postgres", "redis", "minio", "twikoo"), check=True, cwd=ROOT_DIR)

    echo("停止本地开发进程")
    停止开发版进程()

    确保后端环境(use_venv)
    确保前端依赖()
    更新开发数据库(use_venv)

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    backend_env_patch = {
        "APP_ENV": "development",
        "APP_DEBUG": "true",
        "DATABASE_URL": database_url,
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "MINIO_ENDPOINT": "127.0.0.1:9000",
        "MINIO_ACCESS_KEY": minio_key,
        "MINIO_SECRET_KEY": minio_secret,
        "MINIO_BUCKET": minio_bucket,
        "MINIO_USE_SSL": "false",
        "MINIO_PUBLIC_URL": minio_public_url,
        "CORS_ORIGINS": f'["http://localhost:{FRONTEND_DEV_PORT}"]',
    }

    py = 后端_python_路径(use_venv)
    backend_cmd = [
        str(py), "-m", "uvicorn", "app.main:app",
        "--reload",
        "--reload-dir", str(BACKEND_DIR / "app"),
        "--reload-exclude", ".venv",
        "--reload-exclude", ".mypy_cache",
        "--reload-exclude", ".ruff_cache",
        "--reload-exclude", "alembic",
        "--reload-exclude", "*.pyc",
        "--reload-exclude", "__pycache__",
        "--use-colors",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    frontend_cmd = [*npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", str(FRONTEND_DEV_PORT)]

    echo("正在启动后端热重载")
    backend_proc = 启动并转发日志(backend_cmd, BACKEND_DIR, BACKEND_LOG, env_patch=backend_env_patch, force_color=True)
    echo("正在启动前端热重载")
    frontend_proc = 启动并转发日志(frontend_cmd, FRONTEND_DIR, FRONTEND_LOG, force_color=True)

    保存状态(backend_proc.pid, frontend_proc.pid)
    保存手机端状态(None)

    print("")
    print("本地开发环境已启动:")
    print(f"  前端: http://localhost:{FRONTEND_DEV_PORT}/")
    print("  后端:  http://localhost:8000/api/docs")
    print("  Twikoo: http://localhost:8001/")
    print(f"  后端日志:  {BACKEND_LOG}")
    print(f"  前端日志: {FRONTEND_LOG}")
    print("")
    print(f"停止命令: {sys.executable} ./tools/{SCRIPT_NAME} --stop")
    print("按 Ctrl+C 可停止开发环境并退出。")

    上次中断时间 = 0.0
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            当前时间 = time.monotonic()
            if 当前时间 - 上次中断时间 <= 2:
                print("")
                echo("检测到 Ctrl+C，正在停止开发环境")
                try:
                    停止开发版()
                except KeyboardInterrupt:
                    pass
                break
            上次中断时间 = 当前时间
            print("")
            echo("收到中断信号，再按一次 Ctrl+C 才会停止开发环境")
            continue

        state = 读取状态()
        if state is None:
            break
        backend_pid, frontend_pid = 提取进程_pid(state)
        if not 存在进程(backend_pid) and not 存在进程(frontend_pid):
            break


def 显示开发状态() -> None:
    os.chdir(ROOT_DIR)
    echo("Docker 依赖状态:")
    try:
        subprocess.run(组合_compose_命令("ps", "postgres", "redis", "minio", "twikoo"), check=False, cwd=ROOT_DIR)
    except subprocess.CalledProcessError as e:
        print(f"检查 Docker 依赖状态时出错: {e}")
        return

    state = 读取状态()
    if state is None:
        print("未找到本地开发进程记录。")
        return

    backend_pid, frontend_pid = 提取进程_pid(state)
    phone_frontend_pid = 提取手机端前端_pid(state)
    print(f"后端:  {'正在运行' if 存在进程(backend_pid) else '已停止'} (PID={backend_pid})")
    print(f"前端: {'正在运行' if 存在进程(frontend_pid) else '已停止'} (PID={frontend_pid})")
    if phone_frontend_pid > 0:
        print(f"手机前端: {'正在运行' if 存在进程(phone_frontend_pid) else '已停止'} (PID={phone_frontend_pid})")
    else:
        print("手机前端: 未启动")
    mobile = state.get("mobile")
    if isinstance(mobile, dict):
        target_name = str(mobile.get("target_name", "未知目标"))
        server_url = str(mobile.get("server_url", ""))
        print(f"手机端: 已部署 ({target_name} -> {server_url})")
    else:
        print("手机端: 未启动")


def 停止开发版() -> None:
    os.chdir(ROOT_DIR)
    停止开发版进程()
    
    # 检查 Docker 是否运行，如果未运行则跳过停止 docker 依赖
    if not docker_是否运行():
        echo("Docker 未运行，跳过停止 docker 依赖")
        return
    
    echo("正在停止 docker 依赖")
    try:
        subprocess.run(组合_compose_命令("stop", "postgres", "redis", "minio", "twikoo"), check=False, cwd=ROOT_DIR)
    except KeyboardInterrupt:
        pass


def 检查_api_健康() -> bool:
    urls = [
        "http://localhost:8000/api/health",
        "http://localhost:8000/api/docs",
        "http://localhost:8000/",
    ]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 300:
                    return True
        except (urllib.error.URLError, TimeoutError):
            continue
    return False


def 单独启动手机端(*, phone_target: Optional[str], phone_host: Optional[str], phone_port: int) -> None:
    os.chdir(ROOT_DIR)
    确保手机端依赖()
    确保手机端开发服务已启动(phone_port)
    try:
        启动安卓手机端(
            app_dir=PHONE_DIR,
            phone_target=phone_target,
            phone_host=phone_host,
            phone_port=phone_port,
        )
    except KeyboardInterrupt:
        print("")
        echo("检测到 Ctrl+C，正在停止手机端开发环境")
        停止手机端开发进程()
        return
    except Exception:
        停止手机端开发进程()
        raise


def 更新开发数据库(use_venv: bool) -> None:
    """在开发模式下执行数据库迁移。"""
    os.chdir(ROOT_DIR)
    查找命令("docker")
    检查_docker_运行()
    确保_env_文件()
    确保后端环境(use_venv)

    env_map = 解析_dotenv(CLOUD_ENV_FILE)
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@127.0.0.1:15432/{postgres_db}"

    echo("启动数据库依赖")
    subprocess.run(
        组合_compose_命令("up", "-d", "postgres"),
        check=True,
        cwd=ROOT_DIR,
    )
    echo("等待数据库就绪")
    等待_docker_compose_服务就绪("postgres", timeout=90)

    py = 后端_python_路径(use_venv)
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["DATABASE_URL"] = database_url

    echo("执行开发数据库迁移")
    subprocess.run(
        [str(py), "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=BACKEND_DIR,
        env=env,
    )
    echo("开发数据库已更新到最新版本")


def 更新生产数据库() -> None:
    """在生产模式下执行数据库迁移。"""
    os.chdir(ROOT_DIR)
    查找命令("docker")
    检查_docker_运行()
    第一次复制 = 确保_env_文件()
    if 第一次复制:
        自动生成认证密钥()
        echo("已完成生产环境密钥初始化")
        echo("请先编辑 apps/cloud/.env 文件中的敏感信息（密码、认证密钥等），然后重新运行此脚本")
        raise SystemExit(0)

    echo("启动生产后端与数据库容器")
    subprocess.run(
        组合_compose_命令("up", "-d", "postgres", "backend"),
        check=True,
        cwd=ROOT_DIR,
    )

    echo("执行生产数据库迁移")
    subprocess.run(
        组合_compose_命令(
            "exec",
            "-T",
            "-e",
            "PYTHONPATH=/app",
            "backend",
            "python",
            "-m",
            "alembic",
            "upgrade",
            "head",
        ),
        check=True,
        cwd=ROOT_DIR,
    )
    echo("生产数据库已更新到最新版本")


def 启动生产版() -> None:
    os.chdir(ROOT_DIR)
    查找命令("docker")
    echo("检查 Docker 状态")
    检查_docker_运行()
    第一次复制 = 确保_env_文件()
    if 第一次复制:
        自动生成认证密钥()
        echo("已完成生产环境密钥初始化")
        echo("请先编辑 apps/cloud/.env 文件中的敏感信息（密码、认证密钥等），然后重新运行此脚本")
        exit(0)

    echo("构建并启动生产容器")
    subprocess.run(组合_compose_命令("up", "-d", "--build"), check=True, cwd=ROOT_DIR)
    echo("重启 nginx 以更新 upstream 解析")
    subprocess.run(组合_compose_命令("restart", "nginx"), check=False, cwd=ROOT_DIR)
    更新生产数据库()

    echo("等待服务启动")
    time.sleep(10)

    echo("检查容器状态")
    subprocess.run(组合_compose_命令("ps"), check=False, cwd=ROOT_DIR)

    if 检查_api_健康():
        echo("API 健康检查通过")
    else:
        echo("API 健康检查失败，请检查容器日志")

    print("")
    print("生产环境已启动:")
    print("  前端:  http://www.sakurakugu.top")
    print("  API:   http://api.sakurakugu.top")
    print("  文档:  http://api.sakurakugu.top/api/docs")


def 停止生产版() -> None:
    os.chdir(ROOT_DIR)
    echo("停止生产容器")
    subprocess.run(组合_compose_命令("down"), check=False, cwd=ROOT_DIR)


def 显示生产状态() -> None:
    os.chdir(ROOT_DIR)
    echo("生产容器状态:")
    subprocess.run(组合_compose_命令("ps"), check=False, cwd=ROOT_DIR)


def 解析_docker_compose_镜像(compose_path: Path) -> list[str]:
    """解析 docker-compose.yml 文件，提取所有镜像名称。"""
    # PyYAML 当前未提供类型桩，这里按运行时依赖使用。
    import yaml  # type: ignore[import-untyped]

    content = compose_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    images = []
    services = data.get("services", {})
    for service_name, service_config in services.items():
        image = service_config.get("image")
        if image:
            images.append(image)

    return images


def 验证_docker_compose_镜像(compose_path: Path) -> None:
    """验证 docker-compose.yml 中定义的所有镜像。"""
    echo(f"解析 compose 文件: {compose_path}")
    images = 解析_docker_compose_镜像(compose_path)

    if not images:
        echo("未找到需要拉取的镜像（所有服务均为 build 模式）")
        return

    echo(f"发现 {len(images)} 个镜像需要验证")

    查找命令("docker")
    检查_docker_运行()

    echo("开始验证镜像...")
    验证_docker_镜像(images)
    echo("所有镜像验证完成")


def 打印帮助() -> None:
    script_path = f"./tools/{SCRIPT_NAME}"
    print("用法:")
    print(f"  python {script_path}")
    print(f"  python {script_path} --cloud [--start|--stop|--restart|--status|--db-upgrade] [--venv] [--prod]")
    print(f"  python {script_path} --phone [--target TARGET] [--host HOST] [--port PORT]")
    print(f"  python {script_path} --apk [--debug|--release]")
    print(f"  python {script_path} --verify-images COMPOSE_FILE")
    print(f"  python {script_path} --help")
    print("")
    print("模式说明:")
    print("  不加参数:    默认等价于 `--cloud --restart`，只重启云端开发环境")
    print("  --cloud:     云端模式，管理 apps/cloud 的后端、Web 前端和开发依赖")
    print("  --phone:     手机端热更新部署，管理 apps/phone 的 Android 调试接入")
    print("  --apk:       构建 apps/phone 的 Android 安装包")
    print("")
    print("云端模式动作:")
    print("  --start:       启动云端开发环境")
    print("  --stop:        停止云端开发环境")
    print("  --restart:     重启云端开发环境（默认）")
    print("  --status:      查看云端开发环境状态")
    print("  --db-upgrade:  执行数据库迁移")
    print("  --prod:        对云端模式使用生产配置")
    print("  --venv:        云端开发模式下使用后端虚拟环境")
    print("")
    print("手机端参数:")
    print("  --target:  指定 Android 目标 ID，仅 `--phone` 可用")
    print("  --host:    指定手机端访问开发服务器的主机地址，仅 `--phone` 可用")
    print(f"  --port:    指定 apps/phone 开发服务器端口，仅 `--phone` 可用，默认 {PHONE_DEV_PORT}")
    print("")
    print("安装包参数:")
    print("  --debug:    构建 Debug APK，仅 `--apk` 可用")
    print("  --release:  构建 Release APK，仅 `--apk` 可用，默认值")
    print("")
    print("兼容说明:")
    print("  位置动作 `start|stop|restart|status|db-upgrade` 仍可用，但建议改用 `--cloud` + 动作参数")
    print("  `--phone` 与 `--apk` 均为独立模式，不会隐式操作云端环境")
    print("")
    print("示例:")
    print(f"  python {script_path}")
    print(f"  python {script_path} --cloud --status")
    print(f"  python {script_path} --cloud --start --venv")
    print(f"  python {script_path} --phone")
    print(f"  python {script_path} --phone --target emulator-5554")
    print(f"  python {script_path} --apk --debug")


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="跨平台开发/生产启动器", add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="启动环境")
    group.add_argument("--stop", action="store_true", help="停止环境")
    group.add_argument("--restart", action="store_true", help="重启环境（默认）")
    group.add_argument("--status", action="store_true", help="查看环境状态")
    group.add_argument("--db-upgrade", action="store_true", help="更新数据库到最新迁移")
    group.add_argument("--verify-images", metavar="COMPOSE_FILE", help="验证 docker-compose.yml 中的镜像（传入 compose 文件路径）")
    parser.add_argument("action", nargs="?", help="可选动作")
    parser.add_argument("--cloud", action="store_true", help="显式指定云端模式（默认模式）")
    parser.add_argument("--prod", action="store_true", help="使用生产模式")
    parser.add_argument("--venv", action="store_true", help="开发模式下使用 Python 虚拟环境")
    mobile_group = parser.add_mutually_exclusive_group()
    mobile_group.add_argument("--phone", action="store_true", help="单独启动 apps/phone 的 Android 手机端热更新")
    mobile_group.add_argument("--apk", action="store_true", help="构建 apps/phone 的 Android APK 安装包")
    parser.add_argument("--target", help="指定 Android 目标 ID（仅 --phone 使用）")
    parser.add_argument("--host", help="指定手机端访问前端开发服务器的主机地址（仅 --phone 使用）")
    parser.add_argument("--port", type=int, default=PHONE_DEV_PORT, help="指定 apps/phone 开发服务器端口（仅 --phone 使用，默认 5174）")
    variant_group = parser.add_mutually_exclusive_group()
    variant_group.add_argument("--debug", action="store_true", help="构建 Android Debug 安装包（仅 --apk 使用）")
    variant_group.add_argument("--release", action="store_true", help="构建 Android Release 安装包（仅 --apk 使用，默认）")
    parser.add_argument("--relay-cwd", help=argparse.SUPPRESS)
    parser.add_argument("--relay-log", help=argparse.SUPPRESS)
    parser.add_argument("--relay-cmd-json", help=argparse.SUPPRESS)
    parser.add_argument("--relay-env-json", help=argparse.SUPPRESS)
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    return parser.parse_args()


def main() -> int:
    args = 解析参数()
    if args.action == "__relay__":
        return 运行日志转发模式(args)

    if args.help:
        打印帮助()
        return 0

    # 处理镜像验证模式
    if args.verify_images:
        compose_path = Path(args.verify_images)
        if not compose_path.exists():
            print(f"错误: 文件不存在: {compose_path}", file=sys.stderr)
            return 1
        try:
            验证_docker_compose_镜像(compose_path)
            return 0
        except Exception as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1

    try:
        if args.prod and (args.phone or args.apk):
            raise RuntimeError("生产模式不支持手机端热更新或安装包构建")

        if args.cloud and (args.phone or args.apk):
            raise RuntimeError("`--cloud` 不能与 `--phone`、`--apk` 同时使用")

        if (args.target or args.host or args.port != PHONE_DEV_PORT) and not args.phone:
            raise RuntimeError("`--target`、`--host`、`--port` 仅可与 `--phone` 一起使用")

        if (args.debug or args.release) and not args.apk:
            raise RuntimeError("`--debug`、`--release` 仅可与 `--apk` 一起使用")

        deprecated_actions = {
            "mobile-start": "--phone",
            "phone-start": "--phone",
            "mobile-build": "--apk",
            "phone-build": "--apk",
        }
        if args.action in deprecated_actions:
            raise RuntimeError(f"旧动作 `{args.action}` 已移除，请改用 `{deprecated_actions[args.action]}`")

        if args.phone or args.apk:
            if args.action:
                raise RuntimeError("`--phone`、`--apk` 不能与位置动作同时使用")
            if args.start or args.stop or args.restart or args.status or args.db_upgrade or args.cloud:
                raise RuntimeError("`--phone`、`--apk` 不能与 `--cloud/--start/--stop/--restart/--status/--db-upgrade` 同时使用")
            action = "phone" if args.phone else "apk"
        else:
            action = args.action or "restart"
            if action not in {"start", "stop", "restart", "status", "db-upgrade"}:
                raise RuntimeError(f"不支持的动作: {action}")

            if args.start:
                action = "start"
            elif args.stop:
                action = "stop"
            elif args.restart:
                action = "restart"
            elif args.status:
                action = "status"
            elif args.db_upgrade:
                action = "db-upgrade"

        if args.prod:
            if action == "start":
                启动生产版()
            elif action == "stop":
                停止生产版()
            elif action == "restart":
                停止生产版()
                启动生产版()
            elif action == "status":
                显示生产状态()
            elif action == "db-upgrade":
                更新生产数据库()
        else:
            if action == "start":
                启动开发版(args.venv)
            elif action == "stop":
                停止开发版()
            elif action == "restart":
                停止开发版()
                启动开发版(args.venv)
            elif action == "status":
                显示开发状态()
            elif action == "db-upgrade":
                更新开发数据库(args.venv)
            elif action == "phone":
                单独启动手机端(
                    phone_target=args.target,
                    phone_host=args.host,
                    phone_port=args.port,
                )
            elif action == "apk":
                build_variant = "debug" if args.debug else "release"
                构建安卓安装包(build_variant=build_variant)
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败，返回代码为: {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except KeyboardInterrupt:
        print("")
        echo("操作已取消")
        return 130
    except Exception as exc:  # pylint: disable=broad-except
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
