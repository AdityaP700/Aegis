from abc import ABC,abstractmethod
from engine.types import ExecutionPlan

class BaseBrain(ABC):
    """Every Brain must follow this contract."""

    @abstractmethod
    #accepting the user_query as usual
    def think(self, user_query: str) -> ExecutionPlan:

        pass

    @property
    @abstractmethod
    # we have some of the providers hence ,we will redirect to them
    def provider_name(self) -> str:
        """Name of the LLM provider."""
        pass
