"""应用中间件与异常处理注册。"""

from __future__ import annotations

from datetime import datetime, timezone
from logging import Logger
from time import perf_counter
from typing import Awaitable, Callable, cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

from app.modules.auth.cookies import get_session_id_from_request
from app.modules.system.monitoring import SLOW_REQUEST_THRESHOLD_MS, record_request_event
from app.shared.kernel.config import settings
from app.shared.kernel.validation import request_validation_exception_handler

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
监控排除路径 = frozenset({
    "/api/health",
    "/api/v1/health",
    "/api/v1/admin/system",
})


def register_middlewares(app: FastAPI, *, app_logger: Logger) -> None:
    """注册中间件和异常处理器。"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter
    rate_limit_handler = cast(
        Callable[[Request, Exception], Response | Awaitable[Response]],
        _rate_limit_exceeded_handler,
    )
    validation_exception_handler = cast(
        Callable[[Request, Exception], Response | Awaitable[Response]],
        request_validation_exception_handler,
    )
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.middleware("http")
    async def csrf_protect_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """对携带登录 Session 的写操作执行 CSRF 校验。"""
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return await call_next(request)

        if get_session_id_from_request(request) is None:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(
                status_code=403,
                content='{"detail":"CSRF 校验失败"}',
                media_type="application/json",
            )

        return await call_next(request)

    @app.middleware("http")
    async def request_monitor_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """记录最近错误和慢请求摘要。"""
        if request.url.path in 监控排除路径:
            return await call_next(request)

        started_at = perf_counter()
        happened_at = datetime.now(timezone.utc)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((perf_counter() - started_at) * 1000, 1)
            detail: str | None = type(exc).__name__
            if str(exc):
                detail = f"{detail}: {exc}"
            await record_request_event(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                happened_at=happened_at,
                detail=detail,
            )
            app_logger.exception(
                "接口异常 %s %s，耗时 %.1f ms",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = round((perf_counter() - started_at) * 1000, 1)
        detail = "服务器内部错误" if response.status_code >= 500 else None
        await record_request_event(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            happened_at=happened_at,
            detail=detail,
        )

        if response.status_code >= 500:
            app_logger.error(
                "接口返回异常状态 %s %s，状态码 %s，耗时 %.1f ms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        elif duration_ms >= SLOW_REQUEST_THRESHOLD_MS:
            app_logger.warning(
                "慢请求 %s %s，状态码 %s，耗时 %.1f ms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )

        return response
