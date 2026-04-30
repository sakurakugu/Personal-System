"""
日志工具模块

提供统一的日志格式化和文件管理，支持应用日志和 SQLAlchemy 日志。
"""

import io
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO

# 日志级别中文名
LEVEL_NAME_CN = {
    "DEBUG": "调试",
    "INFO": "信息",
    "WARNING": "警告",
    "ERROR": "错误",
    "CRITICAL": "严重",
}

# 日志级别颜色 (ANSI 转义码)
LEVEL_COLOR = {
    "DEBUG": "\x1b[36m",      # 青色
    "INFO": "\x1b[32m",       # 绿色
    "WARNING": "\x1b[33m",    # 黄色
    "ERROR": "\x1b[31m",      # 红色
    "CRITICAL": "\x1b[1;31m", # 加粗红色
}

RESET_COLOR = "\x1b[0m"


class CNLevelFormatter(logging.Formatter):
    """中文日志级别格式化器，支持彩色输出"""

    def __init__(
        self,
        fmt: str,
        time_mode: str = "file",
        datefmt: str | None = None,
        enable_color: bool = False,
    ):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.time_mode = time_mode
        self.enable_color = enable_color

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        if self.time_mode == "console":
            local_dt = datetime.fromtimestamp(record.created).astimezone()
            return local_dt.strftime(datefmt or "%H:%M:%S.%f")[:-3]  # 毫秒精度
        local_dt = datetime.fromtimestamp(record.created).astimezone()
        ts = local_dt.isoformat(timespec="microseconds")
        if ts.endswith("Z") or ts.endswith("z"):
            ts = ts[:-1] + "+00:00"
        return ts

    def format(self, record: logging.LogRecord) -> str:
        original = record.levelname
        level_cn = LEVEL_NAME_CN.get(original, original)
        if self.enable_color:
            color = LEVEL_COLOR.get(original, "")
            record.levelname = f"{color}{level_cn}{RESET_COLOR}"
        else:
            record.levelname = level_cn
        try:
            return super().format(record)
        finally:
            record.levelname = original


def _get_console_stream() -> TextIO | None:
    """获取控制台输出流"""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOBase) and stream.isatty():
            return stream  # type: ignore[return-value]
    return None


def _build_log_path(
    base_dir: Path,
    date_value: datetime | None = None,
    file_prefix: str | None = None,
) -> Path:
    """构建日志文件路径，按日期分类"""
    now = date_value or datetime.now().astimezone()
    date_folder = now.date().isoformat()
    date_compact = now.strftime("%Y%m%d")
    daily_dir = base_dir / date_folder
    daily_dir.mkdir(parents=True, exist_ok=True)
    name = file_prefix or "app"
    return daily_dir / f"{name}_{date_compact}.log"


class DailySwitchingHandler(logging.Handler):
    """每日自动切换的日志处理器"""

    def __init__(
        self,
        base_dir: Path,
        formatter: logging.Formatter,
        level: int,
        max_file_size_mb: int | None = None,
        file_prefix: str | None = None,
    ) -> None:
        super().__init__(level=level)
        self.base_dir = base_dir
        self.max_file_size_mb = max_file_size_mb
        self._formatter = formatter
        self.file_prefix = file_prefix
        self._current_date = datetime.now().astimezone().date()
        self._handler = self._create_handler(datetime.now().astimezone())

    def _create_handler(self, now: datetime) -> logging.Handler:
        log_path = _build_log_path(self.base_dir, now, self.file_prefix)
        handler: logging.Handler
        if self.max_file_size_mb:
            handler = RotatingFileHandler(
                log_path,
                maxBytes=self.max_file_size_mb * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
        else:
            handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(self._formatter)
        return handler

    def emit(self, record: logging.LogRecord) -> None:
        now = datetime.fromtimestamp(record.created).astimezone()
        record_date = now.date()
        if record_date != self._current_date:
            self._current_date = record_date
            self._handler.close()
            self._handler = self._create_handler(now)
        self._handler.emit(record)

    def flush(self) -> None:
        self._handler.flush()

    def close(self) -> None:
        try:
            self._handler.close()
        finally:
            super().close()


def get_logger(name: str | None = None) -> logging.Logger:
    """获取 logger 实例"""
    return logging.getLogger(name or "app")


def configure_logger(
    app_name: str = "app",
    log_dir: str | Path | None = None,
    level: int | str = logging.INFO,
    max_file_size_mb: int | None = None,
    log_file_prefix: str | None = None,
) -> logging.Logger:
    """配置应用日志

    Args:
        app_name: 应用名称，作为 logger 名称
        log_dir: 日志目录，默认 backend/logs
        level: 日志级别
        max_file_size_mb: 单个日志文件最大大小（MB）
        log_file_prefix: 日志文件前缀

    Returns:
        配置好的 logger
    """
    resolved_level = level
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)

    # 默认日志目录：项目根目录下的 logs
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs" / app_name
    base_dir = Path(log_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # 文件日志格式化器
    file_formatter = CNLevelFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d %(funcName)s] %(message)s",
        time_mode="file",
    )
    file_handler = DailySwitchingHandler(
        base_dir=base_dir,
        formatter=file_formatter,
        level=resolved_level,
        max_file_size_mb=max_file_size_mb,
        file_prefix=log_file_prefix or app_name,
    )

    handlers: list[logging.Handler] = [file_handler]

    # 控制台日志（带颜色）
    console_stream = _get_console_stream()
    if console_stream is not None:
        console_handler = logging.StreamHandler(console_stream)
        console_formatter = CNLevelFormatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] %(message)s",
            time_mode="console",
            datefmt="%H:%M:%S.%f",
            enable_color=True,
        )
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    logger = logging.getLogger(app_name)
    logger.setLevel(resolved_level)
    logger.handlers = []
    for handler in handlers:
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def configure_sqlalchemy_logger(
    log_dir: str | Path | None = None,
    level: int | str = logging.INFO,
    max_file_size_mb: int | None = None,
) -> logging.Logger:
    """配置 SQLAlchemy 日志，使用与应用相同的样式

    Args:
        log_dir: 日志目录，默认 backend/logs/sqlalchemy
        level: 日志级别
        max_file_size_mb: 单个日志文件最大大小（MB）

    Returns:
        配置好的 SQLAlchemy logger
    """
    resolved_level = level
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)

    # SQLAlchemy 日志目录
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs" / "sqlalchemy"
    base_dir = Path(log_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # 文件日志格式化器（简化格式，SQL 语句较长）
    file_formatter = CNLevelFormatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        time_mode="file",
    )
    file_handler = DailySwitchingHandler(
        base_dir=base_dir,
        formatter=file_formatter,
        level=resolved_level,
        max_file_size_mb=max_file_size_mb,
        file_prefix="sqlalchemy",
    )

    handlers: list[logging.Handler] = [file_handler]

    # 控制台日志（带颜色，简化格式）
    console_stream = _get_console_stream()
    if console_stream is not None:
        console_handler = logging.StreamHandler(console_stream)
        # SQLAlchemy 控制台格式更简洁，因为 SQL 语句通常很长
        console_formatter = CNLevelFormatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            time_mode="console",
            datefmt="%H:%M:%S.%f",
            enable_color=True,
        )
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    # 配置 SQLAlchemy 引擎日志
    logger = logging.getLogger("sqlalchemy.engine.Engine")
    logger.setLevel(resolved_level)
    logger.handlers = []
    for handler in handlers:
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def setup_logging(
    app_name: str = "app",
    log_dir: str | Path | None = None,
    level: int | str = logging.INFO,
    sqlalchemy_level: int | str = logging.WARNING,
    max_file_size_mb: int | None = None,
) -> tuple[logging.Logger, logging.Logger]:
    """统一配置应用日志和 SQLAlchemy 日志

    Args:
        app_name: 应用名称
        log_dir: 日志根目录，默认 backend/logs
        level: 应用日志级别
        sqlalchemy_level: SQLAlchemy 日志级别
        max_file_size_mb: 单个日志文件最大大小（MB）

    Returns:
        (app_logger, sqlalchemy_logger) 元组

    Example:
        >>> from app.core.logger import setup_logging
        >>> app_logger, sql_logger = setup_logging(
        ...     app_name="personal-system",
        ...     level="INFO",
        ...     sqlalchemy_level="INFO"  # 显示 SQL 语句
        ... )
    """
    # 应用日志目录
    if log_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)

    # 配置应用日志
    app_logger = configure_logger(
        app_name=app_name,
        log_dir=log_dir / app_name,
        level=level,
        max_file_size_mb=max_file_size_mb,
    )

    # 配置 SQLAlchemy 日志
    sql_logger = configure_sqlalchemy_logger(
        log_dir=log_dir / "sqlalchemy",
        level=sqlalchemy_level,
        max_file_size_mb=max_file_size_mb,
    )

    return app_logger, sql_logger


__all__ = [
    "get_logger",
    "configure_logger",
    "configure_sqlalchemy_logger",
    "setup_logging",
    "CNLevelFormatter",
    "DailySwitchingHandler",
]
