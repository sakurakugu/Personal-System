from __future__ import annotations

import mimetypes
import math
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

from .models import 图片工具能力, 格式能力定义
from .models import 图片资源记录, 图片资源句柄
from .storage import 保存资源记录, 创建资源标识, 删除资源记录, 获取资源预览路径, 读取资源记录

桌面格式定义 = [
    格式能力定义(
        mime_type="image/png",
        扩展名=("png",),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/jpeg",
        扩展名=("jpg", "jpeg"),
        可导入=True,
        可导出=True,
        支持透明=False,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/webp",
        扩展名=("webp",),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/avif",
        扩展名=("avif",),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/heic",
        扩展名=("heic", "heif"),
        可导入=True,
        可导出=False,
        支持透明=False,
        支持动画=False,
        保留元数据=True,
    ),
    格式能力定义(
        mime_type="image/tiff",
        扩展名=("tif", "tiff"),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=True,
    ),
    格式能力定义(
        mime_type="image/bmp",
        扩展名=("bmp",),
        可导入=True,
        可导出=True,
        支持透明=False,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/x-icon",
        扩展名=("ico",),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=False,
    ),
    格式能力定义(
        mime_type="image/vnd.adobe.photoshop",
        扩展名=("psd",),
        可导入=True,
        可导出=False,
        支持透明=True,
        支持动画=False,
        保留元数据=True,
    ),
    格式能力定义(
        mime_type="image/gif",
        扩展名=("gif",),
        可导入=True,
        可导出=True,
        支持透明=True,
        支持动画=False,
        保留元数据=False,
    ),
]

预览最大尺寸 = (1600, 1600)
MimeType到格式 = {
    "image/png": ("PNG", "png"),
    "image/jpeg": ("JPEG", "jpg"),
    "image/webp": ("WEBP", "webp"),
    "image/avif": ("AVIF", "avif"),
    "image/bmp": ("BMP", "bmp"),
    "image/tiff": ("TIFF", "tiff"),
    "image/x-icon": ("ICO", "ico"),
    "image/gif": ("GIF", "gif"),
}


def _读取字符串值(payload: dict[str, object], key: str, default: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or default
    return default


def _读取布尔值(payload: dict[str, object], key: str, default: bool) -> bool:
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "1", "yes"}:
            return True
        if value.lower() in {"false", "0", "no"}:
            return False
    return default


def _读取浮点值(payload: dict[str, object], key: str, default: float) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _读取整数值(payload: dict[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        try:
            return int(round(float(value)))
        except ValueError:
            return default
    return default


def 获取图片工具能力() -> 图片工具能力:
    导入格式 = [item.to_payload() for item in 桌面格式定义 if item.可导入]
    导出格式 = [item.to_payload() for item in 桌面格式定义 if item.可导出]
    return {
        "运行时": "desktop",
        "支持后端增强": True,
        "导入格式": 导入格式,
        "导出格式": 导出格式,
        "支持预览代理": True,
        "支持拼接": True,
        "支持编辑": True,
        "支持批量转换": True,
    }


def _推断图片MimeType(image: Image.Image, source_path: Path) -> str:
    if image.format and image.format in Image.MIME:
        return str(Image.MIME[image.format])

    guessed, _ = mimetypes.guess_type(source_path.name)
    return guessed or "application/octet-stream"


def _构建预览图(source_path: Path, resource_id: str) -> 图片资源记录:
    preview_path = 获取资源预览路径(resource_id)

    try:
        with Image.open(source_path) as image:
            normalized = ImageOps.exif_transpose(image)
            preview_image = normalized.copy()
            preview_image.thumbnail(预览最大尺寸, Image.Resampling.LANCZOS)
            preview_image.save(preview_path, format="PNG")

            mime_type = _推断图片MimeType(image, source_path)
            is_animated = bool(getattr(image, "is_animated", False) and getattr(image, "n_frames", 1) > 1)
            has_exif = bool(normalized.getexif())
            has_icc = bool(normalized.info.get("icc_profile"))
            width, height = normalized.size
    except UnidentifiedImageError as error:
        raise ValueError(f"无法识别图片格式：{source_path}") from error

    return 图片资源记录(
        id=resource_id,
        source_path=str(source_path),
        preview_path=str(preview_path),
        原始文件名=source_path.name,
        原始MimeType=mime_type,
        文件大小=source_path.stat().st_size,
        宽度=width,
        高度=height,
        是否动画=is_animated,
        has_exif=has_exif,
        has_icc=has_icc,
    )


def _准备导出图像(image: Image.Image, output_mime_type: str) -> Image.Image:
    normalized = ImageOps.exif_transpose(image)
    if output_mime_type in {"image/jpeg", "image/bmp"}:
        if normalized.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", normalized.size, "#ffffff")
            alpha = normalized.getchannel("A")
            background.paste(normalized.convert("RGBA"), mask=alpha)
            return background
        if normalized.mode == "P":
            return normalized.convert("RGB")
    if output_mime_type == "image/x-icon":
        return normalized.convert("RGBA")
    return normalized.copy()


def _应用编辑参数(image: Image.Image, edit: dict[str, object], output_mime_type: str) -> Image.Image:
    normalized = ImageOps.exif_transpose(image)
    working = normalized.convert("RGBA")

    if bool(edit.get("水平翻转")):
        working = ImageOps.mirror(working)
    if bool(edit.get("垂直翻转")):
        working = ImageOps.flip(working)

    rotation = _读取整数值(edit, "旋转角度", 0) % 360
    if rotation:
        working = working.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)

    brightness = _读取浮点值(edit, "亮度", 100)
    contrast = _读取浮点值(edit, "对比度", 100)
    saturation = _读取浮点值(edit, "饱和度", 100)
    grayscale = _读取浮点值(edit, "灰度", 0)
    blur = _读取浮点值(edit, "模糊", 0)

    if brightness != 100:
        working = ImageEnhance.Brightness(working).enhance(brightness / 100)
    if contrast != 100:
        working = ImageEnhance.Contrast(working).enhance(contrast / 100)
    if saturation != 100:
        working = ImageEnhance.Color(working).enhance(saturation / 100)
    if grayscale > 0:
        gray = ImageOps.grayscale(working).convert("RGBA")
        alpha = max(0.0, min(1.0, grayscale / 100))
        working = Image.blend(working, gray, alpha)
    if blur > 0:
        working = working.filter(ImageFilter.GaussianBlur(radius=blur))

    crop = edit.get("裁剪区域")
    if isinstance(crop, dict):
        crop_payload = crop
        crop_x = max(0, _读取整数值(crop_payload, "x", 0))
        crop_y = max(0, _读取整数值(crop_payload, "y", 0))
        crop_width = max(1, _读取整数值(crop_payload, "width", 1))
        crop_height = max(1, _读取整数值(crop_payload, "height", 1))
        crop_right = min(working.width, crop_x + crop_width)
        crop_bottom = min(working.height, crop_y + crop_height)
        working = working.crop((crop_x, crop_y, crop_right, crop_bottom))

    output_width = _读取整数值(edit, "输出宽度", working.width)
    output_height = _读取整数值(edit, "输出高度", working.height)
    if output_width > 0 and output_height > 0 and (working.width != output_width or working.height != output_height):
        working = working.resize((output_width, output_height), Image.Resampling.LANCZOS)

    if output_mime_type in {"image/jpeg", "image/bmp"}:
        background = Image.new("RGB", working.size, "#ffffff")
        alpha_channel = working.getchannel("A")
        background.paste(working, mask=alpha_channel)
        working.close()
        return background

    if output_mime_type == "image/x-icon":
        return working.convert("RGBA")

    return working


def _构建保存参数(output_mime_type: str, quality: float | None) -> tuple[str, dict[str, object]]:
    format_info = MimeType到格式.get(output_mime_type)
    if not format_info:
        raise ValueError(f"暂不支持导出格式：{output_mime_type}")

    format_name, _extension = format_info
    save_options: dict[str, object] = {}

    if quality is not None and output_mime_type in {"image/jpeg", "image/webp", "image/avif"}:
        normalized_quality = quality * 100 if quality <= 1 else quality
        save_options["quality"] = max(1, min(100, int(round(normalized_quality))))

    if output_mime_type == "image/jpeg":
        save_options["optimize"] = True
    if output_mime_type == "image/png":
        save_options["optimize"] = True

    return format_name, save_options


def _获取宫格比例(aspect: str) -> float:
    if aspect == "4:3":
        return 4 / 3
    if aspect == "3:4":
        return 3 / 4
    if aspect == "16:9":
        return 16 / 9
    return 1.0


def _填充拼接背景(canvas: Image.Image, options: dict[str, object], output_mime_type: str) -> None:
    background_payload = options.get("背景")
    background_options: dict[str, object] = background_payload if isinstance(background_payload, dict) else {}
    transparent = _读取字符串值(background_options, "type", "solid") == "transparent"
    if transparent and output_mime_type != "image/jpeg":
        return

    background_color = "#ffffff"
    if background_options:
        background_color = _读取字符串值(background_options, "color", "#ffffff")

    fill_color = "#ffffff" if transparent and output_mime_type == "image/jpeg" else background_color
    background = Image.new("RGBA", canvas.size, fill_color)
    canvas.alpha_composite(background)


def _打开拼接源图片(resource_ids: list[str]) -> list[tuple[图片资源记录, Image.Image]]:
    opened: list[tuple[图片资源记录, Image.Image]] = []
    try:
        for resource_id in resource_ids:
            record = 读取资源记录(resource_id.strip())
            image = ImageOps.exif_transpose(Image.open(record.source_path)).convert("RGBA")
            opened.append((record, image))
        return opened
    except Exception:
        for _, image in opened:
            image.close()
        raise


def _关闭拼接源图片(images: list[tuple[图片资源记录, Image.Image]]) -> None:
    for _, image in images:
        image.close()


def _渲染横向拼接(images: list[tuple[图片资源记录, Image.Image]], options: dict[str, object]) -> Image.Image:
    target_size = max(40, _读取整数值(options, "目标尺寸", 480))
    gap = max(0, _读取整数值(options, "间距", 24))
    padding = max(0, _读取整数值(options, "边距", 24))

    widths: list[int] = []
    total_width = padding * 2
    for record, _image in images:
        ratio = record.宽度 / record.高度
        draw_width = max(1, int(round(target_size * ratio)))
        widths.append(draw_width)
        total_width += draw_width
    total_width += max(0, len(images) - 1) * gap
    total_height = target_size + padding * 2

    canvas = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    current_x = padding
    for index, (_record, image) in enumerate(images):
        resized = image.resize((widths[index], target_size), Image.Resampling.LANCZOS)
        canvas.alpha_composite(resized, (current_x, padding))
        resized.close()
        current_x += widths[index] + gap
    return canvas


def _渲染纵向拼接(images: list[tuple[图片资源记录, Image.Image]], options: dict[str, object]) -> Image.Image:
    target_size = max(40, _读取整数值(options, "目标尺寸", 480))
    gap = max(0, _读取整数值(options, "间距", 24))
    padding = max(0, _读取整数值(options, "边距", 24))

    heights: list[int] = []
    total_height = padding * 2
    for record, _image in images:
        ratio = record.高度 / record.宽度
        draw_height = max(1, int(round(target_size * ratio)))
        heights.append(draw_height)
        total_height += draw_height
    total_height += max(0, len(images) - 1) * gap
    total_width = target_size + padding * 2

    canvas = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    current_y = padding
    for index, (_record, image) in enumerate(images):
        resized = image.resize((target_size, heights[index]), Image.Resampling.LANCZOS)
        canvas.alpha_composite(resized, (padding, current_y))
        resized.close()
        current_y += heights[index] + gap
    return canvas


def _渲染字幕拼接(images: list[tuple[图片资源记录, Image.Image]], options: dict[str, object]) -> Image.Image:
    target_size = max(40, _读取整数值(options, "目标尺寸", 480))
    gap = max(0, _读取整数值(options, "间距", 24))
    padding = max(0, _读取整数值(options, "边距", 24))
    keep_ratio = max(0.0, min(1.0, _读取浮点值(options, "字幕裁剪比例", 15) / 100))

    heights: list[int] = []
    crop_specs: list[tuple[int, int, int, int]] = []
    total_height = padding * 2
    for index, (record, _image) in enumerate(images):
        source_width = record.宽度
        source_height = record.高度 if index == 0 else max(1, int(round(record.高度 * keep_ratio)))
        source_y = 0 if index == 0 else record.高度 - source_height
        draw_height = max(1, int(round(target_size * (source_height / source_width))))
        crop_specs.append((0, source_y, source_width, source_height))
        heights.append(draw_height)
        total_height += draw_height
    total_height += max(0, len(images) - 1) * gap
    total_width = target_size + padding * 2

    canvas = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    current_y = padding
    for index, (_record, image) in enumerate(images):
        source_x, source_y, source_width, source_height = crop_specs[index]
        cropped = image.crop((source_x, source_y, source_x + source_width, source_y + source_height))
        resized = cropped.resize((target_size, heights[index]), Image.Resampling.LANCZOS)
        canvas.alpha_composite(resized, (padding, current_y))
        cropped.close()
        resized.close()
        current_y += heights[index] + gap
    return canvas


def _渲染宫格拼接(images: list[tuple[图片资源记录, Image.Image]], options: dict[str, object]) -> Image.Image:
    target_size = max(40, _读取整数值(options, "目标尺寸", 480))
    columns = max(1, min(8, _读取整数值(options, "列数", 3)))
    gap = max(0, _读取整数值(options, "间距", 24))
    padding = max(0, _读取整数值(options, "边距", 24))
    aspect_ratio = _获取宫格比例(_读取字符串值(options, "宫格比例", "1:1"))
    fit_mode = _读取字符串值(options, "宫格填充", "contain")

    cell_width = target_size
    cell_height = max(1, int(round(target_size / aspect_ratio)))
    rows = max(1, math.ceil(len(images) / columns))
    canvas_width = padding * 2 + columns * cell_width + max(0, columns - 1) * gap
    canvas_height = padding * 2 + rows * cell_height + max(0, rows - 1) * gap
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

    for index, (_record, image) in enumerate(images):
        row = index // columns
        column = index % columns
        cell_x = padding + column * (cell_width + gap)
        cell_y = padding + row * (cell_height + gap)
        scale = max(cell_width / image.width, cell_height / image.height) if fit_mode == "cover" else min(cell_width / image.width, cell_height / image.height)
        draw_width = max(1, int(round(image.width * scale)))
        draw_height = max(1, int(round(image.height * scale)))
        resized = image.resize((draw_width, draw_height), Image.Resampling.LANCZOS)
        draw_x = cell_x + int(round((cell_width - draw_width) / 2))
        draw_y = cell_y + int(round((cell_height - draw_height) / 2))

        if fit_mode == "cover":
            cell_canvas = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
            paste_x = int(round((cell_width - draw_width) / 2))
            paste_y = int(round((cell_height - draw_height) / 2))
            cell_canvas.alpha_composite(resized, (paste_x, paste_y))
            canvas.alpha_composite(cell_canvas, (cell_x, cell_y))
            cell_canvas.close()
        else:
            canvas.alpha_composite(resized, (draw_x, draw_y))
        resized.close()

    return canvas


def 从路径导入图片(paths: list[str]) -> list[图片资源句柄]:
    imported: list[图片资源句柄] = []
    errors: list[str] = []

    for raw_path in paths:
        source_path = Path(raw_path).expanduser()
        if not source_path.is_file():
            errors.append(f"文件不存在：{source_path}")
            continue

        resource_id = 创建资源标识()
        try:
            record = _构建预览图(source_path, resource_id)
            保存资源记录(record)
            imported.append(record.to_payload())
        except Exception as error:
            删除资源记录(resource_id)
            errors.append(str(error))

    if imported:
        return imported

    message = "；".join(errors) if errors else "没有可导入的图片文件"
    raise ValueError(message)


def 转换图片(resource_id: str, output_mime_type: str, output_path: str, quality: float | None) -> dict[str, object]:
    record = 读取资源记录(resource_id.strip())
    target_path = Path(output_path).expanduser()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    source_path = Path(record.source_path)
    if not source_path.is_file():
        raise ValueError(f"源文件不存在：{source_path}")

    format_name, save_options = _构建保存参数(output_mime_type, quality)

    try:
        with Image.open(source_path) as image:
            export_image = _准备导出图像(image, output_mime_type)
            try:
                export_image.save(target_path, format=format_name, **save_options)
            finally:
                export_image.close()
    except UnidentifiedImageError as error:
        raise ValueError(f"无法读取源图片：{source_path}") from error

    if not target_path.exists():
        raise ValueError(f"导出失败，未生成目标文件：{target_path}")

    return {
        "outputPath": str(target_path),
        "outputMimeType": output_mime_type,
        "outputSize": target_path.stat().st_size,
    }


def 导出编辑结果(
    resource_id: str,
    edit: dict[str, object],
    output_mime_type: str,
    output_path: str,
    quality: float | None,
) -> dict[str, object]:
    record = 读取资源记录(resource_id.strip())
    target_path = Path(output_path).expanduser()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    source_path = Path(record.source_path)
    if not source_path.is_file():
        raise ValueError(f"源文件不存在：{source_path}")

    format_name, save_options = _构建保存参数(output_mime_type, quality)

    try:
        with Image.open(source_path) as image:
            export_image = _应用编辑参数(image, edit, output_mime_type)
            try:
                export_image.save(target_path, format=format_name, **save_options)
            finally:
                export_image.close()
    except UnidentifiedImageError as error:
        raise ValueError(f"无法读取源图片：{source_path}") from error

    if not target_path.exists():
        raise ValueError(f"导出失败，未生成目标文件：{target_path}")

    return {
        "outputPath": str(target_path),
        "outputMimeType": output_mime_type,
        "outputSize": target_path.stat().st_size,
    }


def 导出拼接结果(
    resource_ids: list[str],
    stitch: dict[str, object],
    output_mime_type: str,
    output_path: str,
    quality: float | None,
) -> dict[str, object]:
    if not resource_ids:
        raise ValueError("至少需要一张图片才能拼接。")

    target_path = Path(output_path).expanduser()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    format_name, save_options = _构建保存参数(output_mime_type, quality)

    opened_images = _打开拼接源图片(resource_ids)
    try:
        layout = _读取字符串值(stitch, "布局", "horizontal")
        if layout == "vertical":
            canvas = _渲染纵向拼接(opened_images, stitch)
        elif layout == "subtitle":
            canvas = _渲染字幕拼接(opened_images, stitch)
        elif layout == "grid":
            canvas = _渲染宫格拼接(opened_images, stitch)
        else:
            canvas = _渲染横向拼接(opened_images, stitch)

        try:
            _填充拼接背景(canvas, stitch, output_mime_type)
            if output_mime_type in {"image/jpeg", "image/bmp"}:
                export_image = Image.new("RGB", canvas.size, "#ffffff")
                export_image.paste(canvas, mask=canvas.getchannel("A"))
                canvas.close()
                canvas = export_image
            canvas.save(target_path, format=format_name, **save_options)
        finally:
            canvas.close()
    finally:
        _关闭拼接源图片(opened_images)

    if not target_path.exists():
        raise ValueError(f"拼接导出失败，未生成目标文件：{target_path}")

    return {
        "outputPath": str(target_path),
        "outputMimeType": output_mime_type,
        "outputSize": target_path.stat().st_size,
    }


def 释放图片资源(resource_ids: list[str]) -> None:
    for resource_id in resource_ids:
        normalized = resource_id.strip()
        if normalized:
            删除资源记录(normalized)
