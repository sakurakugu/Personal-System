"""准备桌面端 embedded 模式所需的内置 Python 运行时。"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
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
默认嵌入包地址 = "https://www.python.org/ftp/python/3.14.5/python-3.14.5-embed-amd64.zip"
默认GetPip地址 = "https://bootstrap.pypa.io/get-pip.py"
依赖文件列表 = [
    桌面端Python目录 / "ai-media-processor" / "requirements.txt",
    桌面端Python目录 / "image-tools" / "requirements.txt",
    桌面端Python目录 / "minecraft-tool" / "requirements.txt",
]


def 解析参数() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="准备桌面端内置 Python 运行时")
    parser.add_argument(
        "--embed-url",
        default=默认嵌入包地址,
        help="embedded 模式使用的 Python embeddable zip 下载地址",
    )
    parser.add_argument(
        "--get-pip-url",
        default=默认GetPip地址,
        help="安装 pip 使用的 get-pip.py 下载地址",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="准备前先清空 apps/desktop/python-runtime",
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
    echo(f"正在下载文件: {url}")
    with urllib.request.urlopen(url) as response, output_path.open("wb") as output_file:
        shutil.copyfileobj(response, output_file)
    return output_path


def 启用Site模块() -> None:
    pth_files = sorted(运行时根目录.glob("python*._pth"))
    if not pth_files:
        raise RuntimeError(f"embedded Python 缺少 ._pth 文件: {运行时根目录}")

    pth_file = pth_files[0]
    lines = pth_file.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    found_import_site = False

    for line in lines:
        stripped = line.strip()
        if stripped == "#import site":
            updated_lines.append("import site")
            found_import_site = True
            continue
        if stripped == "import site":
            found_import_site = True
        updated_lines.append(line)

    if not found_import_site:
        updated_lines.append("import site")

    pth_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def 从嵌入包准备运行时(embed_url: str) -> Path:
    embed_name = embed_url.rstrip("/").split("/")[-1] or "python-embed.zip"
    embed_file = 下载文件(embed_url, 缓存目录 / embed_name)
    if 运行时根目录.exists():
        shutil.rmtree(运行时根目录)
    运行时根目录.mkdir(parents=True, exist_ok=True)
    echo(f"正在解压 embedded Python 到 {运行时根目录}")
    with zipfile.ZipFile(embed_file) as zip_file:
        zip_file.extractall(运行时根目录)
    启用Site模块()
    if not 运行时Python路径.exists():
        raise RuntimeError(f"embedded Python 解压完成，但未找到: {运行时Python路径}")
    return 运行时Python路径


def 安装Pip(runtime_python: Path, get_pip_url: str) -> None:
    get_pip_file = 下载文件(get_pip_url, 缓存目录 / "get-pip.py")
    echo("正在为 embedded Python 安装 pip")
    subprocess.run(
        [str(runtime_python), str(get_pip_file)],
        check=True,
        cwd=ROOT_DIR,
        env=获取代理环境变量(dict(os.environ)),
    )


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


def 输出结果(runtime_python: Path) -> None:
    print("")
    echo("桌面端 embedded Python 运行时准备完成")
    print("  准备模式: embedded zip")
    print(f"  运行时目录: {DESKTOP_PYTHON_RUNTIME_DIR}")
    print(f"  Python 路径: {runtime_python}")


def main() -> int:
    args = 解析参数()

    if args.reset:
        清理运行时目录()

    确保运行时目录()
    runtime_python = 从嵌入包准备运行时(args.embed_url)
    安装Pip(runtime_python, args.get_pip_url)
    升级基础工具(runtime_python)
    安装桌面端依赖(runtime_python)
    输出结果(runtime_python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
