"""日志转发子进程入口，独立运行，不依赖包内其他模块。"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
OSC_TITLE_RE = re.compile(r"\x1b\](?:0|2);.*?(?:\x07|\x1b\\)")


def _移除标题序列(text: str) -> str:
    return OSC_TITLE_RE.sub("", text)


def _设置终端标题(title: str) -> None:
    sys.stdout.write(f"\033]0;{title}\007")
    sys.stdout.flush()


def _run_relay() -> int:
    args = sys.argv[1:]
    relay_cwd: str | None = None
    relay_log: str | None = None
    relay_cmd_json: str | None = None
    relay_env_json: str | None = None
    relay_title: str | None = None

    i = 0
    while i < len(args):
        if args[i] == "__relay__":
            i += 1
            continue
        if args[i] == "--relay-cwd" and i + 1 < len(args):
            relay_cwd = args[i + 1]
            i += 2
        elif args[i] == "--relay-log" and i + 1 < len(args):
            relay_log = args[i + 1]
            i += 2
        elif args[i] == "--relay-cmd-json" and i + 1 < len(args):
            relay_cmd_json = args[i + 1]
            i += 2
        elif args[i] == "--relay-env-json" and i + 1 < len(args):
            relay_env_json = args[i + 1]
            i += 2
        elif args[i] == "--relay-title" and i + 1 < len(args):
            relay_title = args[i + 1]
            i += 2
        else:
            i += 1

    if not relay_cwd or not relay_log or not relay_cmd_json:
        print("错误: 日志转发模式参数不完整", file=sys.stderr)
        return 1

    cmd = json.loads(relay_cmd_json)
    if not isinstance(cmd, list) or not all(isinstance(item, str) for item in cmd):
        print("错误: 日志转发命令格式错误", file=sys.stderr)
        return 1

    env = os.environ.copy()
    if relay_env_json:
        env_patch = json.loads(relay_env_json)
        if not isinstance(env_patch, dict):
            print("错误: 日志转发环境变量格式错误", file=sys.stderr)
            return 1
        env.update({str(k): str(v) for k, v in env_patch.items()})

    process = subprocess.Popen(
        cmd,
        cwd=relay_cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    stop_title_event = threading.Event()
    title_thread: threading.Thread | None = None
    if relay_title:
        _设置终端标题(relay_title)

        def _保持终端标题() -> None:
            while not stop_title_event.wait(0.5):
                _设置终端标题(relay_title)

        title_thread = threading.Thread(target=_保持终端标题, daemon=True)
        title_thread.start()

    assert process.stdout is not None
    Path(relay_log).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(relay_log, "a", encoding="utf-8") as log_fp:
            for line in process.stdout:
                clean_line = _移除标题序列(line)
                sys.stdout.write(clean_line)
                sys.stdout.flush()
                log_fp.write(ANSI_ESCAPE_RE.sub("", clean_line))
                log_fp.flush()

        return process.wait()
    finally:
        stop_title_event.set()
        if title_thread is not None:
            title_thread.join(timeout=1)


if __name__ == "__main__":
    raise SystemExit(_run_relay())
