"""文章 MCP 正文片段定位与哈希辅助。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Literal

from fastapi import HTTPException, status


定位类型 = Literal["heading", "line_range", "text_anchor"]


@dataclass(frozen=True)
class 正文片段:
    """正文片段定位结果。"""

    content: str
    start_index: int
    end_index: int
    start_line: int
    end_line: int
    target: dict[str, Any]


def 计算片段哈希(content: str) -> str:
    """计算 MCP 正文片段哈希。"""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def 构建正文摘要(content: str) -> dict[str, Any]:
    """构建不会泄露完整正文的摘要信息。"""
    return {
        "length": len(content),
        "line_count": len(content.splitlines()) if content else 0,
        "hash": 计算片段哈希(content),
    }


def _按原始行拆分(content: str) -> list[str]:
    """按行拆分并保留换行符。"""
    return content.splitlines(keepends=True) or [""]


def _行起始偏移(lines: list[str]) -> list[int]:
    """计算每一行的起始字符偏移。"""
    offsets: list[int] = []
    current = 0
    for line in lines:
        offsets.append(current)
        current += len(line)
    return offsets


def _清理标题(raw_title: str) -> str:
    """清理 Markdown 标题文字。"""
    return re.sub(r"\s+#{1,}\s*$", "", raw_title).strip()


def _是否代码围栏行(line: str) -> bool:
    """判断是否为 fenced code block 边界。"""
    stripped = line.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def 解析Markdown大纲(content: str) -> list[dict[str, Any]]:
    """解析 Markdown ATX 标题并返回片段定位信息。"""
    lines = _按原始行拆分(content)
    offsets = _行起始偏移(lines)
    headings: list[dict[str, Any]] = []
    stack: list[str] = []
    in_fence = False

    for index, line in enumerate(lines):
        if _是否代码围栏行(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.rstrip("\r\n"))
        if match is None:
            continue
        level = len(match.group(1))
        title = _清理标题(match.group(2))
        stack = stack[: level - 1]
        stack.append(title)
        headings.append(
            {
                "level": level,
                "title": title,
                "line": index + 1,
                "heading_path": stack.copy(),
                "start_line": index + 1,
                "start_index": offsets[index],
            }
        )

    content_length = len(content)
    for index, heading in enumerate(headings):
        next_index = content_length
        next_line = len(lines)
        for candidate in headings[index + 1 :]:
            if candidate["level"] <= heading["level"]:
                next_index = int(candidate["start_index"])
                next_line = int(candidate["start_line"]) - 1
                break
        section = content[int(heading["start_index"]) : next_index]
        heading["end_index"] = next_index
        heading["end_line"] = next_line
        heading["hash"] = 计算片段哈希(section)
        heading["length"] = len(section)

    return headings


def _定位标题片段(content: str, target: dict[str, Any]) -> 正文片段:
    """按标题路径定位正文片段。"""
    heading_path = target.get("heading_path")
    if not isinstance(heading_path, list) or not all(isinstance(item, str) for item in heading_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="heading 定位需要 heading_path")

    matches = [item for item in 解析Markdown大纲(content) if item["heading_path"] == heading_path]
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定标题片段")
    if len(matches) > 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="标题路径不唯一，无法安全定位")

    item = matches[0]
    start_index = int(item["start_index"])
    end_index = int(item["end_index"])
    return 正文片段(
        content=content[start_index:end_index],
        start_index=start_index,
        end_index=end_index,
        start_line=int(item["start_line"]),
        end_line=int(item["end_line"]),
        target={"type": "heading", "heading_path": heading_path},
    )


def _定位行范围片段(content: str, target: dict[str, Any]) -> 正文片段:
    """按行范围定位正文片段。"""
    start_line = target.get("start_line")
    end_line = target.get("end_line")
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="line_range 定位需要 start_line 和 end_line")
    if start_line < 1 or end_line < start_line:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的正文行范围")

    lines = _按原始行拆分(content)
    if end_line > len(lines):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="正文行范围超出当前内容")

    offsets = _行起始偏移(lines)
    start_index = offsets[start_line - 1]
    end_index = offsets[end_line - 1] + len(lines[end_line - 1])
    return 正文片段(
        content=content[start_index:end_index],
        start_index=start_index,
        end_index=end_index,
        start_line=start_line,
        end_line=end_line,
        target={"type": "line_range", "start_line": start_line, "end_line": end_line},
    )


def _定位文本锚点片段(content: str, target: dict[str, Any]) -> 正文片段:
    """按原文和前后锚点定位正文片段。"""
    text = target.get("text")
    if not isinstance(text, str) or not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text_anchor 定位需要 text")

    search_start = 0
    before_text = target.get("before_text")
    if isinstance(before_text, str) and before_text:
        before_index = content.find(before_text)
        if before_index < 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到前置锚点")
        search_start = before_index + len(before_text)

    search_end = len(content)
    after_text = target.get("after_text")
    if isinstance(after_text, str) and after_text:
        after_index = content.find(after_text, search_start)
        if after_index < 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到后置锚点")
        search_end = after_index

    scoped = content[search_start:search_end]
    relative_index = scoped.find(text)
    if relative_index < 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定原文片段")
    if scoped.find(text, relative_index + 1) >= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="原文片段不唯一，无法安全定位")

    start_index = search_start + relative_index
    end_index = start_index + len(text)
    start_line = content.count("\n", 0, start_index) + 1
    end_line = content.count("\n", 0, max(start_index, end_index - 1)) + 1
    return 正文片段(
        content=content[start_index:end_index],
        start_index=start_index,
        end_index=end_index,
        start_line=start_line,
        end_line=end_line,
        target={
            "type": "text_anchor",
            "text": text,
            "before_text": before_text,
            "after_text": after_text,
        },
    )


def 定位正文片段(content: str, target: dict[str, Any]) -> 正文片段:
    """按 MCP 定位参数查找正文片段。"""
    target_type = target.get("type")
    if target_type == "heading":
        return _定位标题片段(content, target)
    if target_type == "line_range":
        return _定位行范围片段(content, target)
    if target_type == "text_anchor":
        return _定位文本锚点片段(content, target)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的正文定位类型")


def 替换正文片段(content: str, fragment: 正文片段, replacement: str) -> str:
    """替换正文片段并返回新正文。"""
    return f"{content[: fragment.start_index]}{replacement}{content[fragment.end_index :]}"
