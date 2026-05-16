"""终端输出辅助。"""

from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager

from .config import ANSI_GREEN, ANSI_RED, ANSI_RESET, ANSI_YELLOW


def echo(msg: str) -> None:
    print(f"==> {msg}")


def 设置终端标题(title: str) -> None:
    # VS Code 在 tabs.title = ${sequence} 时会读取 OSC 标题序列。
    sys.stdout.write(f"\033]0;{title}\007")
    sys.stdout.flush()


@contextmanager
def 保持终端标题(title: str, *, interval: float = 0.5):
    stop_event = threading.Event()
    设置终端标题(title)

    def _worker() -> None:
        while not stop_event.wait(interval):
            设置终端标题(title)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join(timeout=1)


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
