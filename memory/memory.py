"""
Wednesday AI Assistant — Memory System
Persistent JSON-based memory for storing user info, preferences, and notes.
"""

import json
import os
from utils.logger import get_logger
import config

log = get_logger("memory")

_memory_data: dict = {}


def _load() -> None:
    """Load memory from JSON file."""
    global _memory_data
    try:
        if os.path.exists(config.MEMORY_FILE):
            with open(config.MEMORY_FILE, "r", encoding="utf-8") as f:
                _memory_data = json.load(f)
            log.info(f"Memory loaded: {len(_memory_data)} entries")
        else:
            _memory_data = {}
            _save()
            log.info("Memory file created (empty).")
    except Exception as e:
        log.error(f"Memory load failed: {e}")
        _memory_data = {}


def _save() -> None:
    """Save memory to JSON file."""
    try:
        os.makedirs(os.path.dirname(config.MEMORY_FILE) or ".", exist_ok=True)
        with open(config.MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_data, f, indent=2, ensure_ascii=False)
        log.debug("Memory saved.")
    except Exception as e:
        log.error(f"Memory save failed: {e}")


def save(key: str, value) -> str:
    """
    Save a key-value pair to memory.

    Args:
        key: The key (e.g. "name", "favorite_language")
        value: The value to store
    """
    _memory_data[key.lower().strip()] = value
    _save()
    log.info(f"Memory saved: {key} = {value}")
    return f"Yaad rakh liya, boss! {key} = {value}"


def recall(key: str) -> str:
    """
    Recall a value from memory.

    Args:
        key: The key to look up
    """
    key = key.lower().strip()
    value = _memory_data.get(key)
    if value is not None:
        log.info(f"Memory recalled: {key} = {value}")
        return f"{key} is {value}, boss."
    else:
        log.info(f"Memory miss: {key}")
        return f"Sorry boss, '{key}' yaad nahi hai mujhe."


def forget(key: str) -> str:
    """Remove a key from memory."""
    key = key.lower().strip()
    if key in _memory_data:
        del _memory_data[key]
        _save()
        log.info(f"Memory forgot: {key}")
        return f"Bhool gayi boss, '{key}' hata diya."
    return f"'{key}' toh tha hi nahi memory mein."


def list_all() -> str:
    """List everything in memory."""
    if not _memory_data:
        return "Memory khaali hai, boss. Kuch yaad karwao!"
    items = [f"{k}: {v}" for k, v in _memory_data.items()]
    return "Memory mein hai: " + ", ".join(items[:10])


def get_all() -> dict:
    """Return raw memory dict."""
    return _memory_data.copy()


# ── Load memory on import ───────────────────────────────────────
_load()
