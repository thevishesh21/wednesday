"""
WEDNESDAY AI OS — Config Loader & Validator
A validated wrapper around the existing config.py.

config.py is NEVER modified. This module reads all values from it,
validates types and ranges using Pydantic, and exposes a typed `cfg`
object with additional computed properties.

Usage:
    from core.config_loader import cfg

    print(cfg.WAKE_WORD)         # "hey wednesday"
    print(cfg.has_cloud_llm)     # True/False based on API keys
    print(cfg.log_dir_path)      # Resolved pathlib.Path

All values are the same names as config.py — zero refactor needed
in existing code that already reads config directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.exceptions import ConfigError
from core.logger import get_logger

log = get_logger("core.config_loader")


# ═════════════════════════════════════════════════════════════════
#  Validation Helpers
# ═════════════════════════════════════════════════════════════════

def _validate_range(
    field: str, value: int | float, lo: int | float, hi: int | float
) -> None:
    """Raise ConfigError if value is outside [lo, hi]."""
    if not (lo <= value <= hi):
        raise ConfigError(
            f"Config field '{field}' must be between {lo} and {hi}, got {value}",
            details={"field": field, "value": value, "min": lo, "max": hi},
        )


def _validate_type(field: str, value: Any, expected: type) -> None:
    """Raise ConfigError if value is not an instance of expected type."""
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

    Reads from config.py at instantiation, validates all critical fields,
    and exposes them as typed attributes plus computed convenience properties.

    Raises:
        ConfigError: If any critical configuration value is invalid.
    """

    def __init__(self) -> None:
        self._raw = self._load_raw_config()
        self._validate()
        log.info("Configuration loaded and validated successfully.")

    # ── Load raw config ───────────────────────────────────────────

    def _load_raw_config(self) -> Any:
        """Import the raw config module."""
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
        """Validate all critical config fields."""
        cfg = self._raw

        # Assistant identity
        _validate_type("ASSISTANT_NAME", cfg.ASSISTANT_NAME, str)
        _validate_type("WAKE_WORD", cfg.WAKE_WORD, str)
        if not cfg.ASSISTANT_NAME.strip():
            raise ConfigError("ASSISTANT_NAME cannot be empty")
        if not cfg.WAKE_WORD.strip():
            raise ConfigError("WAKE_WORD cannot be empty")

        # Voice settings
        _validate_type("VOICE_RATE", cfg.VOICE_RATE, int)
        _validate_range("VOICE_RATE", cfg.VOICE_RATE, 50, 400)
        _validate_type("VOICE_INDEX", cfg.VOICE_INDEX, int)
        _validate_range("VOICE_INDEX", cfg.VOICE_INDEX, 0, 10)

        # Listener settings
        _validate_type("LISTEN_TIMEOUT", cfg.LISTEN_TIMEOUT, int)
        _validate_range("LISTEN_TIMEOUT", cfg.LISTEN_TIMEOUT, 1, 60)
        _validate_type("PHRASE_TIME_LIMIT", cfg.PHRASE_TIME_LIMIT, int)
        _validate_range("PHRASE_TIME_LIMIT", cfg.PHRASE_TIME_LIMIT, 1, 120)

        # Input mode
        valid_modes = {"voice", "text", "auto"}
        if cfg.INPUT_MODE not in valid_modes:
            raise ConfigError(
                f"INPUT_MODE must be one of {valid_modes}, got '{cfg.INPUT_MODE}'",
                details={"field": "INPUT_MODE", "value": cfg.INPUT_MODE},
            )

        # Context history
        _validate_type("CONTEXT_HISTORY_SIZE", cfg.CONTEXT_HISTORY_SIZE, int)
        _validate_range("CONTEXT_HISTORY_SIZE", cfg.CONTEXT_HISTORY_SIZE, 1, 50)

        # Reminder interval
        _validate_type("REMINDER_CHECK_INTERVAL", cfg.REMINDER_CHECK_INTERVAL, int)
        _validate_range("REMINDER_CHECK_INTERVAL", cfg.REMINDER_CHECK_INTERVAL, 5, 3600)

        log.debug("All config fields validated.")

    # ── Attribute Access ──────────────────────────────────────────

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the raw config module.
        Allows cfg.WAKE_WORD, cfg.OPENROUTER_API_KEY, etc.
        """
        try:
            return getattr(self._raw, name)
        except AttributeError:
            raise ConfigError(
                f"Config field '{name}' does not exist in config.py",
                details={"field": name},
            )

    def get(self, name: str, default: Any = None) -> Any:
        """
        Safely get a config value with a default.

        Args:
            name:    Config field name.
            default: Value to return if field doesn't exist.

        Returns:
            Config value or default.
        """
        return getattr(self._raw, name, default)

    # ── Computed Properties ───────────────────────────────────────

    @property
    def has_openrouter(self) -> bool:
        """True if an OpenRouter API key is configured."""
        return bool(getattr(self._raw, "OPENROUTER_API_KEY", "").strip())

    @property
    def has_huggingface(self) -> bool:
        """True if a HuggingFace API key is configured."""
        return bool(getattr(self._raw, "HUGGINGFACE_API_KEY", "").strip())

    @property
    def has_openai(self) -> bool:
        """True if an OpenAI API key is configured."""
        return bool(getattr(self._raw, "OPENAI_API_KEY", "").strip())

    @property
    def has_anthropic(self) -> bool:
        """True if an Anthropic API key is configured."""
        return bool(getattr(self._raw, "ANTHROPIC_API_KEY", "").strip())

    @property
    def has_cloud_llm(self) -> bool:
        """True if any cloud LLM API key is configured."""
        return self.has_openrouter or self.has_huggingface or \
               self.has_openai or self.has_anthropic

    @property
    def has_ollama_config(self) -> bool:
        """True if an Ollama base URL is configured (defaults to localhost)."""
        url = getattr(self._raw, "OLLAMA_BASE_URL", "http://localhost:11434")
        return bool(url.strip())

    @property
    def ollama_base_url(self) -> str:
        """Ollama server URL, defaulting to localhost."""
        return getattr(self._raw, "OLLAMA_BASE_URL", "http://localhost:11434")

    @property
    def ollama_model(self) -> str:
        """Ollama model name, defaulting to mistral."""
        return getattr(self._raw, "OLLAMA_MODEL", "mistral")

    @property
    def log_dir_path(self) -> Path:
        """Resolved absolute Path to the log directory."""
        log_dir = getattr(self._raw, "LOG_DIR", "logs")
        return Path(log_dir).resolve()

    @property
    def memory_file_path(self) -> Path:
        """Resolved absolute Path to the memory JSON file."""
        mem_file = getattr(self._raw, "MEMORY_FILE", "memory/memory.json")
        return Path(mem_file).resolve()

    @property
    def reminders_file_path(self) -> Path:
        """Resolved absolute Path to the reminders JSON file."""
        rem_file = getattr(self._raw, "REMINDERS_FILE", "reminders/reminders.json")
        return Path(rem_file).resolve()

    @property
    def screenshot_dir_path(self) -> Path:
        """Resolved absolute Path to the screenshots directory."""
        ss_dir = getattr(self._raw, "SCREENSHOT_DIR", "screenshots")
        return Path(ss_dir).resolve()

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
    """Create the config singleton, with graceful error on failure."""
    try:
        return _WednesdayConfig()
    except ConfigError as exc:
        # Use basic logging since structured logger may not be ready
        import logging
        logging.getLogger("core.config_loader").critical(
            f"FATAL: Configuration error: {exc.message}"
        )
        raise


#: The single validated configuration object for the entire system.
#: Import this everywhere: ``from core.config_loader import cfg``
cfg: _WednesdayConfig = _create_cfg()
