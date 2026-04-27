"""
WEDNESDAY AI OS — Short-Term Memory
Thin wrapper around the existing memory implementation.
"""

# We just re-export the existing functions to keep the API consistent
# We just re-export the existing functions to keep the API consistent
from memory.memory import (
    save,
    recall,
    get_all,
)

class ShortTermMemory:
    @staticmethod
    def add(key: str, value: str):
        save(key, value)
        
    @staticmethod
    def get(key: str) -> str:
        # recall returns a formatted string like "key is value", we want raw
        # but get_all gives raw dict
        raw_dict = get_all()
        return raw_dict.get(key.lower(), "")

short_term = ShortTermMemory()
