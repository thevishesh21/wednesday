"""
WEDNESDAY AI OS — Config Loader & Validator
A validated wrapper around the existing config.py.

FIX: Now loads .env file FIRST before reading config.py so that
     OPENROUTER_API_KEY and all other secrets are always available.

Usage:
    from core.config_loader import cfg

    print(cfg.WAKE_WORD)         # "hey wednesday"
    print(cfg.has_cloud_llm)     # True/False based on API keys
    print(cfg.log_dir_path)      # Resolved pathlib.Path
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# ── Load .env FIRST — before anything else reads os.environ ──────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass  # dotenv not installed — env vars must be set manually

from core.exceptions import ConfigError
from core.logger import get_logger

log = get_logger("core.config_loader")


# ═════════════════════════════════════════════════════════════════
#  Validation Helpers
# ═════════════════════════════════════════════════════════════════

def _validate_range(
    field: str, value: int | float, lo: int | float, hi: int | float
) -> None:
    if not (lo <= value <= hi):
        raise ConfigError(
            f"Config field '{field}' must be between {lo} and {hi}, got {value}",
            details={"field": field, "value": value, "min": lo, "max": hi},
        )


def _validate_type(field: str, value: Any, expected: type) -> None:
    if not isinstance(value, expected):
        raise ConfigError(
            f"Config field '{field}' must be {expected.__name__}, "
            f"got {type(value).__name__}",
            details={"field": field, "type": type(value).__name__},
        )


# ═════════════════════════════════════════════════════════════════
#  Config Loader
# ═════════════════════════════════════════════════════════════════

class _WednesdayConfig:
    """
    Validated configuration object for WEDNESDAY.

    Reads from config.py, validates all critical fields, and exposes
    them as typed attributes plus computed convenience properties.

    API keys are read from os.environ (populated by .env) with
    config.py as fallback — so .env is ALWAYS the source of truth.
    """

    def __init__(self) -> None:
        self._raw = self._load_raw_config()
        self._validate()
        log.info("Configuration loaded and validated successfully.")

    # ── Load raw config ───────────────────────────────────────────

    def _load_raw_config(self) -> Any:
        try:
            import config as _cfg
            return _cfg
        except ImportError as exc:
            raise ConfigError(
                "config.py not found. Ensure you are running from the project root.",
                details={"error": str(exc)},
            ) from exc

    # ── Validation ────────────────────────────────────────────────

    def _validate(self) -> None:
        cfg = self._raw

        _validate_type("ASSISTANT_NAME", cfg.ASSISTANT_NAME, str)
        _validate_type("WAKE_WORD", cfg.WAKE_WORD, str)
        if not cfg.ASSISTANT_NAME.strip():
            raise ConfigError("ASSISTANT_NAME cannot be empty")
        if not cfg.WAKE_WORD.strip():
            raise ConfigError("WAKE_WORD cannot be empty")

        _validate_type("VOICE_RATE", cfg.VOICE_RATE, int)
        _validate_range("VOICE_RATE", cfg.VOICE_RATE, 50, 400)
        _validate_type("VOICE_INDEX", cfg.VOICE_INDEX, int)
        _validate_range("VOICE_INDEX", cfg.VOICE_INDEX, 0, 10)

        _validate_type("LISTEN_TIMEOUT", cfg.LISTEN_TIMEOUT, int)
        _validate_range("LISTEN_TIMEOUT", cfg.LISTEN_TIMEOUT, 1, 60)
        _validate_type("PHRASE_TIME_LIMIT", cfg.PHRASE_TIME_LIMIT, int)
        _validate_range("PHRASE_TIME_LIMIT", cfg.PHRASE_TIME_LIMIT, 1, 120)

        valid_modes = {"voice", "text", "auto"}
        if cfg.INPUT_MODE not in valid_modes:
            raise ConfigError(
                f"INPUT_MODE must be one of {valid_modes}, got '{cfg.INPUT_MODE}'",
                details={"field": "INPUT_MODE", "value": cfg.INPUT_MODE},
            )

        _validate_type("CONTEXT_HISTORY_SIZE", cfg.CONTEXT_HISTORY_SIZE, int)
        _validate_range("CONTEXT_HISTORY_SIZE", cfg.CONTEXT_HISTORY_SIZE, 1, 50)

        _validate_type("REMINDER_CHECK_INTERVAL", cfg.REMINDER_CHECK_INTERVAL, int)
        _validate_range("REMINDER_CHECK_INTERVAL", cfg.REMINDER_CHECK_INTERVAL, 5, 3600)

        log.debug("All config fields validated.")

    # ── Attribute Access ──────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the raw config module.
        For API key fields, os.environ is checked first so .env wins.
        """
        # API keys — always prefer environment variable (set by .env)
        _env_priority_keys = {
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "HUGGINGFACE_API_KEY",
            "ANTHROPIC_API_KEY",
        }
        if name in _env_priority_keys:
            env_val = os.environ.get(name, "").strip()
            if env_val:
                return env_val
            # Fall through to config.py value
        try:
            return getattr(self._raw, name)
        except AttributeError:
            raise ConfigError(
                f"Config field '{name}' does not exist in config.py",
                details={"field": name},
            )

    def get(self, name: str, default: Any = None) -> Any:
        """Safely get a config value with a default."""
        # API keys — env first
        _env_priority_keys = {
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "HUGGINGFACE_API_KEY",
            "ANTHROPIC_API_KEY",
        }
        if name in _env_priority_keys:
            env_val = os.environ.get(name, "").strip()
            if env_val:
                return env_val
        return getattr(self._raw, name, default)

    # ── Computed Properties ───────────────────────────────────────

    @property
    def has_openrouter(self) -> bool:
        key = os.environ.get("OPENROUTER_API_KEY", "") or \
              getattr(self._raw, "OPENROUTER_API_KEY", "")
        return bool(key.strip())

    @property
    def has_huggingface(self) -> bool:
        key = os.environ.get("HUGGINGFACE_API_KEY", "") or \
              getattr(self._raw, "HUGGINGFACE_API_KEY", "")
        return bool(key.strip())

    @property
    def has_openai(self) -> bool:
        key = os.environ.get("OPENAI_API_KEY", "") or \
              getattr(self._raw, "OPENAI_API_KEY", "")
        return bool(key.strip())

    @property
    def has_anthropic(self) -> bool:
        key = os.environ.get("ANTHROPIC_API_KEY", "") or \
              getattr(self._raw, "ANTHROPIC_API_KEY", "")
        return bool(key.strip())

    @property
    def has_cloud_llm(self) -> bool:
        return self.has_openrouter or self.has_huggingface or \
               self.has_openai or self.has_anthropic

    @property
    def has_ollama_config(self) -> bool:
        url = getattr(self._raw, "OLLAMA_BASE_URL", "http://localhost:11434")
        return bool(url.strip())

    @property
    def ollama_base_url(self) -> str:
        return getattr(self._raw, "OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def ollama_model(self) -> str:
        return getattr(self._raw, "OLLAMA_MODEL", "mistral")

    @property
    def log_dir_path(self) -> Path:
        return Path(getattr(self._raw, "LOG_DIR", "logs")).resolve()

    @property
    def memory_file_path(self) -> Path:
        return Path(getattr(self._raw, "MEMORY_FILE", "memory/memory.json")).resolve()

    @property
    def reminders_file_path(self) -> Path:
        return Path(getattr(self._raw, "REMINDERS_FILE", "reminders/reminders.json")).resolve()

    @property
    def screenshot_dir_path(self) -> Path:
        return Path(getattr(self._raw, "SCREENSHOT_DIR", "screenshots")).resolve()

    def __repr__(self) -> str:
        return (
            f"WednesdayConfig("
            f"wake_word={self.WAKE_WORD!r}, "
            f"input_mode={self.INPUT_MODE!r}, "
            f"has_cloud_llm={self.has_cloud_llm}, "
            f"has_ollama={self.has_ollama_config})"
        )


# ═════════════════════════════════════════════════════════════════
#  Global Singleton
# ═════════════════════════════════════════════════════════════════

def _create_cfg() -> _WednesdayConfig:
    try:
        return _WednesdayConfig()
    except ConfigError as exc:
        import logging
        logging.getLogger("core.config_loader").critical(
            f"FATAL: Configuration error: {exc.message}"
        )
        raise


cfg: _WednesdayConfig = _create_cfg()