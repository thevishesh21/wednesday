"""
memory/long_term.py
-------------------
Persistent vector memory using ChromaDB.
STUB — Full implementation in Phase 3.
"""
from utils.logger import setup_logger
logger = setup_logger(__name__)

class LongTermMemory:
    """Phase 3: ChromaDB-backed semantic memory store."""
    async def store(self, text: str, metadata: dict = None): pass
    async def retrieve(self, query: str, top_k: int = 5) -> list: return []
