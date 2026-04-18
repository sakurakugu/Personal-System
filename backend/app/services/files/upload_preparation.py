"""文件上传预处理兼容入口。"""

from app.modules.files.upload_preparation import (
    PreparedUpload,
    build_fallback_filename,
    build_target_filename,
    convert_animated_image_to_avif,
    convert_image_to_avif,
    guess_content_type,
    guess_extension,
    is_animated_image,
    is_avif_upload,
    is_gif_upload,
    is_image_upload,
    is_svg_upload,
    normalize_content_type,
    normalize_filename_for_content_type,
    normalize_raster_image,
    prepare_upload_payload,
)

__all__ = [
    "PreparedUpload",
    "build_fallback_filename",
    "build_target_filename",
    "convert_animated_image_to_avif",
    "convert_image_to_avif",
    "guess_content_type",
    "guess_extension",
    "is_animated_image",
    "is_avif_upload",
    "is_gif_upload",
    "is_image_upload",
    "is_svg_upload",
    "normalize_content_type",
    "normalize_filename_for_content_type",
    "normalize_raster_image",
    "prepare_upload_payload",
]
