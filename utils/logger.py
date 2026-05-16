"""
utils/logger.py
---------------
Centralized structured logging for Wednesday.

Every module does:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)

Output: colored console + rotating file at data/logs/wednesday.log
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ANSI color codes for console output
_COLORS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET":    "\033[0m",
}


class ColorFormatter(logging.Formatter):
    """Console formatter with ANSI colors per log level."""

    FMT = "{color}[{levelname:8s}]{reset} {asctime} | {name:22s} | {message}"

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, "")
        reset = _COLORS["RESET"]
        formatter = logging.Formatter(
            fmt=self.FMT.format(color=color, levelname="{levelname}", reset=reset,
                                asctime="{asctime}", name="{name}", message="{message}"),
            datefmt="%H:%M:%S",
            style="{",
        )
        return formatter.format(record)


def setup_logger(name: str) -> logging.Logger:
    """
    Build and return a logger for the given module name.
    Safe to call multiple times — handlers are not duplicated.
    """
    # Lazy import to avoid circular dependency at module load time
    from config.settings import settings

    log_level = getattr(logging, settings.log.level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(log_level)
    logger.propagate = False  # Don't bubble to root logger

    # ── Console handler ─────────────────────────────────────
    if settings.log.console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(ColorFormatter())
        logger.addHandler(ch)

    # ── Rotating file handler ────────────────────────────────
    if settings.log.file:
        log_path = Path(settings.log.log_dir) / "wednesday.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            filename=log_path,
            maxBytes=settings.log.max_bytes,
            backupCount=settings.log.backup_count,
            encoding="utf-8",
        )
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)

    return logger
