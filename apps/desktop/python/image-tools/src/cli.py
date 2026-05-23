from __future__ import annotations

import argparse
import json
import sys

from .services import 从路径导入图片, 导出拼接结果, 导出编辑结果, 获取图片工具能力, 转换图片, 释放图片资源


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-tools",
        description="桌面端图片工具本地处理器。",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("capabilities-json", help="输出桌面端图片工具能力")
    import_parser = subparsers.add_parser("import-json", help="从本地路径导入图片并生成预览")
    import_parser.add_argument("inputs", nargs="+", help="图片文件路径")
    convert_parser = subparsers.add_parser("convert-json", help="将导入资源导出为目标格式")
    convert_parser.add_argument("--resource-id", required=True, help="资源标识")
    convert_parser.add_argument("--mime-type", required=True, help="目标 MimeType")
    convert_parser.add_argument("--output-path", required=True, help="输出文件路径")
    convert_parser.add_argument("--quality", type=float, default=-1, help="导出质量，可传 0-1 或 1-100")
    edit_parser = subparsers.add_parser("edit-json", help="将导入资源按编辑参数导出为目标格式")
    edit_parser.add_argument("--resource-id", required=True, help="资源标识")
    edit_parser.add_argument("--mime-type", required=True, help="目标 MimeType")
    edit_parser.add_argument("--output-path", required=True, help="输出文件路径")
    edit_parser.add_argument("--quality", type=float, default=-1, help="导出质量，可传 0-1 或 1-100")
    edit_parser.add_argument("--edit-json", required=True, help="编辑参数 JSON 字符串")
    stitch_parser = subparsers.add_parser("stitch-json", help="将多张导入资源按拼接参数导出为目标格式")
    stitch_parser.add_argument("--resource-ids", nargs="+", required=True, help="资源标识列表")
    stitch_parser.add_argument("--mime-type", required=True, help="目标 MimeType")
    stitch_parser.add_argument("--output-path", required=True, help="输出文件路径")
    stitch_parser.add_argument("--quality", type=float, default=-1, help="导出质量，可传 0-1 或 1-100")
    stitch_parser.add_argument("--stitch-json", required=True, help="拼接参数 JSON 字符串")
    release_parser = subparsers.add_parser("release-json", help="释放临时图片资源")
    release_parser.add_argument("resource_ids", nargs="+", help="资源标识")
    return parser


def run_capabilities_json() -> int:
    print(json.dumps(获取图片工具能力(), ensure_ascii=False))
    return 0


def run_import_json(inputs: list[str]) -> int:
    print(json.dumps(从路径导入图片(inputs), ensure_ascii=False))
    return 0


def run_convert_json(resource_id: str, mime_type: str, output_path: str, quality: float) -> int:
    normalized_quality = None if quality < 0 else quality
    print(json.dumps(转换图片(resource_id, mime_type, output_path, normalized_quality), ensure_ascii=False))
    return 0


def run_edit_json(resource_id: str, mime_type: str, output_path: str, quality: float, edit_json: str) -> int:
    normalized_quality = None if quality < 0 else quality
    edit_payload = json.loads(edit_json)
    print(json.dumps(导出编辑结果(resource_id, edit_payload, mime_type, output_path, normalized_quality), ensure_ascii=False))
    return 0


def run_stitch_json(resource_ids: list[str], mime_type: str, output_path: str, quality: float, stitch_json: str) -> int:
    normalized_quality = None if quality < 0 else quality
    stitch_payload = json.loads(stitch_json)
    print(json.dumps(导出拼接结果(resource_ids, stitch_payload, mime_type, output_path, normalized_quality), ensure_ascii=False))
    return 0


def run_release_json(resource_ids: list[str]) -> int:
    释放图片资源(resource_ids)
    print(json.dumps({"released": resource_ids}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "capabilities-json":
        return run_capabilities_json()
    if args.command == "import-json":
        return run_import_json(args.inputs)
    if args.command == "convert-json":
        return run_convert_json(args.resource_id, args.mime_type, args.output_path, args.quality)
    if args.command == "edit-json":
        return run_edit_json(args.resource_id, args.mime_type, args.output_path, args.quality, args.edit_json)
    if args.command == "stitch-json":
        return run_stitch_json(args.resource_ids, args.mime_type, args.output_path, args.quality, args.stitch_json)
    if args.command == "release-json":
        return run_release_json(args.resource_ids)

    parser.print_help(sys.stderr)
    return 1
