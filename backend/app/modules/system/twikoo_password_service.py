"""Twikoo 管理密码运维服务。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.models import SystemSetting
from app.modules.system.schemas import TwikooPasswordStateRead
from app.shared.kernel.config import settings

TWIKOO_LAST_RESET_PASSWORD_SETTING = "twikoo_last_reset_password"


class TwikooPasswordManageError(RuntimeError):
    """Twikoo 管理密码运维异常。"""


def _计算_twikoo_管理密码存储哈希(password: str) -> str:
    """计算 Twikoo 自托管场景使用的 ADMIN_PASS 存储值。"""
    一次哈希 = hashlib.md5(password.encode("utf-8")).hexdigest()
    return hashlib.md5(一次哈希.encode("utf-8")).hexdigest()


async def _set_str_setting(db: AsyncSession, key: str, value: str) -> None:
    """写入字符串设置。"""
    setting = await db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, bool_value=None, str_value=value)
        db.add(setting)
    else:
        setting.str_value = value
        setting.bool_value = None
    await db.flush()


def _可直接访问数据目录() -> bool:
    """判断当前运行环境是否可直接访问 Twikoo 数据目录。"""
    return Path(settings.TWIKOO_DATA_DIR).exists()


def _可使用_docker_cli() -> bool:
    """判断当前环境是否可调用 Docker CLI。"""
    return bool(settings.TWIKOO_CONTAINER_NAME) and shutil.which("docker") is not None


def _可使用_docker_socket() -> bool:
    """判断当前环境是否可通过 Docker Socket 重启容器。"""
    return bool(settings.TWIKOO_CONTAINER_NAME) and Path(settings.DOCKER_SOCKET_PATH).exists()


def 获取_twikoo_密码运维状态说明() -> tuple[bool, str]:
    """返回 Twikoo 密码运维能力说明。"""
    可写数据 = _可直接访问数据目录() or _可使用_docker_cli()
    可重启服务 = _可使用_docker_socket() or _可使用_docker_cli()
    if 可写数据 and 可重启服务:
        return True, "可直接在此页面重置 Twikoo 管理密码，并保存最近一次重置备忘。"

    原因列表: list[str] = []
    if not 可写数据:
        原因列表.append("当前环境无法访问 Twikoo 数据文件")
    if not 可重启服务:
        原因列表.append("当前环境无法重启 Twikoo 服务")
    return False, "；".join(原因列表)


def _读取_json_文件(path: Path, *, 默认值: Any) -> Any:
    """读取 JSON 文件，不存在或为空时返回默认值。"""
    if not path.exists() or path.stat().st_size == 0:
        return 默认值
    return json.loads(path.read_text(encoding="utf-8"))


def _原子写入_json_文件(path: Path, payload: Any) -> None:
    """原子写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    临时文件 = path.with_name(f"{path.name}.tmp")
    临时文件.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    临时文件.replace(path)


def _解析_config_分片路径(db_meta: dict[str, Any], 数据目录: Path) -> tuple[dict[str, Any], Path]:
    """解析 config collection 对应的分片文件路径。"""
    collections = db_meta.get("collections")
    if not isinstance(collections, list):
        raise TwikooPasswordManageError("Twikoo 数据文件结构异常，缺少 collections")

    for index, collection in enumerate(collections):
        if isinstance(collection, dict) and collection.get("name") == "config":
            return collection, 数据目录 / f"db.json.{index}"

    raise TwikooPasswordManageError("Twikoo 数据文件结构异常，未找到 config collection")


def _构造_config_记录(旧记录: dict[str, Any] | None, 管理密码哈希: str) -> dict[str, Any]:
    """构造更新后的 config 记录。"""
    当前毫秒 = int(time.time() * 1000)
    if 旧记录:
        新记录 = dict(旧记录)
        旧元数据 = 新记录.get("meta")
        元数据 = dict(旧元数据) if isinstance(旧元数据, dict) else {}
        元数据["created"] = int(元数据.get("created", 当前毫秒))
        元数据["updated"] = 当前毫秒
        元数据["revision"] = int(元数据.get("revision", -1)) + 1
        元数据["version"] = int(元数据.get("version", 0))
    else:
        新记录 = {}
        元数据 = {
            "revision": 0,
            "created": 当前毫秒,
            "updated": 当前毫秒,
            "version": 0,
        }

    if not isinstance(新记录.get("$loki"), int):
        新记录["$loki"] = 1
    新记录["meta"] = 元数据
    新记录["ADMIN_PASS"] = 管理密码哈希
    return 新记录


def _写入_twikoo_数据目录(数据目录: Path, 管理密码哈希: str) -> None:
    """直接写入 Twikoo 数据目录中的密码哈希。"""
    db_meta_path = 数据目录 / "db.json"
    db_meta = _读取_json_文件(db_meta_path, 默认值=None)
    if not isinstance(db_meta, dict):
        raise TwikooPasswordManageError("Twikoo 主数据文件不存在或内容异常")

    config_collection, config_path = _解析_config_分片路径(db_meta, 数据目录)
    旧记录 = _读取_json_文件(config_path, 默认值=None)
    if 旧记录 is not None and not isinstance(旧记录, dict):
        raise TwikooPasswordManageError("Twikoo 配置分片内容异常")

    新记录 = _构造_config_记录(旧记录, 管理密码哈希)
    _原子写入_json_文件(config_path, 新记录)

    config_collection["maxId"] = max(int(config_collection.get("maxId") or 0), int(新记录["$loki"]))
    config_collection["dirty"] = True
    _原子写入_json_文件(db_meta_path, db_meta)


def _执行_docker_cli命令(args: list[str], *, input_text: str | None = None) -> str:
    """执行 Docker CLI 并返回标准输出。"""
    try:
        result = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except FileNotFoundError as exc:
        raise TwikooPasswordManageError("当前环境未安装 Docker CLI") from exc
    except subprocess.CalledProcessError as exc:
        输出 = (exc.stderr or exc.stdout or "").strip()
        raise TwikooPasswordManageError(输出 or "Docker 命令执行失败") from exc
    return result.stdout


def _从容器读取_json(容器内路径: str, *, 默认值: Any) -> Any:
    """通过 Docker CLI 从 Twikoo 容器读取 JSON 文件。"""
    shell_script = (
        f"if [ -s {json.dumps(容器内路径)} ]; then "
        f"cat {json.dumps(容器内路径)}; "
        "fi"
    )
    输出 = _执行_docker_cli命令(
        ["docker", "exec", settings.TWIKOO_CONTAINER_NAME, "sh", "-lc", shell_script],
    ).strip()
    if not 输出:
        return 默认值
    return json.loads(输出)


def _写入容器内_json(容器内路径: str, payload: Any) -> None:
    """通过 Docker CLI 向 Twikoo 容器写入 JSON 文件。"""
    内容 = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    _执行_docker_cli命令(
        [
            "docker",
            "exec",
            "-i",
            settings.TWIKOO_CONTAINER_NAME,
            "sh",
            "-lc",
            f"cat > {json.dumps(容器内路径)}",
        ],
        input_text=内容,
    )


def _通过_docker_cli_写入密码(管理密码哈希: str) -> None:
    """通过 Docker CLI 直接写入 Twikoo 容器内的密码哈希。"""
    容器数据目录 = settings.TWIKOO_CONTAINER_DATA_DIR.rstrip("/")
    db_meta_path = f"{容器数据目录}/db.json"
    db_meta = _从容器读取_json(db_meta_path, 默认值=None)
    if not isinstance(db_meta, dict):
        raise TwikooPasswordManageError("Twikoo 主数据文件不存在或内容异常")

    collections = db_meta.get("collections")
    if not isinstance(collections, list):
        raise TwikooPasswordManageError("Twikoo 数据文件结构异常，缺少 collections")

    config_collection: dict[str, Any] | None = None
    config_index = -1
    for index, collection in enumerate(collections):
        if isinstance(collection, dict) and collection.get("name") == "config":
            config_collection = collection
            config_index = index
            break
    if config_collection is None or config_index < 0:
        raise TwikooPasswordManageError("Twikoo 数据文件结构异常，未找到 config collection")

    config_path = f"{容器数据目录}/db.json.{config_index}"
    旧记录 = _从容器读取_json(config_path, 默认值=None)
    if 旧记录 is not None and not isinstance(旧记录, dict):
        raise TwikooPasswordManageError("Twikoo 配置分片内容异常")

    新记录 = _构造_config_记录(旧记录, 管理密码哈希)
    _写入容器内_json(config_path, 新记录)

    config_collection["maxId"] = max(int(config_collection.get("maxId") or 0), int(新记录["$loki"]))
    config_collection["dirty"] = True
    _写入容器内_json(db_meta_path, db_meta)


async def _重启_twikoo_容器() -> None:
    """重启 Twikoo 容器，使新密码立刻生效。"""
    if _可使用_docker_socket():
        transport = httpx.AsyncHTTPTransport(uds=settings.DOCKER_SOCKET_PATH)
        async with httpx.AsyncClient(
            base_url="http://docker",
            transport=transport,
            timeout=15.0,
        ) as client:
            response = await client.post(
                f"/containers/{quote(settings.TWIKOO_CONTAINER_NAME, safe='')}/restart",
                params={"t": 10},
            )
            if response.status_code != 204:
                raise TwikooPasswordManageError(f"重启 Twikoo 失败：{response.text or response.status_code}")
        await asyncio.sleep(1.0)
        return

    if _可使用_docker_cli():
        await asyncio.to_thread(
            _执行_docker_cli命令,
            ["docker", "restart", settings.TWIKOO_CONTAINER_NAME],
        )
        await asyncio.sleep(1.0)
        return

    raise TwikooPasswordManageError("当前环境无法重启 Twikoo 服务")


async def get_twikoo_password_state(db: AsyncSession) -> TwikooPasswordStateRead:
    """读取 Twikoo 密码运维状态与备忘。"""
    可用, 说明 = 获取_twikoo_密码运维状态说明()
    setting = await db.get(SystemSetting, TWIKOO_LAST_RESET_PASSWORD_SETTING)
    return TwikooPasswordStateRead(
        available=可用,
        detail=说明,
        last_reset_password=setting.str_value if setting is not None else None,
        last_reset_at=setting.updated_at if setting is not None else None,
    )


async def reset_twikoo_admin_password(db: AsyncSession, password: str) -> TwikooPasswordStateRead:
    """重置 Twikoo 管理密码并保存最近一次备忘。"""
    新密码 = password.strip()
    if len(新密码) < 6:
        raise TwikooPasswordManageError("Twikoo 管理密码长度不能少于 6 位")

    可用, 说明 = 获取_twikoo_密码运维状态说明()
    if not 可用:
        raise TwikooPasswordManageError(说明)

    管理密码哈希 = _计算_twikoo_管理密码存储哈希(新密码)

    if _可直接访问数据目录():
        await asyncio.to_thread(_写入_twikoo_数据目录, Path(settings.TWIKOO_DATA_DIR), 管理密码哈希)
    elif _可使用_docker_cli():
        await asyncio.to_thread(_通过_docker_cli_写入密码, 管理密码哈希)
    else:
        raise TwikooPasswordManageError("当前环境无法访问 Twikoo 数据文件")

    await _重启_twikoo_容器()
    await _set_str_setting(db, TWIKOO_LAST_RESET_PASSWORD_SETTING, 新密码)
    return await get_twikoo_password_state(db)
