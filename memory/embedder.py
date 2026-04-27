"""
WEDNESDAY AI OS — Text Embedder
Uses sentence-transformers to convert text into dense vectors.
"""

from core.logger import get_logger

log = get_logger("memory.embedder")

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        
    def _load_model(self):
        if self._model is None:
            log.info(f"Loading embedding model: {self.model_name}...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                log.error("sentence-transformers not installed. Embeddings will be disabled.")
                self._model = "DISABLED"
            except Exception as e:
                log.error(f"Failed to load embedding model: {e}")
                self._model = "DISABLED"
                
    def embed(self, text: str) -> list[float]:
        """Convert a string into a float vector."""
        self._load_model()
        
        if self._model == "DISABLED":
            # Fallback mock embedding (so the system doesn't crash)
            return [0.0] * 384
            
        return self._model.encode(text).tolist()

embedder = Embedder()
