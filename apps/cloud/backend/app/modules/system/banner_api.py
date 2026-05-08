"""Banner 轮播图路由。"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/banner-images", tags=["banner"])

图片扩展名 = (".avif", ".jpg", ".jpeg", ".png", ".webp", ".gif")


def _解析横幅目录() -> str | None:
    """解析 banner 图片目录路径。"""
    container_path = "/app/banner"
    if os.path.isdir(container_path):
        return container_path

    dev_path = os.path.join(
        os.path.dirname(__file__),
        "../../../../frontend/public/banner",
    )
    dev_path = os.path.normpath(dev_path)
    if os.path.isdir(dev_path):
        return dev_path
    return None


@router.get("")
def 列出横幅图片() -> dict[str, list[str]]:
    """返回 public/banner/ 目录下的图片 URL 列表。"""
    banner_dir = _解析横幅目录()
    if not banner_dir:
        raise HTTPException(status_code=404, detail="Banner 目录不存在")

    try:
        files = [
            file_name
            for file_name in os.listdir(banner_dir)
            if os.path.isfile(os.path.join(banner_dir, file_name))
            and file_name.lower().endswith(图片扩展名)
        ]
        files.sort()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"读取目录失败: {exc}") from exc

    return {"images": [f"/banner/{file_name}" for file_name in files]}
