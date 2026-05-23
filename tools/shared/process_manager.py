"""进程、端口、状态与日志管理。"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from .config import (
    ROOT_DIR,
    STATE_DIR,
    STATE_FILE,
    STATE_HISTORY_DIR,
)
from .terminal import echo


# ---------------------------------------------------------------------------
# 状态持久化
# ---------------------------------------------------------------------------

_未设置 = object()


def 读取状态() -> Optional[dict]:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except KeyboardInterrupt:
        return None


def _写入状态(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _确保字典字段(state: dict, key: str) -> dict:
    value = state.get(key)
    if not isinstance(value, dict):
        value = {}
    state[key] = value
    return value


def 更新状态(
    *,
    processes: Optional[dict[str, int]] = None,
    mobile: object = _未设置,
    hash_values: Optional[dict[str, str]] = None,
) -> None:
    state = 读取状态() or {}
    if processes is not None:
        current_processes = _确保字典字段(state, "processes")
        current_processes.update(processes)
    if mobile is not _未设置:
        if mobile is None:
            state.pop("mobile", None)
        else:
            state["mobile"] = mobile
    if hash_values is not None:
        current_hash = _确保字典字段(state, "hash")
        current_hash.update(hash_values)
    _写入状态(state)


def 提取进程PID(state: dict, *keys: str) -> tuple[int, ...]:
    processes = state.get("processes") if isinstance(state, dict) else None
    if not isinstance(processes, dict):
        return tuple(0 for _ in keys)
    return tuple(int(processes.get(k, 0)) for k in keys)


# ---------------------------------------------------------------------------
# 进程生命周期
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 端口管理
# ---------------------------------------------------------------------------

def 本地TCP端口可用(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
    except OSError:
        return False
    return True


def 本地TCP端口已被占用(port: int) -> bool:
    hosts = ["127.0.0.1", "::1"]
    for host in hosts:
        try:
            if not 本地TCP端口可用(host, port):
                return True
        except OSError:
            continue
    return False


def 确保本地端口未被占用(port: int, *, label: str, host: str = "127.0.0.1") -> None:
    if not 本地TCP端口已被占用(port):
        return
    raise RuntimeError(f"{label}启动失败：端口 {port} 已被占用，请先释放后再启动")


def 等待本地端口释放(port: int, *, host: str = "127.0.0.1", timeout: float = 10.0) -> bool:
    del host
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not 本地TCP端口已被占用(port):
            return True
        time.sleep(0.2)
    return not 本地TCP端口已被占用(port)


def 读取Windows监听端口PID(port: int) -> list[int]:
    if os.name != "nt":
        return []

    pids: list[int] = []
    seen: set[int] = set()
    result = subprocess.run(
        ["netstat", "-ano"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line.startswith("TCP"):
            continue
        parts = line.split()
        if len(parts) < 5 or parts[3].upper() != "LISTENING":
            continue
        local_address = parts[1]
        pid_text = parts[4]
        try:
            local_port = int(local_address.rsplit(":", 1)[1])
            pid = int(pid_text)
        except (IndexError, ValueError):
            continue
        if local_port != port or pid in seen:
            continue
        seen.add(pid)
        pids.append(pid)

    return pids


def 清理Windows端口残留进程(port: int, *, label: str) -> None:
    if os.name != "nt" or not 本地TCP端口已被占用(port):
        return

    for pid in 读取Windows监听端口PID(port):
        if not 存在进程(pid):
            continue
        print(f"检测到{label}端口 {port} 仍被残留进程占用，正在清理 (PID={pid})")
        停止进程(pid)

    等待本地端口释放(port)


# ---------------------------------------------------------------------------
# HTTP 检查
# ---------------------------------------------------------------------------

def 等待HTTP服务(url: str, timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    raise RuntimeError(f"等待服务超时: {url}")


def 检查HTTP服务(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, TimeoutError):
        return False


# ---------------------------------------------------------------------------
# 日志管理
# ---------------------------------------------------------------------------

def 等待日志出现关键字(log_path: Path, keyword: str, timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log_path.exists():
            try:
                content = log_path.read_text(encoding="utf-8")
            except OSError:
                content = ""
            if keyword in content:
                return
        time.sleep(0.3)
    raise RuntimeError(f"等待日志关键字超时: {keyword}")


def 生成日志启动时间() -> datetime:
    return datetime.now().astimezone()


def 格式化日志时间(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def 格式化日志文件时间(dt: datetime) -> str:
    return dt.strftime("%Y%m%d-%H%M%S")


def 从日志读取启动时间(log_path: Path) -> Optional[datetime]:
    try:
        with open(log_path, "r", encoding="utf-8") as log_fp:
            first_line = log_fp.readline().strip()
    except OSError:
        return None

    prefix = "[启动时间] "
    if not first_line.startswith(prefix):
        return None

    value = first_line[len(prefix):].strip()
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        return None


def 生成唯一日志归档路径(log_path: Path, archived_at: datetime) -> Path:
    STATE_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = 格式化日志文件时间(archived_at)
    candidate = STATE_HISTORY_DIR / f"{log_path.stem}-{timestamp}{log_path.suffix}"
    if not candidate.exists():
        return candidate

    index = 1
    while True:
        candidate = STATE_HISTORY_DIR / f"{log_path.stem}-{timestamp}-{index}{log_path.suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def 归档旧日志(log_path: Path) -> Optional[Path]:
    if not log_path.exists() or log_path.stat().st_size == 0:
        return None

    archived_at = 从日志读取启动时间(log_path)
    if archived_at is None:
        archived_at = datetime.fromtimestamp(log_path.stat().st_mtime).astimezone()

    archive_path = 生成唯一日志归档路径(log_path, archived_at)
    shutil.move(str(log_path), str(archive_path))
    return archive_path


def 准备日志文件(log_path: Path, *, started_at: datetime, cmd: list[str], cwd: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    归档旧日志(log_path)
    with open(log_path, "w", encoding="utf-8") as log_fp:
        log_fp.write(f"[启动时间] {格式化日志时间(started_at)}\n")
        log_fp.write(f"[工作目录] {cwd}\n")
        log_fp.write(f"[启动命令] {' '.join(cmd)}\n")
        log_fp.write("\n")


def 启动并转发日志(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    *,
    started_at: Optional[datetime] = None,
    env_patch: Optional[Dict[str, str]] = None,
    force_color: bool = False,
    terminal_title: Optional[str] = None,
) -> subprocess.Popen:
    当前启动时间 = started_at or 生成日志启动时间()
    准备日志文件(log_path, started_at=当前启动时间, cmd=cmd, cwd=cwd)

    relay_env_patch: Dict[str, str] = {}
    if env_patch:
        relay_env_patch.update(env_patch)
    if force_color:
        relay_env_patch.update({
            "FORCE_COLOR": "1",
            "PY_COLORS": "1",
            "CLICOLOR_FORCE": "1",
            "TERM": "xterm-256color",
        })
        relay_env_patch.pop("NO_COLOR", None)

    relay_script = Path(__file__).resolve().parent / "_relay.py"
    relay_cmd = [
        sys.executable,
        str(relay_script),
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
    if terminal_title:
        relay_cmd.extend(["--relay-title", terminal_title])

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


# ---------------------------------------------------------------------------
# 交互辅助
# ---------------------------------------------------------------------------

def 等待二次确认中断(*, 首次提示: str, 执行提示: str, 停止函数: Callable[[], None]) -> None:
    上次中断时间 = 0.0
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            当前时间 = time.monotonic()
            if 当前时间 - 上次中断时间 <= 2:
                print("")
                echo(执行提示)
                try:
                    停止函数()
                except KeyboardInterrupt:
                    pass
                return
            上次中断时间 = 当前时间
            print("")
            echo(首次提示)


def 查找命令(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"未找到命令: {name}")


def 读取JSON输出(stdout: str) -> list[dict]:
    content = stdout.strip()
    if not content:
        return []
    return json.loads(content)


def 打开文件资源管理器(path: Path) -> None:
    target = path.resolve()
    if os.name == "nt":
        if target.is_file():
            subprocess.Popen(["explorer.exe", "/select,", str(target)])
        else:
            subprocess.Popen(["explorer.exe", str(target)])
        return

    opener = shutil.which("open") or shutil.which("xdg-open")
    if opener:
        subprocess.Popen([opener, str(target.parent if target.is_file() else target)])


def 获取本机局域网IP() -> str:
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


# ---------------------------------------------------------------------------
# 通用进程停止辅助
# ---------------------------------------------------------------------------

def _停止单个开发进程(
    *,
    state: Optional[dict],
    显示未找到提示: bool,
    进程键: str,
    进程显示名: str,
    未启动提示: str,
    清理函数: Callable[[], None],
    提取_pid函数: Callable[[dict], int],
) -> None:
    try:
        current_state = state if state is not None else 读取状态()
        if current_state is None:
            if 显示未找到提示:
                print(f"未找到{进程显示名}开发进程记录。")
            清理函数()
            return

        pid = 提取_pid函数(current_state)
        if pid <= 0:
            if 显示未找到提示:
                print(未启动提示)
            清理函数()
            return

        if 存在进程(pid):
            停止进程(pid)
            print(f"已停止 {进程键} (PID={pid})")
        else:
            print(f"{进程键} 已停止 (PID={pid})")

        清理函数()
    except KeyboardInterrupt:
        清理函数()
