"""
WEDNESDAY AI OS — Preference Store
JSON/dict mapping for explicit user preferences (e.g. "my name is X", "I like Y").
This is basically handled by short_term, but this interface provides specific
getters/setters for user persona data.
"""

from memory.short_term import short_term

class PreferenceStore:
    @staticmethod
    def set_preference(key: str, value: str):
        short_term.add(f"pref_{key}", value)
        
    @staticmethod
    def get_preference(key: str, default: str = "") -> str:
        val = short_term.get(f"pref_{key}")
        return val if val else default

preferences = PreferenceStore()
