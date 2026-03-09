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
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
STATE_DIR = ROOT_DIR / ".cache" / ".dev"
STATE_FILE = STATE_DIR / "processes.json"
BACKEND_LOG = STATE_DIR / "backend.log"
FRONTEND_LOG = STATE_DIR / "frontend.log"


def step(msg: str) -> None:
    print(f"==> {msg}")


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"未找到命令: {name}")


def parse_dotenv(path: Path) -> Dict[str, str]:
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


def compose_env_args() -> list[str]:
    env_file = ".env" if (ROOT_DIR / ".env").exists() else ".env.example"
    return ["--env-file", env_file]


def read_state() -> Optional[dict]:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(backend_pid: int, frontend_pid: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(
            {
                "backendPid": backend_pid,
                "frontendPid": frontend_pid,
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_pid_tree(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return


def stop_dev_processes() -> None:
    state = read_state()
    if state is None:
        print("未找到本地开发进程记录。")
        return

    backend_pid = int(state.get("backendPid", 0))
    frontend_pid = int(state.get("frontendPid", 0))

    for name, pid in (("backend", backend_pid), ("frontend", frontend_pid)):
        if pid <= 0:
            continue
        if process_exists(pid):
            stop_pid_tree(pid)
            print(f"已停止 {name} (PID={pid})")
        else:
            print(f"{name} 已停止 (PID={pid})")

    if STATE_FILE.exists():
        STATE_FILE.unlink()


def backend_python_path() -> Path:
    if os.name == "nt":
        return BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    return BACKEND_DIR / ".venv" / "bin" / "python"


def ensure_backend_env() -> None:
    py = backend_python_path()
    if not py.exists():
        step("创建后端虚拟环境")
        subprocess.run([sys.executable, "-m", "venv", str(BACKEND_DIR / ".venv")], check=True)

    step("安装后端依赖")
    subprocess.run([str(py), "-m", "pip", "install", "-r", "requirements.txt"], check=True, cwd=BACKEND_DIR)


def ensure_frontend_deps() -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    step("安装前端依赖")
    npm_cmd = resolve_npm_command()
    subprocess.run([*npm_cmd, "install"], check=True, cwd=FRONTEND_DIR)


def resolve_npm_command() -> list[str]:
    if os.name == "nt":
        for name in ("npm.cmd", "npm.exe", "npm"):
            path = shutil.which(name)
            if path:
                return [path]
        raise RuntimeError("未找到命令: npm（请确认 Node.js 安装目录已加入 PATH）")
    require_command("npm")
    return ["npm"]


def verify_docker_images(images: list[str]) -> None:
    for image in images:
        step(f"检查镜像可用性: {image}")
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
                "无法拉取 Docker 镜像，可能是网络或 Docker Hub 访问/鉴权问题。\n"
                "请确认已登录 Docker、网络可访问，或配置镜像加速后重试。\n"
                f"镜像: {image}\n"
                f"错误: {stderr}"
            )


def start_dev() -> None:
    os.chdir(ROOT_DIR)
    require_command("docker")
    require_command(sys.executable)
    npm_cmd = resolve_npm_command()

    if not (ROOT_DIR / ".env").exists():
        step("未找到 .env，正在从 .env.example 复制")
        shutil.copyfile(ROOT_DIR / ".env.example", ROOT_DIR / ".env")

    env_map = parse_dotenv(ROOT_DIR / ".env")
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    minio_key = env_map.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = env_map.get("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket = env_map.get("MINIO_BUCKET", "blog-uploads")
    minio_public_url = env_map.get("MINIO_PUBLIC_URL", "http://localhost:8000/files")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@localhost:15432/{postgres_db}"

    verify_docker_images(["postgres:16-alpine", "redis:7-alpine", "minio/minio:latest"])

    step("开始安装 docker 依赖: postgres redis minio")
    subprocess.run(["docker", "compose", *compose_env_args(), "up", "-d", "postgres", "redis", "minio"], check=True, cwd=ROOT_DIR)

    step("停止本地开发进程")
    stop_dev_processes()

    ensure_backend_env()
    ensure_frontend_deps()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    backend_log_fp = open(BACKEND_LOG, "a", encoding="utf-8")
    frontend_log_fp = open(FRONTEND_LOG, "a", encoding="utf-8")

    backend_env = os.environ.copy()
    backend_env.update(
        {
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
    )

    py = backend_python_path()
    backend_cmd = [str(py), "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    frontend_cmd = [*npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

    step("正在启动后端热重载")
    if os.name == "nt":
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            env=backend_env,
            stdout=backend_log_fp,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        step("正在启动前端热重载")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            stdout=frontend_log_fp,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=BACKEND_DIR,
            env=backend_env,
            stdout=backend_log_fp,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )
        step("正在启动前端热重载")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,
            stdout=frontend_log_fp,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

    save_state(backend_proc.pid, frontend_proc.pid)

    print("")
    print("本地开发环境已启动:")
    print("  前端: http://localhost:5173")
    print("  后端:  http://localhost:8000/api/docs")
    print(f"  后端日志:  {BACKEND_LOG}")
    print(f"  前端日志: {FRONTEND_LOG}")
    print("")
    print("停止命令: python ./tools/1.启动开发环境.py --stop")


def show_status() -> None:
    os.chdir(ROOT_DIR)
    step("Docker 依赖状态:")
    try:
        subprocess.run(["docker", "compose", *compose_env_args(), "ps", "postgres", "redis", "minio"], check=False, cwd=ROOT_DIR)
    except subprocess.CalledProcessError as e:
        print(f"检查 Docker 依赖状态时出错: {e}")
        return

    state = read_state()
    if state is None:
        print("未找到本地开发进程记录。")
        return

    backend_pid = int(state.get("backendPid", 0))
    frontend_pid = int(state.get("frontendPid", 0))
    print(f"后端:  {'正在运行' if process_exists(backend_pid) else '已停止'} (PID={backend_pid})")
    print(f"前端: {'正在运行' if process_exists(frontend_pid) else '已停止'} (PID={frontend_pid})")


def stop_all() -> None:
    os.chdir(ROOT_DIR)
    stop_dev_processes()
    step("正在停止 docker 依赖")
    subprocess.run(["docker", "compose", *compose_env_args(), "stop", "postgres", "redis", "minio"], check=False, cwd=ROOT_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="跨平台本地开发启动器")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="启动开发环境")
    group.add_argument("--stop", action="store_true", help="停止开发环境")
    group.add_argument("--restart", action="store_true", help="重启开发环境（默认）")
    group.add_argument("--status", action="store_true", help="查看开发环境状态")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    action = "restart"
    if args.start:
        action = "start"
    elif args.stop:
        action = "stop"
    elif args.restart:
        action = "restart"
    elif args.status:
        action = "status"

    try:
        if action == "start":
            start_dev()
        elif action == "stop":
            stop_all()
        elif action == "restart":
            stop_all()
            start_dev()
        elif action == "status":
            show_status()
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"命令执行失败，返回代码为: {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:  # pylint: disable=broad-except
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
