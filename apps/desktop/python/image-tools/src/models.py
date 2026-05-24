from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class 格式能力(TypedDict):
    mimeType: str
    扩展名: list[str]
    可导入: bool
    可导出: bool
    支持透明: bool
    支持动画: bool
    保留元数据: bool


class 图片工具能力(TypedDict):
    运行时: str
    支持后端增强: bool
    导入格式: list[格式能力]
    导出格式: list[格式能力]
    支持预览代理: bool
    支持拼接: bool
    支持编辑: bool
    支持批量转换: bool


class 图片资源句柄(TypedDict):
    id: str
    原始文件名: str
    原始MimeType: str
    文件大小: int
    宽度: int
    高度: int
    是否动画: bool
    预览地址: str
    源文件路径: str
    元数据摘要: dict[str, bool]


@dataclass(frozen=True, slots=True)
class 格式能力定义:
    mime_type: str
    扩展名: tuple[str, ...]
    可导入: bool
    可导出: bool
    支持透明: bool
    支持动画: bool
    保留元数据: bool

    def to_payload(self) -> 格式能力:
        return {
            "mimeType": self.mime_type,
            "扩展名": list(self.扩展名),
            "可导入": self.可导入,
            "可导出": self.可导出,
            "支持透明": self.支持透明,
            "支持动画": self.支持动画,
            "保留元数据": self.保留元数据,
        }


@dataclass(frozen=True, slots=True)
class 图片资源记录:
    id: str
    source_path: str
    preview_path: str
    原始文件名: str
    原始MimeType: str
    文件大小: int
    宽度: int
    高度: int
    是否动画: bool
    has_exif: bool
    has_icc: bool

    def to_payload(self) -> 图片资源句柄:
        return {
            "id": self.id,
            "原始文件名": self.原始文件名,
            "原始MimeType": self.原始MimeType,
            "文件大小": self.文件大小,
            "宽度": self.宽度,
            "高度": self.高度,
            "是否动画": self.是否动画,
            "预览地址": self.preview_path,
            "源文件路径": self.source_path,
            "元数据摘要": {
                "hasExif": self.has_exif,
                "hasIcc": self.has_icc,
            },
        }
