from __future__ import annotations

import json
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from .models import 图片资源记录

资源根目录 = Path(gettempdir()) / "personal-system-image-tools"


def 确保资源目录() -> Path:
    资源根目录.mkdir(parents=True, exist_ok=True)
    return 资源根目录


def 创建资源标识() -> str:
    return uuid4().hex


def 获取资源元数据路径(resource_id: str) -> Path:
    return 确保资源目录() / f"{resource_id}.json"


def 获取资源预览路径(resource_id: str) -> Path:
    return 确保资源目录() / f"{resource_id}.png"


def 保存资源记录(record: 图片资源记录) -> None:
    payload = {
        "id": record.id,
        "source_path": record.source_path,
        "preview_path": record.preview_path,
        "原始文件名": record.原始文件名,
        "原始MimeType": record.原始MimeType,
        "文件大小": record.文件大小,
        "宽度": record.宽度,
        "高度": record.高度,
        "是否动画": record.是否动画,
        "has_exif": record.has_exif,
        "has_icc": record.has_icc,
    }
    获取资源元数据路径(record.id).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def 读取资源记录(resource_id: str) -> 图片资源记录:
    payload = json.loads(获取资源元数据路径(resource_id).read_text(encoding="utf-8"))
    source_path = Path(str(payload["source_path"]))
    return 图片资源记录(
        id=str(payload["id"]),
        source_path=str(source_path),
        preview_path=str(payload["preview_path"]),
        原始文件名=str(payload["原始文件名"]),
        原始MimeType=str(payload["原始MimeType"]),
        文件大小=int(payload.get("文件大小", source_path.stat().st_size if source_path.exists() else 0)),
        宽度=int(payload["宽度"]),
        高度=int(payload["高度"]),
        是否动画=bool(payload["是否动画"]),
        has_exif=bool(payload["has_exif"]),
        has_icc=bool(payload["has_icc"]),
    )


def 删除资源记录(resource_id: str) -> None:
    metadata_path = 获取资源元数据路径(resource_id)
    preview_path = 获取资源预览路径(resource_id)
    if metadata_path.exists():
        metadata_path.unlink()
    if preview_path.exists():
        preview_path.unlink()
