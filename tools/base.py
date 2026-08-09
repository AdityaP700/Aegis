from abc import ABC ,abstractmethod
from engine.types import ExecutionRequest,ExecutionResponse
#"Every tool should have these methods."
from typing import List

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self)->str:
        pass
    """added capabilities as one of the properties to the baseTool"""
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:     # ← NEW
        """List of capabilities this tool supports.
        Can this tool actually perform what the user asked?
        """
        pass

    @property
    @abstractmethod
    def required_args(self) -> List[str]:
        """Required arguments for this tool."""
        pass

    @abstractmethod
    def execute(
        self,
        request:ExecutionRequest
    )->ExecutionResponse:
      pass

    @abstractmethod
    def description(self) -> str:
        """What this tool does."""
        pass
