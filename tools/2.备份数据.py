"""项目数据备份脚本。

当前脚本用于在仓库内生成一份可追溯的本地备份目录，默认覆盖：

- PostgreSQL
- MinIO
- Twikoo

如需附带 Redis，可显式传入 `--with-redis`。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

仓库根目录 = Path(__file__).resolve().parent.parent
云端应用目录 = 仓库根目录 / "apps" / "cloud"
云端_env_文件 = 云端应用目录 / ".env"
云端_env_示例文件 = 云端应用目录 / ".env.example"
云端_compose_文件 = 云端应用目录 / "docker-compose.yml"
默认备份目录 = 仓库根目录 / "backups"
默认组件列表 = ("postgres", "minio", "twikoo")
可选组件列表 = ("postgres", "minio", "twikoo", "redis")


class 备份异常(RuntimeError):
    """备份流程异常。"""


@dataclass(slots=True)
class 备份文件信息:
    """单个备份产物的元信息。"""

    组件: str
    文件名: str
    大小字节: int
    sha256: str


def 格式化文件大小(size_bytes: int) -> str:
    """优先显示更易读的单位，同时保留原始字节数。"""
    units = ("bytes", "KB", "MB", "GB", "TB")
    value = float(size_bytes)
    unit = units[0]
    for current_unit in units:
        unit = current_unit
        if current_unit == units[-1] or value < 1024:
            break
        value /= 1024

    if unit == "bytes":
        readable = f"{size_bytes} bytes"
    elif value >= 100:
        readable = f"{value:.0f} {unit}"
    elif value >= 10:
        readable = f"{value:.1f} {unit}"
    else:
        readable = f"{value:.2f} {unit}"
    return f"\033[32m{readable} | {size_bytes} bytes\033[0m"


def 输出(message: str) -> None:
    """统一输出日志。"""
    print(message, flush=True)


def 解析环境变量文件(path: Path) -> dict[str, str]:
    """读取 `.env` 文件。"""
    if not path.exists():
        return {}

    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key.strip()] = value
    return result


def 获取环境变量文件路径() -> Path:
    """返回当前应使用的云端应用 env 文件。"""
    if 云端_env_文件.exists():
        return 云端_env_文件
    return 云端_env_示例文件


def 构造Compose命令(*args: str) -> list[str]:
    """构造指向 apps/cloud 的 docker compose 命令。"""
    return [
        "docker",
        "compose",
        "--file",
        str(云端_compose_文件),
        "--env-file",
        str(获取环境变量文件路径()),
        *args,
    ]


def 运行命令(
    args: list[str],
    *,
    cwd: Path = 仓库根目录,
    env: dict[str, str] | None = None,
    text: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """执行普通命令。"""
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
            check=True,
        )
    except FileNotFoundError as exc:
        raise 备份异常(f"未找到命令：{args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        原始输出 = exc.stderr if exc.stderr is not None else exc.stdout
        if isinstance(原始输出, bytes):
            stderr = 原始输出.decode("utf-8", errors="ignore").strip()
        else:
            stderr = (原始输出 or "").strip()
        raise 备份异常(stderr or f"命令执行失败：{' '.join(args)}") from exc


def 运行文本命令(
    args: list[str],
    *,
    cwd: Path = 仓库根目录,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """执行文本命令，避免在调用侧处理 bytes 联合类型。"""
    result = 运行命令(args, cwd=cwd, env=env, text=True)
    if not isinstance(result.stdout, str) or not isinstance(result.stderr, str):
        raise 备份异常("命令输出类型异常")
    return result


def 检查DockerCLI() -> None:
    """确认本机可使用 Docker。"""
    if shutil.which("docker") is None:
        raise 备份异常("当前环境未安装 Docker CLI，无法执行备份")

    try:
        运行文本命令(["docker", "compose", "version"])
    except 备份异常 as exc:
        raise 备份异常(f"Docker Compose 不可用：{exc}") from exc

    try:
        运行文本命令(["docker", "info"])
    except 备份异常 as exc:
        raise 备份异常(f"Docker 当前不可连接，请先启动 Docker：{exc}") from exc


def 获取运行中的服务容器(service: str) -> str:
    """返回运行中的容器 ID。"""
    result = 运行文本命令(构造Compose命令("ps", "-q", service))
    容器ID = result.stdout.strip()
    if not 容器ID:
        raise 备份异常(f"服务 `{service}` 未运行，无法备份")
    return 容器ID


def 流式写入命令输出(args: list[str], output_path: Path) -> None:
    """将命令标准输出直接写入文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("wb") as file_handle:
            process = subprocess.Popen(
                args,
                cwd=仓库根目录,
                stdout=file_handle,
                stderr=subprocess.PIPE,
            )
            _, stderr = process.communicate()
    except FileNotFoundError as exc:
        raise 备份异常(f"未找到命令：{args[0]}") from exc

    if process.returncode != 0:
        output_path.unlink(missing_ok=True)
        message = (stderr or b"").decode("utf-8", errors="ignore").strip()
        raise 备份异常(message or f"命令执行失败：{' '.join(args)}")


def 从容器复制目录(容器ID: str, 容器内目录: str, 本地目录: Path) -> None:
    """把容器目录复制到本地目录。"""
    本地目录.mkdir(parents=True, exist_ok=True)
    运行文本命令(["docker", "cp", f"{容器ID}:{容器内目录.rstrip('/')}/.", str(本地目录)])


def 打包本地目录(source_dir: Path, output_path: Path) -> None:
    """将本地目录压缩为 tar.gz。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as archive:
        for child in sorted(source_dir.iterdir(), key=lambda item: item.name):
            archive.add(child, arcname=child.name)


def 导出容器目录(
    *,
    service: str,
    组件名: str,
    容器内目录: str,
    输出文件名: str,
    backup_dir: Path,
    预处理命令: str | None = None,
) -> 备份文件信息:
    """复制容器目录到本地后再压缩归档。"""
    容器ID = 获取运行中的服务容器(service)
    output_path = backup_dir / 输出文件名
    输出(f"开始备份 {组件名} ...")
    if 预处理命令:
        运行文本命令(构造Compose命令("exec", "-T", service, "sh", "-lc", 预处理命令))

    with tempfile.TemporaryDirectory(prefix=f"backup-{service}-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        copied_dir = temp_dir / "data"
        从容器复制目录(容器ID, 容器内目录, copied_dir)
        打包本地目录(copied_dir, output_path)

    return 记录备份文件(service, output_path)


def 计算文件SHA256(path: Path) -> str:
    """计算文件摘要。"""
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def 记录备份文件(组件: str, path: Path) -> 备份文件信息:
    """构造备份文件元信息。"""
    return 备份文件信息(
        组件=组件,
        文件名=path.name,
        大小字节=path.stat().st_size,
        sha256=计算文件SHA256(path),
    )


def 解析组件(raw: str) -> tuple[str, ...]:
    """解析命令行传入的组件列表。"""
    items = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("组件列表不能为空")

    非法组件 = [item for item in items if item not in 可选组件列表]
    if 非法组件:
        raise argparse.ArgumentTypeError(f"存在不支持的组件：{', '.join(非法组件)}")

    去重后组件: list[str] = []
    for item in items:
        if item not in 去重后组件:
            去重后组件.append(item)
    return tuple(去重后组件)


def 生成备份目录名(custom_name: str | None) -> str:
    """生成当前备份目录名。"""
    if custom_name:
        return custom_name.strip()
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def 校验备份目录名(name: str) -> str:
    """限制目录名字符，避免生成不可读路径。"""
    value = name.strip()
    if not value:
        raise 备份异常("备份目录名不能为空")

    forbidden_chars = set('/\\:*?"<>|')
    if any(char in forbidden_chars for char in value):
        raise 备份异常("备份目录名包含非法字符")
    return value


def 导出Postgres(backup_dir: Path) -> 备份文件信息:
    """导出 PostgreSQL 自定义格式备份。"""
    获取运行中的服务容器("postgres")
    output_path = backup_dir / "postgres.dump"
    输出("开始备份 PostgreSQL ...")
    流式写入命令输出(
        构造Compose命令(
            "exec",
            "-T",
            "postgres",
            "sh",
            "-lc",
            'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --compress=6 --clean --if-exists --no-owner --no-privileges',
        ),
        output_path,
    )
    return 记录备份文件("postgres", output_path)


def 导出Minio(backup_dir: Path) -> 备份文件信息:
    """导出 MinIO 数据目录。"""
    return 导出容器目录(
        service="minio",
        组件名="MinIO",
        容器内目录="/data",
        输出文件名="minio-data.tar.gz",
        backup_dir=backup_dir,
    )


def 导出Twikoo(backup_dir: Path) -> 备份文件信息:
    """导出 Twikoo 数据目录。"""
    return 导出容器目录(
        service="twikoo",
        组件名="Twikoo",
        容器内目录="/app/data",
        输出文件名="twikoo-data.tar.gz",
        backup_dir=backup_dir,
    )


def 导出Redis(backup_dir: Path) -> 备份文件信息:
    """导出 Redis 数据目录。"""
    return 导出容器目录(
        service="redis",
        组件名="Redis",
        容器内目录="/data",
        输出文件名="redis-data.tar.gz",
        backup_dir=backup_dir,
        预处理命令="redis-cli SAVE >/dev/null",
    )


def 写入清单(
    backup_dir: Path,
    *,
    components: Iterable[str],
    文件列表: list[备份文件信息],
) -> None:
    """生成本次备份的清单文件。"""
    env_map = 解析环境变量文件(获取环境变量文件路径())
    payload = {
        "created_at": datetime.now().astimezone().isoformat(),
        "project_root": str(仓库根目录),
        "backup_dir": str(backup_dir),
        "components": list(components),
        "docker_compose_file": str(云端_compose_文件),
        "database": {
            "name": env_map.get("POSTGRES_DB", ""),
            "user": env_map.get("POSTGRES_USER", ""),
            "host_port": "127.0.0.1:15432",
        },
        "files": [
            {
                "component": item.组件,
                "filename": item.文件名,
                "size_bytes": item.大小字节,
                "sha256": item.sha256,
            }
            for item in 文件列表
        ],
    }
    (backup_dir / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def 从清单计算总大小(manifest: dict[str, object]) -> int:
    """根据清单中的文件列表汇总总大小。"""
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        return 0

    total_size = 0
    for item in raw_files:
        if not isinstance(item, dict):
            continue
        size_value = item.get("size_bytes")
        if isinstance(size_value, int):
            total_size += size_value
    return total_size


def 从清单提取文件列表(manifest: dict[str, object]) -> list[dict[str, object]]:
    """读取清单中的文件条目。"""
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        return []
    return [item for item in raw_files if isinstance(item, dict)]


def 列出备份目录(root: Path) -> list[Path]:
    """按时间倒序列出已有备份。"""
    if not root.exists():
        return []
    return sorted(
        [item for item in root.iterdir() if item.is_dir()],
        key=lambda item: item.name,
        reverse=True,
    )


def 清理旧备份(root: Path, keep: int) -> list[Path]:
    """按目录名保留最新若干份备份。"""
    if keep <= 0:
        return []

    backups = 列出备份目录(root)
    if len(backups) <= keep:
        return []

    removed: list[Path] = []
    for target in backups[keep:]:
        shutil.rmtree(target)
        removed.append(target)
    return removed


def 执行创建备份(args: argparse.Namespace) -> int:
    """执行 create 子命令。"""
    检查DockerCLI()

    组件列表 = list(args.components)
    if args.with_redis and "redis" not in 组件列表:
        组件列表.append("redis")

    backup_root = Path(args.output_dir).resolve()
    backup_root.mkdir(parents=True, exist_ok=True)

    backup_name = 校验备份目录名(生成备份目录名(args.name))
    backup_dir = backup_root / backup_name
    if backup_dir.exists():
        raise 备份异常(f"备份目录已存在：{backup_dir}")

    backup_dir.mkdir(parents=True, exist_ok=False)
    文件列表: list[备份文件信息] = []

    try:
        if "postgres" in 组件列表:
            文件列表.append(导出Postgres(backup_dir))
        if "minio" in 组件列表:
            文件列表.append(导出Minio(backup_dir))
        if "twikoo" in 组件列表:
            文件列表.append(导出Twikoo(backup_dir))
        if "redis" in 组件列表:
            文件列表.append(导出Redis(backup_dir))
        写入清单(backup_dir, components=组件列表, 文件列表=文件列表)
    except Exception:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise

    输出(f"备份完成：{backup_dir}")
    for item in 文件列表:
        输出(f"- {item.组件}: {item.文件名} {格式化文件大小(item.大小字节)}")

    removed = 清理旧备份(backup_root, args.keep)
    for path in removed:
        输出(f"已清理旧备份：{path}")
    return 0


def 执行列出备份(args: argparse.Namespace) -> int:
    """执行 list 子命令。"""
    backup_root = Path(args.output_dir).resolve()
    backups = 列出备份目录(backup_root)
    if not backups:
        输出(f"当前没有备份目录：{backup_root}")
        return 0

    输出(f"备份根目录：{backup_root}")
    for item in backups:
        manifest_path = item / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                created_at = manifest.get("created_at", "未知时间")
                components = ",".join(manifest.get("components", [])) or "未知组件"
                total_size = 从清单计算总大小(manifest)
                size_text = 格式化文件大小(total_size) if total_size > 0 else "大小未知"
                输出(f"- {item.name} | {created_at} | {components} | {size_text}")
                if args.verbose:
                    for file_item in 从清单提取文件列表(manifest):
                        component = str(file_item.get("component", "未知组件"))
                        filename = str(file_item.get("filename", "未知文件"))
                        size_value = file_item.get("size_bytes", 0)
                        size_bytes = size_value if isinstance(size_value, int) else 0
                        输出(f"  - {component}: {filename} | {格式化文件大小(size_bytes)}")
                continue
            except json.JSONDecodeError:
                pass
        输出(f"- {item.name}")
    return 0


def 执行清理备份(args: argparse.Namespace) -> int:
    """执行 prune 子命令。"""
    backup_root = Path(args.output_dir).resolve()
    if args.keep < 0:
        raise 备份异常("--keep 不能小于 0")

    backups = 列出备份目录(backup_root)
    if not backups:
        输出(f"当前没有备份目录：{backup_root}")
        return 0

    removed = 清理旧备份(backup_root, args.keep)
    if not removed:
        输出(f"无需清理，当前备份数量 {len(backups)}，保留数量 {args.keep}")
        return 0

    输出(f"已清理 {len(removed)} 份旧备份，当前保留最新 {args.keep} 份：")
    for path in removed:
        输出(f"- {path.name}")
    return 0


def 构造参数解析器() -> argparse.ArgumentParser:
    """创建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(description="项目数据备份工具")
    subparsers = parser.add_subparsers(dest="action")

    create_parser = subparsers.add_parser("create", help="创建备份")
    create_parser.add_argument(
        "--output-dir",
        default=str(默认备份目录),
        help="备份根目录，默认位于仓库根目录下的 backups",
    )
    create_parser.add_argument(
        "--components",
        type=解析组件,
        default=默认组件列表,
        help="要备份的组件，逗号分隔：postgres,minio,twikoo,redis",
    )
    create_parser.add_argument(
        "--with-redis",
        action="store_true",
        help="在默认组件基础上附带 Redis 备份",
    )
    create_parser.add_argument(
        "--keep",
        type=int,
        default=0,
        help="备份完成后仅保留最新 N 份，0 表示不清理",
    )
    create_parser.add_argument(
        "--name",
        help="自定义本次备份目录名，默认按时间戳生成",
    )

    list_parser = subparsers.add_parser("list", help="列出已有备份")
    list_parser.add_argument(
        "--output-dir",
        default=str(默认备份目录),
        help="备份根目录，默认位于仓库根目录下的 backups",
    )
    list_parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示每份备份中的文件明细",
    )

    prune_parser = subparsers.add_parser("prune", help="清理旧备份")
    prune_parser.add_argument(
        "--output-dir",
        default=str(默认备份目录),
        help="备份根目录，默认位于仓库根目录下的 backups",
    )
    prune_parser.add_argument(
        "--keep",
        type=int,
        required=True,
        help="仅保留最新 N 份备份",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """脚本入口。"""
    parser = 构造参数解析器()
    args = parser.parse_args(argv)
    action = args.action or "create"

    if action == "create":
        return 执行创建备份(args)
    if action == "list":
        return 执行列出备份(args)
    if action == "prune":
        return 执行清理备份(args)

    parser.error(f"不支持的操作：{action}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except 备份异常 as exc:
        输出(f"备份失败：{exc}")
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        输出("已取消备份")
        raise SystemExit(130)
