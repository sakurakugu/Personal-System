"""桌面端模式启动器 — Electron 开发 + 构建。

start / restart:  启动桌面端 Electron 开发环境
stop:             停止桌面端开发环境
status:           查看桌面端状态
build:            构建 Electron 可执行安装包
--help:           查看所有命令
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import (
    DESKTOP_DIR,
    DESKTOP_DEV_PORT,
    DESKTOP_LOG,
    ROOT_DIR,
)
from shared.dependency_manager import 确保桌面端依赖, 解析Npm命令
from shared.env_utils import 获取桌面端环境变量
from shared.process_manager import (
    存在进程,
    提取进程PID,
    更新状态,
    启动并转发日志,
    等待本地端口释放,
    等待日志出现关键字,
    清理Windows端口残留进程,
    确保本地端口未被占用,
    生成日志启动时间,
    格式化日志时间,
    读取状态,
    等待二次确认中断,
    打开文件资源管理器,
    _停止单个开发进程,
)
from shared.terminal import echo, 保持终端标题

SCRIPT_NAME = Path(__file__).name
TERMINAL_TITLE = "桌面端"


# ---------------------------------------------------------------------------
# 进程停止
# ---------------------------------------------------------------------------

def 清理桌面端状态() -> None:
    更新状态(processes={"desktop": 0})


def 等待桌面端端口释放() -> None:
    等待本地端口释放(DESKTOP_DEV_PORT)


def 停止桌面端开发进程(*, state: dict | None = None, 显示未找到提示: bool = True) -> None:
    _停止单个开发进程(
        state=state,
        显示未找到提示=显示未找到提示,
        进程键="desktop",
        进程显示名="桌面端",
        未启动提示="桌面端: 未启动",
        清理函数=清理桌面端状态,
        提取_pid函数=lambda s: 提取进程PID(s, "desktop")[0],
    )
    清理Windows端口残留进程(DESKTOP_DEV_PORT, label="桌面端")
    等待桌面端端口释放()


# ---------------------------------------------------------------------------
# 开发模式
# ---------------------------------------------------------------------------

def 单独启动桌面端(*, 重启已有进程: bool = True) -> None:
    os.chdir(ROOT_DIR)
    确保桌面端依赖()
    if 重启已有进程:
        停止桌面端开发进程(显示未找到提示=False)
    else:
        state = 读取状态()
        desktop_pid = 提取进程PID(state, "desktop")[0] if state else 0
        if desktop_pid > 0 and 存在进程(desktop_pid):
            print(f"桌面端已在运行 (PID={desktop_pid})")
            print(f"桌面端日志: {DESKTOP_LOG}")
            print(f"Web 预览入口: http://localhost:{DESKTOP_DEV_PORT}/")
            return

    确保本地端口未被占用(DESKTOP_DEV_PORT, label="桌面端")

    npm_cmd = 解析Npm命令()
    desktop_cmd = [*npm_cmd, "run", "electron:dev"]
    desktop_env = 获取桌面端环境变量()
    启动时间 = 生成日志启动时间()
    echo("正在启动桌面端开发环境")
    print(f"  启动时间: {格式化日志时间(启动时间)}")
    proc = 启动并转发日志(
        desktop_cmd,
        DESKTOP_DIR,
        DESKTOP_LOG,
        started_at=启动时间,
        env_patch=desktop_env,
        force_color=True,
        terminal_title=TERMINAL_TITLE,
    )
    更新状态(processes={"desktop": proc.pid})

    try:
        等待日志出现关键字(DESKTOP_LOG, "桌面端主窗口已就绪", timeout=60)
    except Exception as exc:
        停止桌面端开发进程(显示未找到提示=False)
        raise RuntimeError(f"桌面端主窗口启动失败，请检查日志: {DESKTOP_LOG}") from exc

    print("")
    print("桌面端开发环境已启动:")
    print(f"  Web 预览入口: http://localhost:{DESKTOP_DEV_PORT}/")
    print(f"  桌面端日志: {DESKTOP_LOG}")
    print(f"  Electron 镜像: {desktop_env['ELECTRON_MIRROR']}")
    print(f"  Electron 缓存: {desktop_env['ELECTRON_CACHE']}")
    print("")
    print(f"停止命令: {sys.executable} ./tools/{SCRIPT_NAME} --stop")
    print("按 Ctrl+C 可停止桌面端开发环境并退出。")

    try:
        while True:
            time.sleep(1)
            if proc.poll() is not None:
                break
    except KeyboardInterrupt:
        等待二次确认中断(
            首次提示="收到中断信号，再按一次 Ctrl+C 才会停止桌面端开发环境",
            执行提示="检测到 Ctrl+C，正在停止桌面端开发环境",
            停止函数=lambda: 停止桌面端开发进程(显示未找到提示=False),
        )
        return

    清理桌面端状态()


# ---------------------------------------------------------------------------
# 构建模式
# ---------------------------------------------------------------------------

def 构建桌面端() -> None:
    os.chdir(ROOT_DIR)
    确保桌面端依赖()

    npm_cmd = 解析Npm命令()
    desktop_env = 获取桌面端环境变量()
    echo("正在构建桌面端 Electron 安装包")
    subprocess.run([*npm_cmd, "run", "electron:build"], check=True, cwd=DESKTOP_DIR, env=desktop_env)
    release_dir = DESKTOP_DIR / "release"
    echo(f"桌面端安装包构建完成，输出目录: {release_dir}")
    打开文件资源管理器(release_dir)


# ---------------------------------------------------------------------------
# 状态显示
# ---------------------------------------------------------------------------

def 显示桌面端状态() -> None:
    os.chdir(ROOT_DIR)
    state = 读取状态()
    if state is None:
        print("未找到桌面端进程记录。")
        print(f"桌面端日志: {DESKTOP_LOG}")
        return

    desktop_pid = 提取进程PID(state, "desktop")[0]
    if desktop_pid <= 0:
        print("桌面端: 未启动")
    else:
        status = "正在运行" if 存在进程(desktop_pid) else "已停止"
        print(f"桌面端: {status} (PID={desktop_pid})")
    print(f"桌面端日志: {DESKTOP_LOG}")
    print(f"Web 预览入口: http://localhost:{DESKTOP_DEV_PORT}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def 打印帮助() -> None:
    script_path = f"./tools/commands/{SCRIPT_NAME}"
    print("用法:")
    print(f"  python {script_path} [--start|--stop|--restart|--status]")
    print(f"  python {script_path} --build")
    print(f"  python {script_path} --help")
    print("")
    print("动作:")
    print("  --start:   启动桌面端开发环境")
    print("  --stop:    停止桌面端开发环境")
    print("  --restart: 重启桌面端开发环境（默认）")
    print("  --status:  查看桌面端开发环境状态")
    print("  --build:   构建 Electron 可执行安装包")
    print("")
    print("示例:")
    print(f"  python {script_path}")
    print(f"  python {script_path} --status")
    print(f"  python {script_path} --stop")
    print(f"  python {script_path} --build")


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="桌面端模式启动器", add_help=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="启动桌面端")
    group.add_argument("--stop", action="store_true", help="停止桌面端")
    group.add_argument("--restart", action="store_true", help="重启桌面端（默认）")
    group.add_argument("--status", action="store_true", help="查看桌面端状态")
    group.add_argument("--build", action="store_true", help="构建桌面端安装包")
    parser.add_argument("action", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    return parser.parse_args()


def main() -> int:
    with 保持终端标题(TERMINAL_TITLE):
        args = 解析参数()

        if args.help:
            打印帮助()
            return 0

        try:
            if args.build:
                if args.start or args.stop or args.restart or args.status:
                    raise RuntimeError("--build 不能与 --start/--stop/--restart/--status 同时使用")
                构建桌面端()
            elif args.start:
                单独启动桌面端(重启已有进程=False)
            elif args.stop:
                停止桌面端开发进程()
            elif args.restart:
                单独启动桌面端(重启已有进程=True)
            elif args.status:
                显示桌面端状态()
            else:
                单独启动桌面端(重启已有进程=True)
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
