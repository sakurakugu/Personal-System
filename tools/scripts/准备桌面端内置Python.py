"""准备桌面端 embedded 模式所需的内置 Python 运行时。"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))

# ruff: noqa: E402
from shared.config import DESKTOP_PYTHON_RUNTIME_DIR, ROOT_DIR
from shared.env_utils import 获取代理环境变量
from shared.terminal import echo

桌面端Python目录 = ROOT_DIR / "apps" / "desktop" / "python"
运行时根目录 = DESKTOP_PYTHON_RUNTIME_DIR / "python"
运行时Python路径 = 运行时根目录 / "python.exe"
缓存目录 = ROOT_DIR / ".cache" / "downloads" / "python-runtime"
默认安装器地址 = "https://www.python.org/ftp/python/3.14.5/python-3.14.5-amd64.exe"
依赖文件列表 = [
    桌面端Python目录 / "ai-media-processor" / "requirements.txt",
    桌面端Python目录 / "image-tools" / "requirements.txt",
    桌面端Python目录 / "minecraft-tool" / "requirements.txt",
]
运行时裁剪目录列表 = [
    运行时根目录 / "Doc",
    运行时根目录 / "include",
    运行时根目录 / "libs",
    运行时根目录 / "Lib" / "idlelib",
    运行时根目录 / "Lib" / "venv",
]
运行时裁剪文件列表 = [
    运行时根目录 / "NEWS.txt",
]
运行时裁剪模式列表 = [
    "*.pyc",
    "*.pyo",
]
NumPy可裁剪目录列表 = [
    运行时根目录 / "Lib" / "site-packages" / "numpy" / "doc",
    运行时根目录 / "Lib" / "site-packages" / "numpy" / "testing",
    运行时根目录 / "Lib" / "site-packages" / "numpy" / "tests",
    运行时根目录 / "Lib" / "site-packages" / "numpy" / "f2py",
]


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="准备桌面端内置 Python 运行时")
    parser.add_argument(
        "--installer-url",
        default=默认安装器地址,
        help="安装器模式使用的 Python 安装器下载地址",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="准备前先清空 apps/desktop/python-runtime",
    )
    parser.add_argument(
        "--trim",
        action="store_true",
        help="执行运行时裁剪，减少体积",
    )
    return parser.parse_args()


def 清理运行时目录() -> None:
    if 运行时根目录.exists():
        shutil.rmtree(运行时根目录)


def 确保运行时目录() -> None:
    DESKTOP_PYTHON_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    运行时根目录.mkdir(parents=True, exist_ok=True)


def 下载文件(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    echo(f"正在下载 Python 安装器: {url}")
    with urllib.request.urlopen(url) as response, output_path.open("wb") as output_file:
        shutil.copyfileobj(response, output_file)
    return output_path


def 从安装器准备运行时(installer_url: str) -> Path:
    installer_name = installer_url.rstrip("/").split("/")[-1] or "python-installer.exe"
    installer_file = 下载文件(installer_url, 缓存目录 / installer_name)
    echo(f"正在静默安装官方 Python 到 {运行时根目录}")
    subprocess.run(
        [
            str(installer_file),
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=0",
            "Include_test=0",
            "SimpleInstall=0",
            f"TargetDir={运行时根目录}",
        ],
        check=True,
        cwd=ROOT_DIR,
        env=获取代理环境变量(dict(os.environ)),
    )
    if not 运行时Python路径.exists():
        raise RuntimeError(f"官方安装器执行完成，但未找到: {运行时Python路径}")
    return 运行时Python路径


def 升级基础工具(runtime_python: Path) -> None:
    echo("正在升级 embedded Python 的 pip / setuptools / wheel")
    subprocess.run(
        [str(runtime_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=True,
        cwd=ROOT_DIR,
        env=获取代理环境变量(),
    )


def 安装桌面端依赖(runtime_python: Path) -> None:
    for requirements_file in 依赖文件列表:
        if not requirements_file.exists():
            raise RuntimeError(f"未找到依赖文件: {requirements_file}")
        echo(f"正在安装依赖: {requirements_file.relative_to(ROOT_DIR)}")
        subprocess.run(
            [str(runtime_python), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            cwd=ROOT_DIR,
            env=获取代理环境变量(),
        )


def 删除目录(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def 删除文件(path: Path) -> None:
    if path.exists():
        path.unlink()


def 计算目录大小(path: Path) -> int:
    total_size = 0
    if not path.exists():
        return 0
    for file in path.rglob("*"):
        if file.is_file():
            total_size += file.stat().st_size
    return total_size


def 格式化大小(size: int) -> str:
    return f"{round(size / 1024 / 1024, 2)} MB"


def 裁剪运行时缓存与元数据() -> None:
    for cache_dir in 运行时根目录.rglob("__pycache__"):
        删除目录(cache_dir)

    for pattern in 运行时裁剪模式列表:
        for compiled_file in 运行时根目录.rglob(pattern):
            删除文件(compiled_file)


def 裁剪运行时() -> None:
    if not 运行时根目录.exists():
        raise RuntimeError(f"运行时目录不存在，无法裁剪: {运行时根目录}")

    trim_before = 计算目录大小(运行时根目录)
    echo("正在裁剪 embedded Python 运行时")

    for directory in 运行时裁剪目录列表:
        删除目录(directory)

    for directory in NumPy可裁剪目录列表:
        删除目录(directory)

    for file in 运行时裁剪文件列表:
        删除文件(file)

    裁剪运行时缓存与元数据()

    trim_after = 计算目录大小(运行时根目录)
    saved_size = max(trim_before - trim_after, 0)
    print(f"  裁剪前: {格式化大小(trim_before)}")
    print(f"  裁剪后: {格式化大小(trim_after)}")
    print(f"  节省体积: {格式化大小(saved_size)}")


def 输出结果(runtime_python: Path) -> None:
    print("")
    echo("桌面端 embedded Python 运行时准备完成")
    print("  准备模式: installer")
    print(f"  运行时目录: {DESKTOP_PYTHON_RUNTIME_DIR}")
    print(f"  Python 路径: {runtime_python}")


def main() -> int:
    args = 解析参数()

    if args.reset:
        清理运行时目录()

    确保运行时目录()
    runtime_python = 从安装器准备运行时(args.installer_url)

    升级基础工具(runtime_python)
    安装桌面端依赖(runtime_python)
    if args.trim:
        裁剪运行时()
    else:
        echo("默认保留完整运行时，跳过裁剪")
    输出结果(runtime_python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
