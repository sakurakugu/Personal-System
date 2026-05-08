"""请求校验异常中文化。"""

from __future__ import annotations

from typing import Any

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

字段中文名: dict[str, str] = {
    "username": "用户名",
    "nickname": "昵称",
    "email": "邮箱",
    "password": "密码",
    "current_password": "当前密码",
    "new_password": "新密码",
    "role": "角色",
    "bio": "个人简介",
    "avatar_url": "头像地址",
    "title": "标题",
    "content": "内容",
    "excerpt": "摘要",
    "cover_url": "封面地址",
    "status": "状态",
    "name": "名称",
    "description": "描述",
    "slug": "标识",
    "category_id": "分类",
    "tag_ids": "标签",
    "guest_name": "访客名称",
    "website_name": "网站名称",
    "website_url": "网站链接",
    "your_website_url": "贵站链接",
    "site_name": "网站名称",
    "site_url": "网站链接",
    "url": "链接",
    "announcement": "公告",
    "comment": "评论",
    "page": "页码",
    "page_size": "每页数量",
    "keyword": "关键词",
    "is_active": "启用状态",
    "is_pinned": "置顶状态",
    "is_public": "公开状态",
}

位置中文名: dict[str, str] = {
    "body": "请求体",
    "query": "查询参数",
    "path": "路径参数",
    "header": "请求头",
    "cookie": "Cookie",
}


def _格式化字段路径(loc: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, str):
            if item in 位置中文名:
                continue
            parts.append(字段中文名.get(item, item))
            continue
        if isinstance(item, int):
            if parts:
                parts[-1] = f"{parts[-1]}第 {item + 1} 项"
            else:
                parts.append(f"第 {item + 1} 项")
    return " / ".join(parts)


def _构造中文消息(error: dict[str, Any]) -> str:
    error_type = error.get("type", "")
    ctx = error.get("ctx") or {}
    loc = tuple(error.get("loc") or ())
    field_path = _格式化字段路径(loc)
    field_prefix = f"{field_path}：" if field_path else ""

    if error_type == "missing":
        return f"{field_prefix}不能为空"
    if error_type == "string_too_short":
        return f"{field_prefix}长度不能少于 {ctx.get('min_length')} 个字符"
    if error_type == "string_too_long":
        return f"{field_prefix}长度不能超过 {ctx.get('max_length')} 个字符"
    if error_type == "string_pattern_mismatch":
        return f"{field_prefix}格式不正确"
    if error_type == "string_type":
        return f"{field_prefix}必须是字符串"
    if error_type == "int_type":
        return f"{field_prefix}必须是整数"
    if error_type == "float_type":
        return f"{field_prefix}必须是数字"
    if error_type == "bool_type":
        return f"{field_prefix}必须是布尔值"
    if error_type == "list_type":
        return f"{field_prefix}必须是数组"
    if error_type == "dict_type":
        return f"{field_prefix}必须是对象"
    if error_type == "greater_than_equal":
        return f"{field_prefix}不能小于 {ctx.get('ge')}"
    if error_type == "less_than_equal":
        return f"{field_prefix}不能大于 {ctx.get('le')}"
    if error_type == "greater_than":
        return f"{field_prefix}必须大于 {ctx.get('gt')}"
    if error_type == "less_than":
        return f"{field_prefix}必须小于 {ctx.get('lt')}"
    if error_type == "enum":
        expected = ctx.get("expected")
        return f"{field_prefix}取值无效，可选值：{expected}"
    if error_type == "value_error":
        raw = error.get("msg", "")
        if isinstance(raw, str) and raw.startswith("Value error, "):
            raw = raw.removeprefix("Value error, ")
        return f"{field_prefix}{raw or '输入值无效'}"

    raw = error.get("msg", "")
    if isinstance(raw, str) and raw.startswith("String should have at least "):
        min_length = ctx.get("min_length")
        if min_length is not None:
            return f"{field_prefix}长度不能少于 {min_length} 个字符"
    if isinstance(raw, str) and raw.startswith("String should have at most "):
        max_length = ctx.get("max_length")
        if max_length is not None:
            return f"{field_prefix}长度不能超过 {max_length} 个字符"
    if isinstance(raw, str) and raw.startswith("Field required"):
        return f"{field_prefix}不能为空"

    return f"{field_prefix}{raw or '请求参数校验失败'}"


async def 请求校验异常处理器(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """将 FastAPI 请求校验错误转换为中文提示。"""
    _ = request
    errors = exc.errors()
    detail = [_构造中文消息(error) for error in errors]
    return JSONResponse(status_code=422, content={"detail": detail[0] if detail else "请求参数校验失败"})
