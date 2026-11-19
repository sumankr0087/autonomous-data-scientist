"""Production-grade logging setup.

Features
--------
- Single `setup_logging()` entry point, idempotent (safe to call repeatedly).
- Rich, colourised console output in development.
- Rotating file handler (plain text or JSON lines) for persistence.
- `get_logger(__name__)` helper used throughout the codebase.
- `bind()` helper to attach a `run_id` (or any context) to every record.

Usage
-----
    from ads.core.logging import setup_logging, get_logger

    setup_logging()
    log = get_logger(__name__)
    log.info("hello", extra={"run_id": "abc123"})
"""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config.settings import LOGS_DIR, get_settings

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects (one per line)."""

    _RESERVED = set(
        logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
    ) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Attach any custom `extra=` fields (e.g. run_id, agent, step).
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


def _console_handler(level: int) -> logging.Handler:
    """Return a colourised console handler if `rich` is available, else stdlib."""
    try:
        from rich.logging import RichHandler  # type: ignore

        handler: logging.Handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=False,
        )
        handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))
    except Exception:  # pragma: no cover - fallback path
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
    handler.setLevel(level)
    return handler


def _file_handler(level: int, as_json: bool) -> logging.Handler:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    filename = "app.jsonl" if as_json else "app.log"
    handler = RotatingFileHandler(
        Path(LOGS_DIR) / filename,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        JsonFormatter()
        if as_json
        else logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
    )
    handler.setLevel(level)
    return handler


def setup_logging(force: bool = False) -> None:
    """Configure the root logger exactly once (idempotent).

    Reads level / json / file options from `Settings`. Call this at the very
    start of any entry point (CLI, Streamlit app, tests).
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    # Clear existing handlers to avoid duplicate lines on re-configure.
    for existing in list(root.handlers):
        root.removeHandler(existing)

    root.addHandler(_console_handler(level))
    if settings.log_to_file:
        root.addHandler(_file_handler(level, settings.log_json))

    # Tame noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger (configures logging on first use)."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter that injects persistent context (e.g. run_id) into every record."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = {**(self.extra or {}), **kwargs.get("extra", {})}
        kwargs["extra"] = extra
        return msg, kwargs


def bind(logger: logging.Logger, **context: Any) -> LoggerAdapter:
    """Bind context (run_id, agent, step, ...) so it appears on every log line."""
    return LoggerAdapter(logger, context)
