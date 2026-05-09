from __future__ import annotations

import base64
import io
from pathlib import Path
from threading import Lock
from typing import Final

from PIL import Image, ImageFile


SUPPORTED_IMAGE_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic", ".heif", ".avif"}
)
HEIF_BRANDS: Final[frozenset[bytes]] = frozenset(
    {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"avif", b"avis"}
)

_heif_opener_registered = False
_truncated_image_lock = Lock()


def ensure_image_openers_registered() -> None:
    global _heif_opener_registered
    if _heif_opener_registered:
        return
    try:
        from pillow_heif import register_heif_opener  # type: ignore[import-untyped]
    except ImportError:
        _heif_opener_registered = True
        return
    register_heif_opener()
    _heif_opener_registered = True


def is_supported_image_file(path: Path) -> bool:
    if path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
        return True
    return has_supported_image_signature(path)


def has_supported_image_signature(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(32)
    except OSError:
        return False

    if not head:
        return False
    if head.startswith(b"\xff\xd8\xff"):
        return True
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if head.startswith((b"GIF87a", b"GIF89a")):
        return True
    if head.startswith(b"BM"):
        return True
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return True
    return len(head) >= 12 and head[4:8] == b"ftyp" and head[8:12] in HEIF_BRANDS


def load_image_copy(image_path: Path) -> Image.Image:
    ensure_image_openers_registered()
    try:
        with Image.open(image_path) as opened_image:
            opened_image.load()
            return opened_image.copy()
    except (OSError, Image.UnidentifiedImageError):
        with _truncated_image_lock:
            previous = ImageFile.LOAD_TRUNCATED_IMAGES
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            try:
                with Image.open(image_path) as opened_image:
                    opened_image.load()
                    return opened_image.copy()
            finally:
                ImageFile.LOAD_TRUNCATED_IMAGES = previous


def encode_image_as_png_bytes(image_path: Path, minimum_edge: int = 32) -> bytes:
    image = load_image_copy(image_path)
    width = max(image.width, minimum_edge)
    height = max(image.height, minimum_edge)
    if (width, height) != image.size:
        image = image.resize((width, height))
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def encode_image_as_png_data_url(image_path: Path, minimum_edge: int = 32) -> str:
    encoded = base64.b64encode(encode_image_as_png_bytes(image_path, minimum_edge)).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
