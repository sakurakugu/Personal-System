from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Final

from .image_support import is_supported_image_file
from .models import ClassificationResult, VideoFrameClassification


SUPPORTED_VIDEO_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
)


def is_supported_video_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_VIDEO_SUFFIXES


def discover_media_files(paths: list[Path], recursive: bool = True) -> list[Path]:
    discovered: list[Path] = []
    for path in paths:
        if path.is_file() and _is_supported_media_file(path):
            discovered.append(path)
            continue
        if path.is_dir():
            candidates = path.rglob("*") if recursive else path.iterdir()
            for candidate in candidates:
                if candidate.is_file() and _is_supported_media_file(candidate):
                    discovered.append(candidate)
    return sorted(set(discovered))


def extract_video_frames(video_path: Path, frame_count: int) -> list[tuple[int, float, Path]]:
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        raise RuntimeError("未找到 ffmpeg 或 ffprobe，无法处理视频。")
    if frame_count <= 0:
        raise ValueError("抽帧数量必须大于 0。")

    duration_seconds = _probe_video_duration(ffprobe_path, video_path)
    timestamps = _build_timestamps(duration_seconds, frame_count)

    temp_dir = Path(tempfile.mkdtemp(prefix="image_classifier_local_frames_"))
    frames: list[tuple[int, float, Path]] = []
    try:
        for frame_index, timestamp_seconds in enumerate(timestamps, start=1):
            frame_path = temp_dir / f"frame_{frame_index:02d}.png"
            _run_ffmpeg_extract(ffmpeg_path, video_path, frame_path, timestamp_seconds)
            if frame_path.exists():
                frames.append((frame_index, timestamp_seconds, frame_path))
        if not frames:
            raise RuntimeError(f"视频抽帧失败：{video_path}")
        return frames
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup_extracted_frames(frames: list[tuple[int, float, Path]]) -> None:
    if not frames:
        return
    temp_dir = frames[0][2].parent
    shutil.rmtree(temp_dir, ignore_errors=True)


def merge_video_frame_results(
    video_path: Path,
    frame_results: list[VideoFrameClassification],
) -> ClassificationResult:
    if not frame_results:
        raise ValueError("视频帧结果不能为空。")

    label_scores: dict[str, list[float]] = {}
    for item in frame_results:
        label_scores.setdefault(item.result.label, []).append(item.result.confidence)

    selected_label = max(
        label_scores.items(),
        key=lambda item: (len(item[1]), sum(item[1]) / len(item[1])),
    )[0]

    selected_items = [item for item in frame_results if item.result.label == selected_label]
    average_confidence = sum(item.result.confidence for item in selected_items) / len(selected_items)
    reason_fragments = [
        f"第{item.frame_index}帧（{item.timestamp_seconds:.1f}秒）：{item.result.reason}"
        for item in selected_items[:3]
        if item.result.reason
    ]
    reason = (
        f"视频共抽取 {len(frame_results)} 帧，投票结果为 {selected_label}。"
        if not reason_fragments
        else f"视频共抽取 {len(frame_results)} 帧，投票结果为 {selected_label}；" + "；".join(reason_fragments)
    )
    raw_response = json.dumps(
        [
            {
                "frame_index": item.frame_index,
                "timestamp_seconds": round(item.timestamp_seconds, 3),
                "label": item.result.label,
                "confidence": round(item.result.confidence, 4),
                "reason": item.result.reason,
            }
            for item in frame_results
        ],
        ensure_ascii=False,
    )
    return ClassificationResult(
        image_path=video_path,
        label=selected_label,
        confidence=average_confidence,
        reason=reason,
        raw_response=raw_response,
        source_kind="video",
    )


def _is_supported_media_file(path: Path) -> bool:
    return is_supported_image_file(path) or is_supported_video_file(path)


def _probe_video_duration(ffprobe_path: str, video_path: Path) -> float:
    response = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    content = response.stdout.strip()
    if not content:
        raise RuntimeError(f"无法读取视频时长：{video_path}")
    try:
        return max(float(content), 0.0)
    except ValueError as exc:
        raise RuntimeError(f"视频时长格式无效：{video_path}；{content}") from exc


def _build_timestamps(duration_seconds: float, frame_count: int) -> list[float]:
    if duration_seconds <= 0:
        return [0.0] * frame_count
    interval = duration_seconds / (frame_count + 1)
    return [min(interval * index, max(duration_seconds - 0.05, 0.0)) for index in range(1, frame_count + 1)]


def _run_ffmpeg_extract(
    ffmpeg_path: str,
    video_path: Path,
    frame_path: Path,
    timestamp_seconds: float,
) -> None:
    subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-ss",
            f"{timestamp_seconds:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(frame_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
