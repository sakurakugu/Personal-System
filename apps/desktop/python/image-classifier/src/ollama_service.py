from __future__ import annotations

import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit, urlunsplit

import requests

from .models import DEFAULT_OLLAMA_BASE_URL


def ensure_ollama_service_started(
    base_url: str,
    startup_timeout_seconds: int = 20,
) -> str:
    root_url = normalize_ollama_base_url(base_url)
    if not _is_local_url(root_url):
        raise ValueError("启动本地 Ollama 仅支持本机地址，请使用 http://127.0.0.1:11434。")

    if is_ollama_service_running(root_url):
        return f"Ollama 已在运行。服务地址：{root_url}"

    ollama_path = shutil.which("ollama")
    if not ollama_path:
        raise RuntimeError("未找到 ollama 命令，请先安装 Ollama，并确认已加入 PATH。")

    process = _start_ollama_process(ollama_path)
    deadline = time.monotonic() + startup_timeout_seconds
    while time.monotonic() < deadline:
        if is_ollama_service_running(root_url):
            return f"Ollama 启动成功。服务地址：{root_url}"
        if process.poll() is not None:
            raise RuntimeError("已尝试启动 Ollama，但进程提前退出，请在终端手动执行 ollama serve 排查。")
        time.sleep(0.5)

    raise RuntimeError(
        f"已尝试启动 Ollama，但在 {startup_timeout_seconds} 秒内未检测到服务响应：{root_url}"
    )


def ensure_ollama_model_state(
    base_url: str,
    model: str,
    should_load: bool,
    state_timeout_seconds: int = 60,
) -> str:
    normalized_model = model.strip()
    if not normalized_model:
        raise ValueError("模型名不能为空。")

    root_url = normalize_ollama_base_url(base_url)
    if should_load:
        ensure_ollama_service_started(root_url)
        if is_ollama_model_loaded(root_url, normalized_model):
            return f"模型已在运行：{normalized_model}"
        _request_model_state(root_url, normalized_model, keep_alive="24h")
        _wait_for_model_state(
            root_url,
            normalized_model,
            expected_loaded=True,
            state_timeout_seconds=state_timeout_seconds,
        )
        return f"模型启动成功：{normalized_model}"

    if not is_ollama_service_running(root_url):
        return f"Ollama 服务未启动，模型视为已关闭：{normalized_model}"
    if not is_ollama_model_loaded(root_url, normalized_model):
        return f"模型已关闭：{normalized_model}"
    _request_model_state(root_url, normalized_model, keep_alive="0")
    _wait_for_model_state(
        root_url,
        normalized_model,
        expected_loaded=False,
        state_timeout_seconds=state_timeout_seconds,
    )
    return f"模型已关闭：{normalized_model}"


def is_ollama_service_running(base_url: str, timeout_seconds: float = 2) -> bool:
    root_url = normalize_ollama_base_url(base_url)
    try:
        response = requests.get(
            f"{root_url}/api/tags",
            timeout=timeout_seconds,
        )
    except requests.RequestException:
        return False
    return response.ok


def is_ollama_model_loaded(base_url: str, model: str, timeout_seconds: float = 3) -> bool:
    normalized_model = model.strip()
    if not normalized_model:
        return False

    root_url = normalize_ollama_base_url(base_url)
    try:
        response = requests.get(
            f"{root_url}/api/ps",
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False

    payload = response.json()
    loaded_models = {
        item.get("name", "").strip()
        for item in payload.get("models", [])
        if isinstance(item, dict) and item.get("name")
    }
    return normalized_model in loaded_models


def normalize_ollama_base_url(base_url: str) -> str:
    candidate = (base_url or DEFAULT_OLLAMA_BASE_URL).strip()
    if not candidate:
        candidate = DEFAULT_OLLAMA_BASE_URL
    parsed = urlsplit(candidate)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Ollama 服务地址格式无效，请使用 http://127.0.0.1:11434。")
    path = parsed.path.rstrip("/")
    if path.endswith("/v1"):
        path = path[:-3]
    normalized_path = path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, normalized_path, "", ""))


def _is_local_url(base_url: str) -> bool:
    hostname = urlsplit(base_url).hostname
    return hostname in {"127.0.0.1", "localhost"}


def _request_model_state(base_url: str, model: str, keep_alive: str) -> None:
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "stream": False,
                "keep_alive": keep_alive,
            },
            timeout=120,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(_build_model_http_error_message(exc, model)) from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"模型状态切换失败：{model}；{exc}") from exc


def _wait_for_model_state(
    base_url: str,
    model: str,
    expected_loaded: bool,
    state_timeout_seconds: int,
) -> None:
    deadline = time.monotonic() + state_timeout_seconds
    while time.monotonic() < deadline:
        current_loaded = is_ollama_model_loaded(base_url, model)
        if current_loaded == expected_loaded:
            return
        time.sleep(0.5)
    action = "启动" if expected_loaded else "关闭"
    raise RuntimeError(f"模型{action}超时：{model}")


def _build_model_http_error_message(exc: requests.HTTPError, model: str) -> str:
    response = exc.response
    if response is None:
        return f"模型状态切换失败：{model}；{exc}"

    message = ""
    try:
        payload = response.json()
    except ValueError:
        message = response.text.strip()
    else:
        if isinstance(payload, dict):
            message = str(payload.get("error", "")).strip()
        else:
            message = str(payload).strip()

    if message:
        return f"模型状态切换失败：{model}；HTTP {response.status_code}；{message}"
    return f"模型状态切换失败：{model}；HTTP {response.status_code}"


def _start_ollama_process(ollama_path: str) -> subprocess.Popen[bytes]:
    if sys.platform == "win32":
        return subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    return subprocess.Popen(
        [ollama_path, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
