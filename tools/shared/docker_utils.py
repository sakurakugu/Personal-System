"""Docker / Docker Compose 相关工具。"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .config import COMPOSE_FILE, CLOUD_ENV_EXAMPLE_FILE, CLOUD_ENV_FILE, ROOT_DIR
from .process_manager import 查找命令
from .terminal import echo, 开始单行状态, 结束单行状态


def 组合环境变量参数() -> list[str]:
    env_file = CLOUD_ENV_FILE if CLOUD_ENV_FILE.exists() else CLOUD_ENV_EXAMPLE_FILE
    return ["--env-file", str(env_file)]


def 组合Compose命令(*args: str) -> list[str]:
    return ["docker", "compose", "--file", str(COMPOSE_FILE), *组合环境变量参数(), *args]


def 清理Docker构建缓存(*, 保留时长: str = "168h") -> None:
    echo(f"清理 {保留时长} 前未使用的 Docker 构建缓存")
    result = subprocess.run(
        ["docker", "builder", "prune", "--force", "--filter", f"until={保留时长}"],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if stdout:
        print(stdout)
    if result.returncode != 0:
        echo("Docker 构建缓存清理失败，已跳过")
        if stderr:
            print(stderr)


def 启动DockerDesktop() -> None:
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
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def 检查Docker运行() -> None:
    if docker_是否运行():
        return
    启动DockerDesktop()
    echo("等待 Docker 启动...")
    for _ in range(30):
        if docker_是否运行():
            echo("Docker 已启动")
            return
        time.sleep(2)
    raise RuntimeError("Docker 启动超时，请手动检查 Docker Desktop。")


def 等待DockerCompose服务就绪(service: str, timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    last_status = "unknown"
    while time.monotonic() < deadline:
        result = subprocess.run(
            组合Compose命令("ps", "-q", service),
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        container_id = result.stdout.strip()
        if not container_id:
            time.sleep(1)
            continue

        inspect = subprocess.run(
            [
                "docker", "inspect", "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                container_id,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        status = inspect.stdout.strip()
        if status:
            last_status = status

        if status in {"healthy", "running"}:
            return
        time.sleep(1)

    raise RuntimeError(f"等待服务就绪超时: {service}（最后状态: {last_status}）")


def 镜像存在(image: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def 验证Docker镜像(images: list[str]) -> None:
    宽度 = max(len(f"检查镜像: {image}") for image in images)
    for image in images:
        msg = f"检查镜像: {image}"
        开始单行状态(msg, 宽度=宽度)
        if 镜像存在(image):
            结束单行状态(msg, 宽度=宽度, 结果="（已存在）")
            continue

        result = subprocess.run(
            ["docker", "pull", image],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            结束单行状态(msg, 宽度=宽度, 结果="（拉取失败）", 成功=False)
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                "无法拉取 Docker 镜像。\n"
                f"镜像: {image}\n"
                f"错误: {stderr}"
            )
        结束单行状态(msg, 宽度=宽度, 结果="（已拉取）")


def 解析DockerCompose镜像(compose_path: Path) -> list[str]:
    import yaml  # type: ignore[import-untyped]
    content = compose_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    images = []
    services = data.get("services", {})
    for service_config in services.values():
        image = service_config.get("image")
        if image:
            images.append(image)
    return images


def 验证DockerCompose镜像(compose_path: Path) -> None:
    echo(f"解析 compose 文件: {compose_path}")
    images = 解析DockerCompose镜像(compose_path)
    if not images:
        echo("未找到需要拉取的镜像（所有服务均为 build 模式）")
        return
    echo(f"发现 {len(images)} 个镜像需要验证")
    查找命令("docker")
    检查Docker运行()
    echo("开始验证镜像...")
    验证Docker镜像(images)
    echo("所有镜像验证完成")
