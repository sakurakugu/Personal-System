"""跨平台本地开发启动器。

start:   docker 依赖 + 后端/前端热重载
stop:    停止后端/前端 + docker 依赖
restart: 停止后启动
status:  显示进程和 docker 状态
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
SCRIPT_NAME = Path(__file__).name
STATE_DIR = ROOT_DIR / ".cache" / ".dev"
STATE_FILE = STATE_DIR / "config.json"
BACKEND_LOG = STATE_DIR / "backend.log"
FRONTEND_LOG = STATE_DIR / "frontend.log"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def echo(msg: str) -> None:
    print(f"==> {msg}")


def 查找命令(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"未找到命令: {name}")


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
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        return False
    echo("未找到 .env，正在从 .env.example 复制")
    shutil.copyfile(ROOT_DIR / ".env.example", env_file)
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


def 自动生成_jwt_密钥() -> None:
    env_file = ROOT_DIR / ".env"
    env_map = 解析_dotenv(env_file)
    current = env_map.get("JWT_SECRET_KEY", "")
    if current != "replace-with-a-very-long-random-string":
        return
    new_key = secrets.token_hex(32)
    if 更新_env_键值(env_file, "JWT_SECRET_KEY", new_key):
        echo("已自动生成 JWT_SECRET_KEY")


def 组合_env_参数() -> list[str]:
    env_file = ".env" if (ROOT_DIR / ".env").exists() else ".env.example"
    return ["--env-file", env_file]


def 提取进程_pid(state: dict) -> tuple[int, int]:
    processes = state.get("processes")
    if not isinstance(processes, dict):
        return 0, 0
    backend_pid = int(processes.get("backend", 0))
    frontend_pid = int(processes.get("frontend", 0))
    return backend_pid, frontend_pid


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
    state["processes"] = {
        "backend": backend_pid,
        "frontend": frontend_pid,
    }
    if package_hash is not None:
        state["hash"] = state.get("hash", {})
        state["hash"]["frontend_package"] = package_hash
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def 确保前端依赖() -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    package_json = FRONTEND_DIR / "package.json"
    
    # 检查 package.json 是否存在
    if not package_json.exists():
        raise RuntimeError(f"未找到 package.json: {package_json}")
    
    # 计算当前 package.json 的哈希
    current_hash = 计算文件哈希(package_json)
    state = 读取状态()
    saved_hash = state.get("hash", {}).get("frontend_package") if state else None
    
    # 如果 node_modules 存在且 package.json 未变化，跳过安装
    if node_modules.exists() and saved_hash == current_hash:
        return
    
    if not node_modules.exists():
        echo("首次安装前端依赖")
    elif saved_hash != current_hash:
        echo("检测到 package.json 变化，重新安装前端依赖")
    
    npm_cmd = 解析_npm_命令()
    subprocess.run([*npm_cmd, "install"], check=True, cwd=FRONTEND_DIR)
    
    # 保存新的哈希值到状态文件
    state = 读取状态() or {}
    state["hash"] = state.get("hash", {})
    state["hash"]["frontend_package"] = current_hash
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    echo("前端依赖安装完成")


def 解析_npm_命令() -> list[str]:
    if os.name == "nt":
        for name in ("npm.cmd", "npm.exe", "npm"):
            path = shutil.which(name)
            if path:
                return [path]
        raise RuntimeError("未找到命令: npm（请确认 Node.js 安装目录已加入 PATH）")
    查找命令("npm")
    return ["npm"]

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

def 镜像存在(image: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def 验证_docker_镜像(images: list[str]) -> None:
    for image in images:
        if 镜像存在(image):
            echo(f"镜像已存在: {image}")
            continue

        echo(f"正在拉取镜像: {image}")

        result = subprocess.run(
            ["docker", "pull", image],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                "无法拉取 Docker 镜像。\n"
                f"镜像: {image}\n"
                f"错误: {stderr}"
            )


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
    查找命令("docker")
    查找命令(sys.executable)
    npm_cmd = 解析_npm_命令()

    echo("检查 Docker 状态")
    检查_docker_运行()

    确保_env_文件()

    env_map = 解析_dotenv(ROOT_DIR / ".env")
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    minio_key = env_map.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = env_map.get("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket = env_map.get("MINIO_BUCKET", "blog-uploads")
    minio_public_url = env_map.get("MINIO_PUBLIC_URL", "http://localhost:8000/files")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@localhost:15432/{postgres_db}"

    验证_docker_镜像(["postgres:16-alpine", "redis:7-alpine", "minio/minio:latest"])

    echo("开始安装 docker 依赖: postgres redis minio")
    subprocess.run(["docker", "compose", *组合_env_参数(), "up", "-d", "postgres", "redis", "minio"], check=True, cwd=ROOT_DIR)

    echo("停止本地开发进程")
    停止开发版进程()

    确保后端环境(use_venv)
    确保前端依赖()

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    backend_env_patch = {
        "APP_ENV": "development",
        "APP_DEBUG": "true",
        "DATABASE_URL": database_url,
        "REDIS_URL": "redis://localhost:6379/0",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": minio_key,
        "MINIO_SECRET_KEY": minio_secret,
        "MINIO_BUCKET": minio_bucket,
        "MINIO_USE_SSL": "false",
        "MINIO_PUBLIC_URL": minio_public_url,
        "CORS_ORIGINS": '["http://localhost:5173"]',
    }

    py = 后端_python_路径(use_venv)
    backend_cmd = [str(py), "-m", "uvicorn", "app.main:app", "--reload", "--use-colors", "--host", "0.0.0.0", "--port", "8000"]
    frontend_cmd = [*npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

    echo("正在启动后端热重载")
    backend_proc = 启动并转发日志(backend_cmd, BACKEND_DIR, BACKEND_LOG, env_patch=backend_env_patch, force_color=True)
    echo("正在启动前端热重载")
    frontend_proc = 启动并转发日志(frontend_cmd, FRONTEND_DIR, FRONTEND_LOG, force_color=True)

    保存状态(backend_proc.pid, frontend_proc.pid)

    print("")
    print("本地开发环境已启动:")
    print("  前端: http://localhost:5173/")
    print("  后端:  http://localhost:8000/api/docs")
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
        subprocess.run(["docker", "compose", *组合_env_参数(), "ps", "postgres", "redis", "minio"], check=False, cwd=ROOT_DIR)
    except subprocess.CalledProcessError as e:
        print(f"检查 Docker 依赖状态时出错: {e}")
        return

    state = 读取状态()
    if state is None:
        print("未找到本地开发进程记录。")
        return

    backend_pid, frontend_pid = 提取进程_pid(state)
    print(f"后端:  {'正在运行' if 存在进程(backend_pid) else '已停止'} (PID={backend_pid})")
    print(f"前端: {'正在运行' if 存在进程(frontend_pid) else '已停止'} (PID={frontend_pid})")


def 停止开发版() -> None:
    os.chdir(ROOT_DIR)
    停止开发版进程()
    
    # 检查 Docker 是否运行，如果未运行则跳过停止 docker 依赖
    if not docker_是否运行():
        echo("Docker 未运行，跳过停止 docker 依赖")
        return
    
    echo("正在停止 docker 依赖")
    try:
        subprocess.run(["docker", "compose", *组合_env_参数(), "stop", "postgres", "redis", "minio"], check=False, cwd=ROOT_DIR)
    except KeyboardInterrupt:
        pass


def 检查_api_健康(url: str = "http://localhost:8000/api/health") -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def 启动生产版() -> None:
    os.chdir(ROOT_DIR)
    查找命令("docker")
    echo("检查 Docker 状态")
    检查_docker_运行()
    第一次复制 = 确保_env_文件()
    if 第一次复制:
        自动生成_jwt_密钥()
        echo("已完成生产环境密钥初始化")
        echo("请先编辑 .env 文件中的敏感信息（密码、JWT密钥等），然后重新运行此脚本")
        exit(0)

    echo("构建并启动生产容器")
    subprocess.run(["docker", "compose", *组合_env_参数(), "up", "-d", "--build"], check=True, cwd=ROOT_DIR)

    echo("等待服务启动")
    time.sleep(10)

    echo("检查容器状态")
    subprocess.run(["docker", "compose", *组合_env_参数(), "ps"], check=False, cwd=ROOT_DIR)

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
    subprocess.run(["docker", "compose", *组合_env_参数(), "down"], check=False, cwd=ROOT_DIR)


def 显示生产状态() -> None:
    os.chdir(ROOT_DIR)
    echo("生产容器状态:")
    subprocess.run(["docker", "compose", *组合_env_参数(), "ps"], check=False, cwd=ROOT_DIR)


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="跨平台开发/生产启动器")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="启动环境")
    group.add_argument("--stop", action="store_true", help="停止环境")
    group.add_argument("--restart", action="store_true", help="重启环境（默认）")
    group.add_argument("--status", action="store_true", help="查看环境状态")
    parser.add_argument("action", nargs="?", help="可选动作")
    parser.add_argument("--prod", action="store_true", help="使用生产模式")
    parser.add_argument("--venv", action="store_true", help="开发模式下使用 Python 虚拟环境")
    parser.add_argument("--relay-cwd", help=argparse.SUPPRESS)
    parser.add_argument("--relay-log", help=argparse.SUPPRESS)
    parser.add_argument("--relay-cmd-json", help=argparse.SUPPRESS)
    parser.add_argument("--relay-env-json", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = 解析参数()
    if args.action == "__relay__":
        return 运行日志转发模式(args)

    action = args.action or "restart"
    if action not in {"start", "stop", "restart", "status"}:
        raise RuntimeError(f"不支持的动作: {action}")

    if args.start:
        action = "start"
    elif args.stop:
        action = "stop"
    elif args.restart:
        action = "restart"
    elif args.status:
        action = "status"

    try:
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
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败，返回代码为: {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:  # pylint: disable=broad-except
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
