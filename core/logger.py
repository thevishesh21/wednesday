"""
WEDNESDAY AI OS — Structured Logger
Produces both human-readable console output and machine-readable JSON
to the rotating log file.

All new modules (core/, agent/, brain/) import from here.
Existing modules (tools/, voice/, gui/) continue using utils/logger.py —
that file is NOT modified.

Usage:
    from core.logger import get_logger
    log = get_logger("agent_loop")
    log.info("Task started", extra={"data": {"task_id": "abc"}})

Console output:
    [2026-04-27 13:25:01] [INFO   ] agent_loop → Task started

JSON file output:
    {"timestamp": "2026-04-27T13:25:01", "level": "INFO",
     "module": "agent_loop", "message": "Task started",
     "data": {"task_id": "abc"}}
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any


# ═════════════════════════════════════════════════════════════════
#  JSON Formatter
# ═════════════════════════════════════════════════════════════════

class _JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Each JSON record has: timestamp, level, module, message, and optional
    'data' field if extra={"data": {...}} is passed to the log call.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(
                timespec="seconds"
            ),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Include structured data if provided via extra={"data": {...}}
        if hasattr(record, "data") and record.data:  # type: ignore[attr-defined]
            log_obj["data"] = record.data  # type: ignore[attr-defined]

        # Include exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False, default=str)


# ═════════════════════════════════════════════════════════════════
#  Human-Readable Formatter (console)
# ═════════════════════════════════════════════════════════════════

_CONSOLE_FORMAT = "[%(asctime)s] [%(levelname)-7s] %(name)s → %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ═════════════════════════════════════════════════════════════════
#  Logger Factory
# ═════════════════════════════════════════════════════════════════

def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for the given module name.

    Produces:
      - Console output in human-readable format (INFO+ level)
      - JSON file output in machine-readable format (DEBUG+ level)
        Written to logs/wednesday.log with 1 MB rotation, 3 backups.

    The function is idempotent — calling it multiple times with the same
    name returns the same logger without adding duplicate handlers.

    Args:
        name: Logger name, typically the module name (e.g. "agent_loop").

    Returns:
        Configured logging.Logger instance.

    Example:
        log = get_logger("brain.llm_client")
        log.info("Ollama connected", extra={"data": {"model": "mistral"}})
    """
    logger = logging.getLogger(name)

    # Idempotent: don't add handlers twice
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Don't bubble to root logger

    # ── Import config lazily to avoid circular imports ────────────
    try:
        import config as _cfg
        log_to_console: bool = getattr(_cfg, "LOG_TO_CONSOLE", True)
        log_to_file: bool = getattr(_cfg, "LOG_TO_FILE", True)
        log_dir: str = getattr(_cfg, "LOG_DIR", "logs")
        log_file: str = getattr(_cfg, "LOG_FILE", "logs/wednesday.log")
    except ImportError:
        log_to_console = True
        log_to_file = True
        log_dir = "logs"
        log_file = "logs/wednesday.log"

    # ── Console handler (human-readable) ─────────────────────────
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT)
        )
        logger.addHandler(console_handler)

    # ── File handler (JSON, rotating) ─────────────────────────────
    if log_to_file:
        # Resolve path relative to project root
        project_root = _find_project_root()
        abs_log_dir = os.path.join(project_root, log_dir)
        abs_log_file = os.path.join(project_root, log_file)

        os.makedirs(abs_log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            abs_log_file,
            maxBytes=1_000_000,   # 1 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(_JSONFormatter())
        logger.addHandler(file_handler)

    return logger


# ═════════════════════════════════════════════════════════════════
#  Internal Helpers
# ═════════════════════════════════════════════════════════════════

def _find_project_root() -> str:
    """
    Walk up from this file's location to find the project root.
    The root is identified by the presence of 'main.py' or 'config.py'.
    Falls back to the current working directory.
    """
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):  # Search up to 4 levels
        if os.path.exists(os.path.join(current, "config.py")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()
