import logging
import numpy as np
from typing import List
from app.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = None
        self.dimension = 384  # Default for BGE-small or MiniLM-L6-v2
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            # Try to get dimension from model
            if hasattr(self.model, "get_embedding_dimension"):
                self.dimension = self.model.get_embedding_dimension()
            elif hasattr(self.model, "get_sentence_embedding_dimension"):
                self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.warning(
                f"Failed to load sentence-transformers model '{self.model_name}' due to: {e}. "
                "Using fallback keyword-hashing embedding service."
            )
            self.model = None

    def get_embedding(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        if self.model is not None:
            try:
                embedding = self.model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error generating transformer embedding: {e}. Falling back...")
        
        # Fallback implementation: Generate a deterministic mock vector based on string hash
        return self._generate_fallback_vector(text)

    def _generate_fallback_vector(self, text: str) -> List[float]:
        # Generate a deterministic vector using seed from hash of the text
        seed = abs(hash(text)) % (2**32 - 1)
        rng = np.random.default_rng(seed)
        
        # Generate random values, then normalize
        vector = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()


# Singleton instance
embedding_service = EmbeddingService()
