from abc import ABC ,abstractmethod
from engine.types import ExecutionRequest,ExecutionResponse
#"Every tool should have these methods."

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self)->str:
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
