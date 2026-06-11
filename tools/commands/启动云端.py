"""云端模式启动器 — 后端 + Web 前端 + Docker 依赖。

start:       docker 依赖 + 后端/前端热重载
stop:        停止后端/前端 + docker 依赖
restart:     停止后启动
status:      显示进程和 docker 状态
db-upgrade:  更新数据库到最新迁移
--prod:      使用生产配置
--help:      查看所有命令
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

# 将 tools/ 加入 sys.path，以便导入 shared 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import (
    BACKEND_DIR,
    BACKEND_LOG,
    CLOUD_ENV_FILE,
    COMPOSE_FILE,
    FRONTEND_DIR,
    FRONTEND_DEV_PORT,
    FRONTEND_LOG,
    ROOT_DIR,
    STATE_DIR,
)
from shared.dependency_manager import (
    确保Node应用依赖,
    解析Npm命令,
)
from shared.docker_utils import (
    检查Docker运行,
    等待DockerCompose服务就绪,
    清理Docker构建缓存,
    组合Compose命令,
    验证DockerCompose镜像,
)
from shared.env_utils import (
    读取键值文件,
    自动生成认证密钥,
    确保环境变量文件,
)
from shared.process_manager import (
    存在进程,
    停止进程,
    提取进程PID,
    更新状态,
    启动并转发日志,
    读取状态,
    等待二次确认中断,
)
from shared.terminal import echo, 保持终端标题

SCRIPT_NAME = Path(__file__).name
TERMINAL_TITLE = "云端"


# ---------------------------------------------------------------------------
# Git hooks
# ---------------------------------------------------------------------------

def 确保GitHooks已启用() -> None:
    githooks_dir = ROOT_DIR / ".githooks"
    if not githooks_dir.exists():
        return

    result = subprocess.run(
        ["git", "config", "core.hooksPath"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    current_path = result.stdout.strip() if result.returncode == 0 else ""

    if current_path == ".githooks":
        return

    echo("启用 git hooks")
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        check=True,
        cwd=ROOT_DIR,
    )

    if os.name != "nt":
        for hook_file in githooks_dir.iterdir():
            if hook_file.is_file():
                subprocess.run(
                    ["chmod", "+x", str(hook_file)],
                    check=False,
                    cwd=ROOT_DIR,
                )


# ---------------------------------------------------------------------------
# 后端
# ---------------------------------------------------------------------------

def 后端Python路径(use_venv: bool) -> Path:
    if use_venv:
        if os.name == "nt":
            return BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        return BACKEND_DIR / ".venv" / "bin" / "python"
    return Path(sys.executable)


def 确保后端环境(use_venv: bool) -> None:
    from shared.dependency_manager import _安装应用依赖

    py = 后端Python路径(use_venv)
    requirements_txt = BACKEND_DIR / "requirements.txt"

    if use_venv and not py.exists():
        echo("创建后端虚拟环境")
        subprocess.run(
            [sys.executable, "-m", "venv", str(BACKEND_DIR / ".venv")],
            check=True,
        )

    _安装应用依赖(
        source_file=requirements_txt,
        hash_key="backend_requirements",
        label="后端",
        install=lambda: subprocess.run(
            [str(py), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
            check=True,
            cwd=BACKEND_DIR,
        ),
    )


# ---------------------------------------------------------------------------
# 数据库迁移
# ---------------------------------------------------------------------------

def _执行数据库迁移(
    *,
    启动服务: list[str],
    迁移命令: list[str],
    迁移工作目录: Path,
    迁移环境: Optional[dict[str, str]] = None,
    标签: str,
) -> None:
    from shared.process_manager import 查找命令
    from shared.docker_utils import 检查Docker运行

    os.chdir(ROOT_DIR)
    查找命令("docker")
    检查Docker运行()
    确保环境变量文件()

    echo(f"启动 {' '.join(启动服务)}")
    subprocess.run(组合Compose命令("up", "-d", *启动服务), check=True, cwd=ROOT_DIR)
    echo("等待数据库就绪")
    等待DockerCompose服务就绪("postgres", timeout=90)

    echo(f"执行{标签}数据库迁移")
    subprocess.run(迁移命令, check=True, cwd=迁移工作目录, env=迁移环境)
    echo(f"{标签}数据库已更新到最新版本")


def 更新开发数据库(use_venv: bool) -> None:
    确保后端环境(use_venv)

    env_map = 读取键值文件(CLOUD_ENV_FILE, strip_quotes=True)
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@127.0.0.1:15432/{postgres_db}"

    py = 后端Python路径(use_venv)
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["DATABASE_URL"] = database_url

    _执行数据库迁移(
        启动服务=["postgres"],
        迁移命令=[str(py), "-m", "alembic", "upgrade", "head"],
        迁移工作目录=BACKEND_DIR,
        迁移环境=env,
        标签="开发",
    )


def 更新生产数据库() -> None:
    第一次复制 = 确保环境变量文件()
    if 第一次复制:
        自动生成认证密钥()
        echo("已完成生产环境密钥初始化")
        echo("请先编辑 apps/cloud/.env 文件中的敏感信息（密码、认证密钥等），然后重新运行此脚本")
        raise SystemExit(0)

    _执行数据库迁移(
        启动服务=["postgres", "backend"],
        迁移命令=组合Compose命令(
            "exec", "-T", "-e", "PYTHONPATH=/app", "backend",
            "python", "-m", "alembic", "upgrade", "head",
        ),
        迁移工作目录=ROOT_DIR,
        标签="生产",
    )


# ---------------------------------------------------------------------------
# 进程停止
# ---------------------------------------------------------------------------

def 停止开发版进程() -> None:
    try:
        state = 读取状态()
        if state is None:
            print("未找到本地开发进程记录。")
            return

        backend_pid, frontend_pid = 提取进程PID(state, "backend", "frontend")

        for name, pid in (("backend", backend_pid), ("frontend", frontend_pid)):
            if pid <= 0:
                continue
            if 存在进程(pid):
                停止进程(pid)
                print(f"已停止 {name} (PID={pid})")
            else:
                print(f"{name} 已停止 (PID={pid})")

        更新状态(processes={"backend": 0, "frontend": 0})
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------------------
# 开发模式
# ---------------------------------------------------------------------------

def 启动开发版(use_venv: bool) -> None:
    os.chdir(ROOT_DIR)
    from shared.process_manager import 查找命令 as _查找命令
    _查找命令("git")
    _查找命令("docker")
    _查找命令(sys.executable)
    npm_cmd = 解析Npm命令()

    确保GitHooks已启用()

    echo("检查 Docker 状态")
    检查Docker运行()

    确保环境变量文件()

    env_map = 读取键值文件(CLOUD_ENV_FILE, strip_quotes=True)
    postgres_user = env_map.get("POSTGRES_USER", "bloguser")
    postgres_password = env_map.get("POSTGRES_PASSWORD", "change_me_in_production")
    postgres_db = env_map.get("POSTGRES_DB", "blogdb")
    minio_key = env_map.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = env_map.get("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket = env_map.get("MINIO_BUCKET", "blog-uploads")
    minio_public_url = env_map.get("MINIO_PUBLIC_URL", "http://localhost:8000/files")
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@127.0.0.1:15432/{postgres_db}"

    compose_path = COMPOSE_FILE
    验证DockerCompose镜像(compose_path)

    echo("开始安装 docker 依赖: postgres redis minio twikoo")
    subprocess.run(组合Compose命令("up", "-d", "postgres", "redis", "minio", "twikoo"), check=True, cwd=ROOT_DIR)

    echo("停止本地开发进程")
    停止开发版进程()

    确保后端环境(use_venv)
    确保Node应用依赖(FRONTEND_DIR, hash_key="frontend_package", label="前端")
    更新开发数据库(use_venv)

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    backend_env_patch = {
        "APP_ENV": "development",
        "APP_DEBUG": "true",
        # Windows 文件事件偶尔会漏掉编辑器保存动作，开发模式改用轮询保证热更新稳定触发。
        # "WATCHFILES_FORCE_POLLING": "true",
        # "WATCHFILES_POLL_DELAY_MS": "300",
        "DATABASE_URL": database_url,
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "MINIO_ENDPOINT": "127.0.0.1:9000",
        "MINIO_ACCESS_KEY": minio_key,
        "MINIO_SECRET_KEY": minio_secret,
        "MINIO_BUCKET": minio_bucket,
        "MINIO_USE_SSL": "false",
        "MINIO_PUBLIC_URL": minio_public_url,
    }

    py = 后端Python路径(use_venv)
    backend_cmd = [
        str(py), "-m", "uvicorn", "app.main:app",
        "--reload",
        "--reload-dir", str(BACKEND_DIR / "app"),
        "--reload-include", "*.py",
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
    backend_proc = 启动并转发日志(
        backend_cmd, BACKEND_DIR, BACKEND_LOG,
        env_patch=backend_env_patch, force_color=True,
    )
    echo("正在启动前端热重载")
    frontend_proc = 启动并转发日志(
        frontend_cmd, FRONTEND_DIR, FRONTEND_LOG,
        force_color=True,
    )

    更新状态(processes={"backend": backend_proc.pid, "frontend": frontend_proc.pid})
    更新状态(mobile=None)

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

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            等待二次确认中断(
                首次提示="收到中断信号，再按一次 Ctrl+C 才会停止开发环境",
                执行提示="检测到 Ctrl+C，正在停止开发环境",
                停止函数=停止开发版,
            )
            break

        state = 读取状态()
        if state is None:
            break
        backend_pid, frontend_pid = 提取进程PID(state, "backend", "frontend")
        if not 存在进程(backend_pid) and not 存在进程(frontend_pid):
            break


def 显示开发状态() -> None:
    os.chdir(ROOT_DIR)
    echo("Docker 依赖状态:")
    try:
        subprocess.run(组合Compose命令("ps", "postgres", "redis", "minio", "twikoo"), check=False, cwd=ROOT_DIR)
    except subprocess.CalledProcessError as e:
        print(f"检查 Docker 依赖状态时出错: {e}")
        return

    state = 读取状态()
    if state is None:
        print("未找到本地开发进程记录。")
        return

    backend_pid, frontend_pid = 提取进程PID(state, "backend", "frontend")

    def _打印进程状态(name: str, pid: int) -> None:
        status = "正在运行" if 存在进程(pid) else "已停止"
        print(f"{name}: {status} (PID={pid})")

    _打印进程状态("后端", backend_pid)
    _打印进程状态("前端", frontend_pid)


def 停止开发版() -> None:
    os.chdir(ROOT_DIR)
    停止开发版进程()

    from shared.docker_utils import docker_是否运行 as _docker_ok
    if not _docker_ok():
        echo("Docker 未运行，跳过停止 docker 依赖")
        return

    echo("正在停止 docker 依赖")
    try:
        subprocess.run(组合Compose命令("stop", "postgres", "redis", "minio", "twikoo"), check=False, cwd=ROOT_DIR)
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------------------
# 生产模式
# ---------------------------------------------------------------------------

def 检查API健康() -> bool:
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


def 启动生产版() -> None:
    os.chdir(ROOT_DIR)
    from shared.process_manager import 查找命令 as _查找命令
    _查找命令("docker")
    echo("检查 Docker 状态")
    检查Docker运行()
    第一次复制 = 确保环境变量文件()
    if 第一次复制:
        自动生成认证密钥()
        echo("已完成生产环境密钥初始化")
        echo("请先编辑 apps/cloud/.env 文件中的敏感信息（密码、认证密钥等），然后重新运行此脚本")
        exit(0)

    echo("构建并启动生产容器")
    subprocess.run(组合Compose命令("up", "-d", "--build"), check=True, cwd=ROOT_DIR)
    清理Docker构建缓存(保留时长="168h")
    echo("重启 nginx 以更新 upstream 解析")
    subprocess.run(组合Compose命令("restart", "nginx"), check=False, cwd=ROOT_DIR)
    更新生产数据库()

    echo("等待服务启动")
    time.sleep(10)

    echo("检查容器状态")
    subprocess.run(组合Compose命令("ps"), check=False, cwd=ROOT_DIR)

    if 检查API健康():
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
    subprocess.run(组合Compose命令("down"), check=False, cwd=ROOT_DIR)


def 显示生产状态() -> None:
    os.chdir(ROOT_DIR)
    echo("生产容器状态:")
    subprocess.run(组合Compose命令("ps"), check=False, cwd=ROOT_DIR)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def 打印帮助() -> None:
    script_path = f"./tools/commands/{SCRIPT_NAME}"
    print("用法:")
    print(f"  python {script_path} [--start|--stop|--restart|--status|--db-upgrade] [--venv] [--prod]")
    print(f"  python {script_path} --verify-images COMPOSE_FILE")
    print(f"  python {script_path} --help")
    print("")
    print("动作:")
    print("  --start:       启动云端开发环境")
    print("  --stop:        停止云端开发环境")
    print("  --restart:     重启云端开发环境（默认）")
    print("  --status:      查看云端开发环境状态")
    print("  --db-upgrade:  执行数据库迁移")
    print("  --prod:        使用生产配置")
    print("  --venv:        使用后端虚拟环境")
    print("  --verify-images: 验证 docker-compose.yml 中的镜像")
    print("")
    print("示例:")
    print(f"  python {script_path}")
    print(f"  python {script_path} --status")
    print(f"  python {script_path} --start --venv")
    print(f"  python {script_path} --stop")
    print(f"  python {script_path} --prod --start")
    print(f"  python {script_path} --prod --db-upgrade")


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="云端模式启动器", add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="启动环境")
    group.add_argument("--stop", action="store_true", help="停止环境")
    group.add_argument("--restart", action="store_true", help="重启环境（默认）")
    group.add_argument("--status", action="store_true", help="查看环境状态")
    group.add_argument("--db-upgrade", action="store_true", help="更新数据库到最新迁移")
    group.add_argument("--verify-images", metavar="COMPOSE_FILE", help="验证 compose 文件中的镜像")
    parser.add_argument("action", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--prod", action="store_true", help="使用生产模式")
    parser.add_argument("--venv", action="store_true", help="使用 Python 虚拟环境")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    return parser.parse_args()


def main() -> int:
    with 保持终端标题(TERMINAL_TITLE):
        args = 解析参数()

        if args.help:
            打印帮助()
            return 0

        if args.verify_images:
            compose_path = Path(args.verify_images)
            if not compose_path.exists():
                print(f"错误: 文件不存在: {compose_path}", file=sys.stderr)
                return 1
            try:
                from shared.docker_utils import 验证DockerCompose镜像 as _验证
                _验证(compose_path)
                return 0
            except Exception as exc:
                print(f"错误: {exc}", file=sys.stderr)
                return 1

        try:
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
            else:
                action = "restart"

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
            return 0
        except subprocess.CalledProcessError as exc:
            print(f"命令执行失败，返回代码为: {exc.returncode}: {exc.cmd}", file=sys.stderr)
            return exc.returncode
        except KeyboardInterrupt:
            print("")
            echo("操作已取消")
            return 130
        except Exception as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
