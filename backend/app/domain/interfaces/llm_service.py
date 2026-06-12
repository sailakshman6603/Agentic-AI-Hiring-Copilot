from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class ILLMService(ABC):
    @abstractmethod
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        pass

    @abstractmethod
    def generate_json(
        self, 
        prompt: str, 
        response_schema: Type[BaseModel],
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> BaseModel:
        pass
