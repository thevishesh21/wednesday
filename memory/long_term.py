"""
WEDNESDAY AI OS — Long-Term Memory
ChromaDB vector store implementation of IMemoryStore.
"""

import os
import uuid
import datetime
from pathlib import Path

from core.interfaces import IMemoryStore, MemoryRecord
from core.logger import get_logger
from memory.embedder import embedder

log = get_logger("memory.long_term")

class LongTermMemory(IMemoryStore):
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in the same directory as the SQLite DB
            db_path = str(Path(__file__).parent / "chroma_db")
            
        self.db_path = db_path
        self.collection_name = "wednesday_memory"
        self._client = None
        self._collection = None
        self._available = True
        
        self._init_db()
        
    def _init_db(self):
        try:
            import chromadb
            # Use persistent client so memories survive restart
            self._client = chromadb.PersistentClient(path=self.db_path)
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
            log.info(f"ChromaDB initialized at {self.db_path}")
        except ImportError:
            log.warning("chromadb not installed. Long-term memory disabled.")
            self._available = False
        except Exception as e:
            log.error(f"Failed to initialize ChromaDB: {e}")
            self._available = False
            
    async def store(self, content: str, metadata: dict | None = None) -> str:
        if not self._available: return ""
        
        meta = metadata or {}
        if "timestamp" not in meta:
            meta["timestamp"] = datetime.datetime.now().isoformat()
            
        mem_id = str(uuid.uuid4())
        embedding = embedder.embed(content)
        
        try:
            self._collection.add(
                ids=[mem_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            return mem_id
        except Exception as e:
            log.error(f"Failed to store memory: {e}")
            return ""

    async def retrieve(self, query: str, top_k: int = 5) -> list[MemoryRecord]:
        if not self._available: return []
        
        embedding = embedder.embed(query)
        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=top_k
            )
            
            records = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    records.append(MemoryRecord(
                        id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i],
                        source="long_term_memory"
                    ))
            return records
        except Exception as e:
            log.error(f"Failed to retrieve memory: {e}")
            return []

long_term = LongTermMemory()
