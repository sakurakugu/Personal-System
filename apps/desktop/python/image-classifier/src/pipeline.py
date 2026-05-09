from __future__ import annotations

import csv
import json
import subprocess
import shutil
from pathlib import Path
from typing import Callable, Iterable

from PIL import UnidentifiedImageError

from .backends.base import BaseClassifierBackend
from .image_support import is_supported_image_file, load_image_copy
from .models import (
    ClassificationResult,
    DEFAULT_VIDEO_FRAME_COUNT,
    InvalidImageFileError,
    SkippedImage,
    VideoFrameClassification,
    label_to_display_name,
    label_to_folder_name,
)
from .video_support import (
    cleanup_extracted_frames,
    discover_media_files,
    extract_video_frames,
    is_supported_video_file,
    merge_video_frame_results,
)


class ClassificationCancelled(Exception):
    pass


def discover_images(paths: Iterable[Path], recursive: bool = True) -> list[Path]:
    return [path for path in discover_media_files(list(paths), recursive=recursive) if is_supported_image_file(path)]


def discover_inputs(paths: Iterable[Path], recursive: bool = True) -> list[Path]:
    return discover_media_files(list(paths), recursive=recursive)


def classify_images(
    backend: BaseClassifierBackend,
    image_paths: Iterable[Path],
    on_result: Callable[[ClassificationResult, int, int], None] | None = None,
    on_skip: Callable[[SkippedImage, int, int], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> list[ClassificationResult]:
    return classify_media_files(
        backend,
        image_paths,
        on_result=on_result,
        on_skip=on_skip,
        should_stop=should_stop,
    )


def classify_media_files(
    backend: BaseClassifierBackend,
    media_paths: Iterable[Path],
    on_result: Callable[[ClassificationResult, int, int], None] | None = None,
    on_skip: Callable[[SkippedImage, int, int], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    video_frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
) -> list[ClassificationResult]:
    media_list = list(media_paths)
    total = len(media_list)
    results: list[ClassificationResult] = []
    for index, media_path in enumerate(media_list, start=1):
        if should_stop is not None and should_stop():
            raise ClassificationCancelled(f"分类已停止，已完成 {len(results)}/{total} 张图片。")
        try:
            if is_supported_video_file(media_path):
                result = _classify_video_file(
                    backend,
                    media_path,
                    video_frame_count=video_frame_count,
                )
            else:
                _validate_image_file(media_path)
                result = backend.classify(media_path)
        except InvalidImageFileError as exc:
            if on_skip is not None:
                on_skip(SkippedImage(image_path=media_path, reason=str(exc)), index, total)
            continue
        results.append(result)
        if on_result is not None:
            on_result(result, index, total)
    return results


def export_results_csv(results: list[ClassificationResult], output_path: Path) -> None:
    export_results_csv_with_skips(results, [], output_path)


def export_results_csv_with_skips(
    results: list[ClassificationResult],
    skipped_items: list[SkippedImage],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["status", "image_path", "label", "label_zh", "confidence", "reason", "raw_response"]
        )
        for result in results:
            writer.writerow(
                [
                    "classified",
                    str(result.image_path),
                    result.label,
                    label_to_display_name(result.label),
                    f"{result.confidence:.4f}",
                    result.reason,
                    result.raw_response,
                ]
            )
        for item in skipped_items:
            writer.writerow(["skipped", str(item.image_path), "", "", "", item.reason, ""])


def export_results_json(results: list[ClassificationResult], output_path: Path) -> None:
    export_results_json_with_skips(results, [], output_path)


def export_results_json_with_skips(
    results: list[ClassificationResult],
    skipped_items: list[SkippedImage],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "status": "classified",
            "image_path": str(result.image_path),
            "label": result.label,
            "label_zh": label_to_display_name(result.label),
            "confidence": round(result.confidence, 4),
            "reason": result.reason,
            "raw_response": result.raw_response,
        }
        for result in results
    ]
    payload.extend(
        {
            "status": "skipped",
            "image_path": str(item.image_path),
            "label": "",
            "label_zh": "",
            "confidence": None,
            "reason": item.reason,
            "raw_response": "",
        }
        for item in skipped_items
    )
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def move_results_to_label_folders(
    results: list[ClassificationResult],
    output_dir: Path,
) -> list[ClassificationResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    moved_results: list[ClassificationResult] = []
    for result in results:
        source_path = result.image_path
        target_dir = output_dir / label_to_folder_name(result.label)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / source_path.name
        if source_path.resolve() != target_path.resolve():
            target_path = _dedupe_target_path(target_path, source_path)
            shutil.move(str(source_path), str(target_path))
        moved_results.append(
            ClassificationResult(
                image_path=target_path,
                label=result.label,
                confidence=result.confidence,
                reason=result.reason,
                raw_response=result.raw_response,
            )
        )
    return moved_results


def move_skipped_items_to_folder(
    skipped_items: list[SkippedImage],
    output_dir: Path,
    folder_name: str = "跳过文件",
) -> list[SkippedImage]:
    if not skipped_items:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    target_dir = output_dir / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    moved_items: list[SkippedImage] = []
    for item in skipped_items:
        source_path = item.image_path
        target_path = target_dir / source_path.name
        if source_path.resolve() != target_path.resolve():
            target_path = _dedupe_target_path(target_path, source_path)
            shutil.move(str(source_path), str(target_path))
        moved_items.append(
            SkippedImage(
                image_path=target_path,
                reason=item.reason,
            )
        )
    return moved_items


def _dedupe_target_path(target_path: Path, source_path: Path) -> Path:
    if not target_path.exists():
        return target_path
    try:
        if target_path.resolve() == source_path.resolve():
            return target_path
    except FileNotFoundError:
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    index = 1
    while True:
        candidate = target_path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _validate_image_file(image_path: Path) -> None:
    if not is_supported_image_file(image_path):
        raise InvalidImageFileError("已跳过，文件既不是受支持的图片扩展名，也没有可识别的图片文件头。")

    try:
        image = load_image_copy(image_path)
        if image.width <= 0 or image.height <= 0:
            raise InvalidImageFileError("已跳过，图片尺寸无效。")
    except UnidentifiedImageError as exc:
        raise InvalidImageFileError("已跳过，文件内容不是有效图片。") from exc
    except OSError as exc:
        raise InvalidImageFileError(f"已跳过，图片文件损坏或无法读取：{exc}") from exc


def _classify_video_file(
    backend: BaseClassifierBackend,
    video_path: Path,
    video_frame_count: int,
) -> ClassificationResult:
    if not is_supported_video_file(video_path):
        raise InvalidImageFileError("已跳过，不是受支持的视频格式。")

    try:
        extracted_frames = extract_video_frames(video_path, video_frame_count)
    except subprocess.CalledProcessError as exc:
        raise InvalidImageFileError(f"已跳过，视频抽帧失败：{video_path.name}；{exc}") from exc
    except OSError as exc:
        raise InvalidImageFileError(f"已跳过，视频无法读取：{video_path.name}；{exc}") from exc
    except RuntimeError as exc:
        raise InvalidImageFileError(f"已跳过，视频处理失败：{video_path.name}；{exc}") from exc

    frame_results: list[VideoFrameClassification] = []
    try:
        for frame_index, timestamp_seconds, frame_path in extracted_frames:
            _validate_image_file(frame_path)
            result = backend.classify(frame_path)
            frame_results.append(
                VideoFrameClassification(
                    frame_index=frame_index,
                    timestamp_seconds=timestamp_seconds,
                    result=result,
                )
            )
    except InvalidImageFileError as exc:
        raise InvalidImageFileError(f"已跳过，视频抽出的帧无法识别：{video_path.name}；{exc}") from exc
    finally:
        cleanup_extracted_frames(extracted_frames)

    return merge_video_frame_results(video_path, frame_results)
