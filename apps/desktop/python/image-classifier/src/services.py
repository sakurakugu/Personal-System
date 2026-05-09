from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .backends.mock import MockClassifierBackend
from .backends.ollama import OllamaBackend
from .backends.openai_compatible import OpenAICompatibleBackend
from .models import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_BASE_URL,
    DEFAULT_OPENAI_MODEL,
    BackendConfig,
    ClassificationResult,
    DEFAULT_VIDEO_FRAME_COUNT,
    SkippedImage,
)
from .ollama_service import ensure_ollama_model_state, ensure_ollama_service_started, is_ollama_model_loaded
from .pipeline import classify_media_files, discover_inputs


@dataclass(slots=True)
class ClassifierServiceConfig:
    backend_name: str
    base_url: str = ""
    model: str = ""
    api_key: str = ""


@dataclass(slots=True)
class ClassificationRunResult:
    media_paths: list[Path]
    results: list[ClassificationResult]
    skipped_items: list[SkippedImage]
    duration_ms: int


def build_backend_config(config: ClassifierServiceConfig) -> BackendConfig:
    backend_name = config.backend_name.strip() or "mock"
    if backend_name == "mock":
        return BackendConfig(backend_name="mock")

    default_base_url = DEFAULT_OPENAI_BASE_URL
    default_model = DEFAULT_OPENAI_MODEL
    if backend_name == "ollama":
        default_base_url = DEFAULT_OLLAMA_BASE_URL
        default_model = DEFAULT_OLLAMA_MODEL

    normalized = BackendConfig(
        backend_name=backend_name,
        model=config.model.strip() or default_model,
        base_url=config.base_url.strip() or default_base_url,
        api_key=config.api_key.strip(),
    )
    if not normalized.base_url or not normalized.model:
        raise ValueError("使用远程模型后端时，服务地址和模型名不能为空。")
    return normalized


def create_backend(config: ClassifierServiceConfig) -> MockClassifierBackend | OllamaBackend | OpenAICompatibleBackend:
    normalized = build_backend_config(config)
    if normalized.backend_name == "mock":
        return MockClassifierBackend()
    if normalized.backend_name == "ollama":
        return OllamaBackend(normalized)
    return OpenAICompatibleBackend(normalized)


def discover_media_inputs(paths: list[Path], recursive: bool = True) -> list[Path]:
    return discover_inputs(paths, recursive=recursive)


def test_backend_connection(config: ClassifierServiceConfig) -> str:
    backend = create_backend(config)
    return backend.test_connection()


def start_local_ollama(base_url: str) -> str:
    return ensure_ollama_service_started(base_url)


def set_ollama_model_state(base_url: str, model: str, should_load: bool) -> str:
    return ensure_ollama_model_state(base_url, model, should_load)


def get_ollama_model_state(base_url: str, model: str) -> bool:
    return is_ollama_model_loaded(base_url, model)


def run_classification(
    config: ClassifierServiceConfig,
    inputs: list[Path],
    *,
    recursive: bool = True,
    video_frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
    on_result: Callable[[ClassificationResult, int, int], None] | None = None,
    on_skip: Callable[[SkippedImage, int, int], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> ClassificationRunResult:
    media_paths = discover_media_inputs(inputs, recursive=recursive)
    backend = create_backend(config)
    skipped_items: list[SkippedImage] = []

    def handle_skip(item: SkippedImage, completed: int, total: int) -> None:
        skipped_items.append(item)
        if on_skip is not None:
            on_skip(item, completed, total)

    started_at = time.perf_counter()
    results = classify_media_files(
        backend,
        media_paths,
        on_result=on_result,
        on_skip=handle_skip,
        should_stop=should_stop,
        video_frame_count=video_frame_count,
    )
    duration_ms = int((time.perf_counter() - started_at) * 1000)

    return ClassificationRunResult(
        media_paths=media_paths,
        results=results,
        skipped_items=skipped_items,
        duration_ms=duration_ms,
    )
