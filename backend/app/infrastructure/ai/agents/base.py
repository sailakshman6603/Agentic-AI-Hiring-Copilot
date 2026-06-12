from abc import ABC, abstractmethod
from typing import Dict, Any
from app.domain.interfaces.llm_service import ILLMService


class BaseAgent(ABC):
    def __init__(self, llm_service: ILLMService):
        self.llm_service = llm_service

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent logic.
        
        Args:
            state: The current LangGraph state dictionary.
            
        Returns:
            A dictionary containing the keys to update in the graph state.
        """
        pass
class AgentExecutionException(Exception):
    pass
