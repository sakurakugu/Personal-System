from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .models import (
    ClassificationResult,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_VIDEO_FRAME_COUNT,
    SkippedImage,
    label_to_display_name,
)
from .pipeline import (
    export_results_csv_with_skips,
    export_results_json_with_skips,
    move_results_to_label_folders,
)
from .services import (
    ClassifierServiceConfig,
    discover_media_inputs,
    get_ollama_model_state,
    run_classification,
    set_ollama_model_state,
    start_local_ollama,
    test_backend_connection,
)


def add_batch_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_export_options: bool,
) -> None:
    parser.add_argument("inputs", nargs="+", help="图片、视频文件或目录路径")
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="目录输入时只扫描当前目录，不递归子目录",
    )
    parser.add_argument(
        "--backend",
        choices=["mock", "ollama", "openai_compatible"],
        default="mock",
        help="后端类型，默认 mock",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="后端服务地址；ollama 默认使用 http://127.0.0.1:11434",
    )
    parser.add_argument("--model", default="", help="模型名称")
    parser.add_argument("--api-key", default="", help="接口密钥")
    parser.add_argument(
        "--video-frame-count",
        type=int,
        default=DEFAULT_VIDEO_FRAME_COUNT,
        help=f"视频分类时每个视频抽取的帧数，默认 {DEFAULT_VIDEO_FRAME_COUNT}",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="未发现图片时返回非零退出码",
    )
    if include_export_options:
        parser.add_argument("--csv", default="", help="导出 CSV 路径")
        parser.add_argument("--json", default="", help="导出 JSON 路径")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-classifier-local",
        description="本地图像分类工具，支持 GUI 和 CLI 两种模式。",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("gui", help="启动图形界面")

    cli_parser = subparsers.add_parser("cli", help="命令行批量分类")
    add_batch_arguments(cli_parser, include_export_options=True)

    desktop_parser = subparsers.add_parser("desktop-json", help="桌面端结构化批量分类")
    add_batch_arguments(desktop_parser, include_export_options=False)

    desktop_stream_parser = subparsers.add_parser("desktop-stream-json", help="桌面端流式结构化批量分类")
    add_batch_arguments(desktop_stream_parser, include_export_options=False)

    discover_parser = subparsers.add_parser("discover-json", help="桌面端结构化发现输入文件")
    discover_parser.add_argument("inputs", nargs="+", help="图片、视频文件或目录路径")
    discover_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="目录输入时只扫描当前目录，不递归子目录",
    )

    action_parser = subparsers.add_parser("action-json", help="桌面端结构化动作入口")
    action_parser.add_argument(
        "--action",
        choices=["test_connection", "start_ollama", "toggle_ollama_model", "get_ollama_model_state"],
        required=True,
        help="要执行的动作",
    )
    action_parser.add_argument(
        "--backend",
        choices=["mock", "ollama", "openai_compatible"],
        default="mock",
        help="后端类型，默认 mock",
    )
    action_parser.add_argument(
        "--base-url",
        default="",
        help="服务地址；ollama 默认使用 http://127.0.0.1:11434",
    )
    action_parser.add_argument("--model", default="", help="模型名称")
    action_parser.add_argument("--api-key", default="", help="接口密钥")
    action_parser.add_argument(
        "--should-load",
        choices=["true", "false"],
        default="true",
        help="切换模型时的目标状态",
    )

    result_action_parser = subparsers.add_parser("result-action-json", help="桌面端结构化结果处理入口")
    result_action_parser.add_argument(
        "--action",
        choices=["export_csv", "export_json", "move_results"],
        required=True,
        help="要执行的结果处理动作",
    )
    result_action_parser.add_argument(
        "--payload-file",
        required=True,
        help="结果负载 JSON 文件路径",
    )
    result_action_parser.add_argument(
        "--output-path",
        required=True,
        help="导出文件路径或移动目标目录",
    )

    return parser


def build_service_config(args) -> ClassifierServiceConfig:
    return ClassifierServiceConfig(
        backend_name=args.backend,
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
    )


def build_desktop_payload(
    media_paths: list[Path],
    results,
    skipped_items: list[SkippedImage],
    *,
    duration_ms: int,
) -> dict[str, object]:
    return {
        "summary": {
            "total": len(media_paths),
            "classified": len(results),
            "skipped": len(skipped_items),
            "durationMs": duration_ms,
        },
        "results": [
            {
                "path": str(result.image_path),
                "sourceKind": result.source_kind,
                "label": result.label,
                "labelZh": label_to_display_name(result.label),
                "confidence": round(result.confidence, 4),
                "reason": result.reason,
                "rawResponse": result.raw_response,
            }
            for result in results
        ],
        "skipped": [
            {
                "path": str(item.image_path),
                "reason": item.reason,
            }
            for item in skipped_items
        ],
    }


def collect_classification_results(args) -> tuple[list[Path], list, list[SkippedImage], int]:
    result = run_classification(
        build_service_config(args),
        [Path(item) for item in args.inputs],
        recursive=not args.no_recursive,
        video_frame_count=args.video_frame_count,
    )
    return result.media_paths, result.results, result.skipped_items, result.duration_ms


def run_cli(args) -> int:
    media_paths = discover_media_inputs([Path(item) for item in args.inputs], recursive=not args.no_recursive)
    if not media_paths:
        print("未发现可处理的图片或视频。")
        return 2 if args.fail_on_empty else 0

    _, results, skipped, _duration_ms = collect_classification_results(args)

    for item in skipped:
        print(f"跳过\t{item.image_path}\t{item.reason}")

    for result in results:
        print(
            f"{result.image_path}\t{label_to_display_name(result.label)} ({result.label})\t{result.confidence:.2f}\t{result.reason}"
        )

    if args.csv:
        output_path = Path(args.csv)
        export_results_csv_with_skips(results, skipped, output_path)
        print(f"\n已导出 CSV：{output_path}")

    if args.json:
        output_path = Path(args.json)
        export_results_json_with_skips(results, skipped, output_path)
        print(f"\n已导出 JSON：{output_path}")

    print(f"\n处理完成，共 {len(results)} 个媒体文件，跳过 {len(skipped)} 个文件。")
    return 0


def run_desktop_json(args) -> int:
    media_paths = discover_media_inputs([Path(item) for item in args.inputs], recursive=not args.no_recursive)
    if not media_paths:
        payload = build_desktop_payload([], [], [], duration_ms=0)
        print(json.dumps(payload, ensure_ascii=False))
        return 2 if args.fail_on_empty else 0

    try:
        media_paths, results, skipped_items, duration_ms = collect_classification_results(args)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    payload = build_desktop_payload(
        media_paths,
        results,
        skipped_items,
        duration_ms=duration_ms,
    )
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def emit_desktop_stream_event(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def is_stop_requested() -> bool:
    return os.environ.get("PERSONAL_SYSTEM_IMAGE_CLASSIFIER_STOP_REQUESTED") == "1"


def run_desktop_stream_json(args) -> int:
    media_paths = discover_media_inputs([Path(item) for item in args.inputs], recursive=not args.no_recursive)
    total = len(media_paths)
    emit_desktop_stream_event({
        "type": "started",
        "total": total,
    })
    if not media_paths:
        emit_desktop_stream_event({
            "type": "completed",
            "summary": {
                "total": 0,
                "classified": 0,
                "skipped": 0,
                "durationMs": 0,
            },
        })
        return 2 if args.fail_on_empty else 0

    def on_result(result, completed: int, event_total: int) -> None:
        emit_desktop_stream_event({
            "type": "result",
            "completed": completed,
            "total": event_total,
            "result": {
                "path": str(result.image_path),
                "sourceKind": result.source_kind,
                "label": result.label,
                "labelZh": label_to_display_name(result.label),
                "confidence": round(result.confidence, 4),
                "reason": result.reason,
                "rawResponse": result.raw_response,
            },
        })

    skipped_items: list[SkippedImage] = []

    def on_skip(item: SkippedImage, completed: int, event_total: int) -> None:
        skipped_items.append(item)
        emit_desktop_stream_event({
            "type": "skipped",
            "completed": completed,
            "total": event_total,
            "item": {
                "path": str(item.image_path),
                "reason": item.reason,
            },
        })

    try:
        result = run_classification(
            build_service_config(args),
            [Path(item) for item in args.inputs],
            recursive=not args.no_recursive,
            video_frame_count=args.video_frame_count,
            on_result=on_result,
            on_skip=on_skip,
            should_stop=is_stop_requested,
        )
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    emit_desktop_stream_event({
        "type": "completed",
        "summary": {
            "total": total,
            "classified": len(result.results),
            "skipped": len(skipped_items),
            "durationMs": result.duration_ms,
        },
    })
    return 0


def run_discover_json(args) -> int:
    media_paths = discover_media_inputs([Path(item) for item in args.inputs], recursive=not args.no_recursive)
    payload = {
        "inputs": [str(path) for path in media_paths],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def run_action_json(args) -> int:
    try:
        payload: dict[str, object]
        if args.action == "test_connection":
            payload = {
                "message": test_backend_connection(build_service_config(args)),
            }
        elif args.action == "start_ollama":
            payload = {
                "message": start_local_ollama(args.base_url or DEFAULT_OLLAMA_BASE_URL),
            }
        elif args.action == "toggle_ollama_model":
            should_load = args.should_load == "true"
            payload = {
                "message": set_ollama_model_state(
                    args.base_url or DEFAULT_OLLAMA_BASE_URL,
                    args.model or DEFAULT_OLLAMA_MODEL,
                    should_load=should_load,
                ),
                "loaded": should_load,
            }
        elif args.action == "get_ollama_model_state":
            payload = {
                "loaded": get_ollama_model_state(
                    args.base_url or DEFAULT_OLLAMA_BASE_URL,
                    args.model or DEFAULT_OLLAMA_MODEL,
                ),
            }
        else:
            raise ValueError(f"不支持的动作：{args.action}")
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


def load_result_payload(payload_file: Path) -> tuple[list[ClassificationResult], list[SkippedImage]]:
    payload = json.loads(payload_file.read_text(encoding="utf-8"))
    results = [
        ClassificationResult(
            image_path=Path(item["path"]),
            source_kind=item.get("sourceKind", "image"),
            label=item["label"],
            confidence=float(item.get("confidence", 0)),
            reason=item.get("reason", ""),
            raw_response=item.get("rawResponse", ""),
        )
        for item in payload.get("results", [])
    ]
    skipped_items = [
        SkippedImage(
            image_path=Path(item["path"]),
            reason=item.get("reason", ""),
        )
        for item in payload.get("skipped", [])
    ]
    return results, skipped_items


def build_result_items_payload(results: list[ClassificationResult]) -> list[dict[str, object]]:
    return [
        {
            "path": str(result.image_path),
            "sourceKind": result.source_kind,
            "label": result.label,
            "labelZh": label_to_display_name(result.label),
            "confidence": round(result.confidence, 4),
            "reason": result.reason,
            "rawResponse": result.raw_response,
        }
        for result in results
    ]


def build_skipped_items_payload(skipped_items: list[SkippedImage]) -> list[dict[str, object]]:
    return [
        {
            "path": str(item.image_path),
            "reason": item.reason,
        }
        for item in skipped_items
    ]


def run_result_action_json(args) -> int:
    try:
        results, skipped_items = load_result_payload(Path(args.payload_file))
        output_path = Path(args.output_path)
        payload: dict[str, object]

        if args.action == "export_csv":
            export_results_csv_with_skips(results, skipped_items, output_path)
            payload = {
                "message": f"已导出 CSV：{output_path}",
            }
        elif args.action == "export_json":
            export_results_json_with_skips(results, skipped_items, output_path)
            payload = {
                "message": f"已导出 JSON：{output_path}",
            }
        elif args.action == "move_results":
            moved_results = move_results_to_label_folders(results, output_path)
            payload = {
                "message": f"已移动 {len(moved_results)} 张分类图片到：{output_path}；跳过文件保留原位置",
                "results": build_result_items_payload(moved_results),
                "skipped": build_skipped_items_payload(skipped_items),
            }
        else:
            raise ValueError(f"不支持的结果处理动作：{args.action}")
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "gui"):
        from .gui import launch

        launch()
        return 0
    if args.command == "cli":
        return run_cli(args)
    if args.command == "desktop-json":
        return run_desktop_json(args)
    if args.command == "desktop-stream-json":
        return run_desktop_stream_json(args)
    if args.command == "discover-json":
        return run_discover_json(args)
    if args.command == "action-json":
        return run_action_json(args)
    if args.command == "result-action-json":
        return run_result_action_json(args)

    parser.print_help()
    return 1
