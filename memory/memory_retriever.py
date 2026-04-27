"""
WEDNESDAY AI OS — Memory Retriever
Semantic search: query -> top-k MemoryRecord.
Combines short-term (flat dict) and long-term (vector) memory.
"""

from typing import List
from core.interfaces import MemoryRecord
from memory.short_term import short_term
from memory.long_term import long_term
from memory.embedder import embedder

class MemoryRetriever:
    @staticmethod
    async def retrieve(query: str, top_k: int = 5) -> List[MemoryRecord]:
        """Fetch relevant memories from both stores."""
        records = []
        
        # 1. Fetch from Vector DB
        lt_records = await long_term.retrieve(query, top_k=top_k)
        records.extend(lt_records)
        
        # 2. Add some relevant Short Term (hacky text match for now)
        # Ideally, we embed short term keys too, but for simplicity:
        from memory.memory import get_all
        st_dict = get_all()
        query_words = query.lower().split()
        
        for k, v in st_dict.items():
            if any(w in k.lower() for w in query_words):
                records.append(MemoryRecord(
                    id=k,
                    content=f"{k}: {v}",
                    metadata={"type": "preference"},
                    source="short_term_memory"
                ))
                
        return records

memory_retriever = MemoryRetriever()
