"""
Wednesday AI Assistant — Logger
Dual output: console + rotating log file in logs/ directory.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
import config


def get_logger(name: str = "wednesday") -> logging.Logger:
    """
    Returns a configured logger instance.
    - Console output (if config.LOG_TO_CONSOLE is True)
    - File output  (if config.LOG_TO_FILE is True) with rotation at 1 MB
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] %(name)s → %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ──────────────────────────────────────────
    if config.LOG_TO_CONSOLE:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)

    # ── File handler (rotating, max 1 MB, keep 3 backups) ────────
    if config.LOG_TO_FILE:
        # Resolve path relative to the project root (parent of utils/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, config.LOG_DIR)
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.join(project_root, config.LOG_FILE)
        file_handler = RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

