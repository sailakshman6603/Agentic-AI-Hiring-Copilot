import logging
from typing import List, Dict, Any
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config.settings import settings
from app.domain.interfaces.vector_store import IVectorStore
from app.infrastructure.ai.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class QdrantStore(IVectorStore):
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.collection_name = settings.QDRANT_COLLECTION
        self.dimension = embedding_service.dimension
        self.client = None
        self._in_memory_db: Dict[str, Dict[str, Any]] = {}  # Fallback DB

        try:
            logger.info(f"Connecting to Qdrant at {self.host}:{self.port}...")
            # We add a short timeout so it fails quickly if Qdrant is not running
            self.client = QdrantClient(host=self.host, port=self.port, timeout=3.0)
            self._ensure_collection()
            logger.info("Qdrant store initialized successfully.")
        except Exception as e:
            logger.warning(
                f"Could not connect to Qdrant: {e}. "
                "Using local in-memory fallback vector storage."
            )
            self.client = None

    def _ensure_collection(self):
        if not self.client:
            return
        
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.dimension,
                    distance=qmodels.Distance.COSINE
                )
            )

    def upsert_resume(
        self, 
        resume_id: UUID, 
        vector: List[float], 
        metadata: Dict[str, Any]
    ) -> bool:
        # Convert UUID to string for storage
        res_id_str = str(resume_id)
        
        if self.client:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        qmodels.PointStruct(
                            id=res_id_str,
                            vector=vector,
                            payload=metadata
                        )
                    ]
                )
                return True
            except Exception as e:
                logger.error(f"Failed to upsert to Qdrant: {e}. Storing in memory fallback...")

        # In-memory fallback
        self._in_memory_db[res_id_str] = {
            "vector": vector,
            "metadata": metadata
        }
        return True

    def search_similar_resumes(
        self, 
        vector: List[float], 
        organization_id: UUID, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        org_id_str = str(organization_id)
        
        if self.client:
            try:
                # Setup payload filtering to isolate tenants
                qdrant_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="organization_id",
                            match=qmodels.MatchValue(value=org_id_str)
                        )
                    ]
                )
                
                if hasattr(self.client, "query_points"):
                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        query=vector,
                        query_filter=qdrant_filter,
                        limit=limit
                    )
                    results = response.points
                else:
                    results = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=vector,
                        query_filter=qdrant_filter,
                        limit=limit
                    )
                
                return [
                    {
                        "resume_id": UUID(r.id),
                        "score": r.score,
                        "metadata": r.payload
                    }
                    for r in results
                ]
            except Exception as e:
                logger.error(f"Qdrant search failed: {e}. Querying in-memory fallback...")

        # In-memory fallback: Cosine Similarity match
        matches = []
        for res_id, data in self._in_memory_db.items():
            meta = data["metadata"]
            if str(meta.get("organization_id")) != org_id_str:
                continue
            
            stored_vector = data["vector"]
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(vector, stored_vector))
            norm_a = sum(a * a for a in vector) ** 0.5
            norm_b = sum(b * b for b in stored_vector) ** 0.5
            
            score = dot_product / (norm_a * norm_b) if norm_a * norm_b > 0 else 0.0
            matches.append({
                "resume_id": UUID(res_id),
                "score": score,
                "metadata": meta
            })
            
        # Sort by score desc
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    def delete_resume(self, resume_id: UUID) -> bool:
        res_id_str = str(resume_id)
        
        if self.client:
            try:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=qmodels.PointIdsList(points=[res_id_str])
                )
                return True
            except Exception as e:
                logger.error(f"Qdrant delete failed: {e}")

        if res_id_str in self._in_memory_db:
            del self._in_memory_db[res_id_str]
            
        return True


# Singleton instance
qdrant_store = QdrantStore()
