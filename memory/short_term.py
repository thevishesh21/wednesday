"""
memory/short_term.py
---------------------
Rolling in-memory conversation buffer.

Stores the last N message pairs as a deque.
Thread-safe. Compatible with OpenAI and Anthropic message formats.
"""

import threading
from collections import deque
from typing import Optional
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class ShortTermMemory:
    """
    Rolling conversation buffer for active session memory.

    Thread-safe (uses a lock for the deque operations).
    """

    def __init__(self, max_messages: Optional[int] = None):
        self._limit = max_messages or settings.memory.short_term_limit
        self._buffer: deque = deque(maxlen=self._limit)
        self._lock = threading.Lock()
        logger.debug(f"ShortTermMemory ready (max={self._limit})")

    def add(self, role: str, content: str) -> None:
        """Add a message. Role must be 'user' or 'assistant'."""
        if role not in ("user", "assistant", "system"):
            logger.warning(f"Unexpected role '{role}' — storing anyway.")
        if not content or not content.strip():
            return
        with self._lock:
            self._buffer.append({"role": role, "content": content.strip()})

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def get_messages(self) -> list[dict]:
        """Return all messages as a list (oldest → newest). Thread-safe copy."""
        with self._lock:
            return list(self._buffer)

    def get_last_n(self, n: int) -> list[dict]:
        """Return the most recent N messages."""
        with self._lock:
            msgs = list(self._buffer)
        return msgs[-n:] if n < len(msgs) else msgs

    def get_last_user_message(self) -> Optional[str]:
        """Return the text of the most recent user message."""
        with self._lock:
            for msg in reversed(self._buffer):
                if msg["role"] == "user":
                    return msg["content"]
        return None

    def clear(self) -> None:
        """Clear all messages."""
        with self._lock:
            self._buffer.clear()
        logger.info("Short-term memory cleared.")

    def summary_str(self) -> str:
        """Human-readable memory dump for debugging."""
        with self._lock:
            msgs = list(self._buffer)
        if not msgs:
            return "  (empty)"
        lines = []
        for i, msg in enumerate(msgs):
            icon = "👤" if msg["role"] == "user" else "🤖"
            content = msg["content"][:100]
            if len(msg["content"]) > 100:
                content += "..."
            lines.append(f"  [{i:2d}] {icon} {content}")
        return "\n".join(lines)

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)

    def __repr__(self) -> str:
        return f"ShortTermMemory(messages={len(self)}, limit={self._limit})"
