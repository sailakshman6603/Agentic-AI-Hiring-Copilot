from abc import ABC, abstractmethod
from typing import List, Dict, Any
from uuid import UUID


class IVectorStore(ABC):
    @abstractmethod
    def upsert_resume(
        self, 
        resume_id: UUID, 
        vector: List[float], 
        metadata: Dict[str, Any]
    ) -> bool:
        pass

    @abstractmethod
    def search_similar_resumes(
        self, 
        vector: List[float], 
        organization_id: UUID, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_resume(self, resume_id: UUID) -> bool:
        pass
