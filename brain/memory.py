"""
Wednesday - Memory System
Short-term (RAM) and long-term (JSON file) memory.
"""

import json
import os
import config


class ShortTermMemory:
    """In-memory storage that lasts for the current session."""

    def __init__(self, max_items: int = 50):
        self._store = {}
        self._history = []
        self.max_items = max_items

    def set(self, key: str, value):
        self._store[key.lower()] = value

    def get(self, key: str, default=None):
        return self._store.get(key.lower(), default)

    def add_exchange(self, user_input: str, response: str):
        self._history.append({"user": user_input, "assistant": response})
        if len(self._history) > self.max_items:
            self._history = self._history[-self.max_items:]

    def get_recent_history(self, n: int = 5) -> list:
        return self._history[-n:]

    def clear(self):
        self._store.clear()
        self._history.clear()


class LongTermMemory:
    """Persistent memory backed by a JSON file."""

    def __init__(self):
        self._file = os.path.join(config.MEMORY_DIR, "long_term.json")
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"facts": {}, "preferences": {}}
        return {"facts": {}, "preferences": {}}

    def _save(self):
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def store_fact(self, key: str, value: str):
        self._data["facts"][key.lower()] = value
        self._save()

    def get_fact(self, key: str) -> str | None:
        return self._data["facts"].get(key.lower())

    def store_preference(self, key: str, value: str):
        self._data["preferences"][key.lower()] = value
        self._save()

    def get_preference(self, key: str) -> str | None:
        return self._data["preferences"].get(key.lower())

    def get_all_facts(self) -> dict:
        return dict(self._data["facts"])

    def get_context_string(self) -> str:
        """Return a string summary of known facts for AI context."""
        if not self._data["facts"]:
            return ""
        lines = [f"{k}: {v}" for k, v in self._data["facts"].items()]
        return "Known facts about the user: " + "; ".join(lines)
