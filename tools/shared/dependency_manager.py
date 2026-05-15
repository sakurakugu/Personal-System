"""Node / Python 依赖安装与命令解析。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from .config import (
    DESKTOP_DIR,
    FRONTEND_DIR,
    PHONE_DIR,
)
from .env_utils import 获取代理环境变量, 获取桌面端环境变量
from .process_manager import 读取状态, 更新状态
from .terminal import echo


def 计算文件哈希(path: Path) -> str:
    import hashlib
    content = path.read_bytes()
    return hashlib.md5(content).hexdigest()


def 去重路径列表(candidates: list[Path]) -> list[Path]:
    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        normalized = candidate.expanduser()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(normalized)
    return unique_paths


def _安装应用依赖(
    *,
    source_file: Path,
    hash_key: str,
    label: str,
    install: Callable[[], object],
    skip_if: Callable[[], bool] | None = None,
) -> None:
    if not source_file.exists():
        raise RuntimeError(f"未找到依赖文件: {source_file}")

    current_hash = 计算文件哈希(source_file)
    state = 读取状态()
    saved_hash = state.get("hash", {}).get(hash_key) if state else None

    if skip_if is not None and skip_if() and saved_hash == current_hash:
        return
    if skip_if is None and saved_hash == current_hash:
        return

    if saved_hash is None:
        echo(f"首次安装{label}依赖")
    else:
        echo(f"检测到 {label} {source_file.name} 变化，重新安装依赖")

    install()
    更新状态(hash_values={hash_key: current_hash})
    echo(f"{label}依赖安装完成")


def 确保_node_应用依赖(app_dir: Path, *, hash_key: str, label: str) -> None:
    node_modules = app_dir / "node_modules"
    package_json = app_dir / "package.json"
    npm_cmd = 解析_npm_命令()
    _安装应用依赖(
        source_file=package_json,
        hash_key=hash_key,
        label=label,
        skip_if=lambda: node_modules.exists(),
        install=lambda: subprocess.run([*npm_cmd, "install"], check=True, cwd=app_dir, env=获取代理环境变量()),
    )


def 确保_python_应用依赖(app_dir: Path, *, hash_key: str, label: str) -> None:
    pyproject_toml = app_dir / "pyproject.toml"
    _安装应用依赖(
        source_file=pyproject_toml,
        hash_key=hash_key,
        label=label,
        install=lambda: subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            check=True,
            cwd=app_dir,
        ),
    )


def 确保前端依赖() -> None:
    确保_node_应用依赖(FRONTEND_DIR, hash_key="frontend_package", label="前端")


def 确保手机端依赖() -> None:
    确保_node_应用依赖(PHONE_DIR, hash_key="phone_package", label="手机端")


def 确保手机端_web资源() -> None:
    index_html = PHONE_DIR / "dist" / "index.html"
    if index_html.exists():
        return

    echo("未检测到手机端 Web 资源，正在构建 apps/phone/dist")
    npm_cmd = 解析_npm_命令()
    subprocess.run([*npm_cmd, "run", "build"], check=True, cwd=PHONE_DIR, env=获取代理环境变量())


def 确保桌面端依赖() -> None:
    node_modules = DESKTOP_DIR / "node_modules"
    package_json = DESKTOP_DIR / "package.json"
    npm_cmd = 解析_npm_命令()
    _安装应用依赖(
        source_file=package_json,
        hash_key="desktop_package",
        label="桌面端",
        skip_if=lambda: node_modules.exists(),
        install=lambda: subprocess.run(
            [*npm_cmd, "install"],
            check=True,
            cwd=DESKTOP_DIR,
            env=获取桌面端环境变量(),
        ),
    )


def 解析_npm_命令() -> list[str]:
    if os.name == "nt":
        for name in ("npm.cmd", "npm.exe", "npm"):
            path = shutil.which(name)
            if path:
                return [path]
        raise RuntimeError("未找到命令: npm（请确认 Node.js 安装目录已加入 PATH）")
    from .process_manager import 查找命令
    查找命令("npm")
    return ["npm"]


def 解析_cap_命令(app_dir: Path) -> list[str]:
    npm_cmd = 解析_npm_命令()
    try:
        subprocess.run(
            [*npm_cmd, "exec", "--", "cap", "--version"],
            check=True,
            cwd=app_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("未找到命令: cap（请先执行前端依赖安装）") from exc
    return [*npm_cmd, "exec", "--", "cap"]
