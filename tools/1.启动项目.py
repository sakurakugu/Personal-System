"""跨平台本地开发启动器。

本脚本主要进行转发：
  python tools/commands/启动云端.py    — 云端模式（后端 + Web 前端 + Docker）
  python tools/commands/启动桌面端.py  — 桌面端模式（Electron 开发 / 构建）
  python tools/commands/启动手机端.py  — 手机端模式（Android 热更新 / APK 构建）
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent


def _转发(script: str) -> int:
    script_path = TOOLS_DIR / "commands" / script
    filtered_args = [sys.executable, str(script_path)]

    skip_flags = {"--cloud", "--desktop", "--pc", "--phone", "--apk"}
    for arg in sys.argv[1:]:
        if arg not in skip_flags:
            filtered_args.append(arg)

    return subprocess.run(filtered_args, cwd=TOOLS_DIR.parent).returncode


def main() -> int:
    args = sys.argv[1:]

    # 转发模式（日志转发）
    if args and args[0] == "__relay__":
        # 日志转发已迁移到 tools/shared/_relay.py
        sys.path.insert(0, str(TOOLS_DIR))
        from shared._relay import _run_relay
        return _run_relay()

    # 帮助 / 无参数
    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    # 判断目标脚本
    if "--desktop" in args or "--pc" in args:
        return _转发("启动桌面端.py")
    if "--phone" in args or "--apk" in args:
        return _转发("启动手机端.py")

    return _转发("启动云端.py")


if __name__ == "__main__":
    raise SystemExit(main())
