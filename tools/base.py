from abc import ABC ,abstractmethod
from engine.types import ExecutionPlan, PostExecutionResult
from typing import List,Dict,Any

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

    @property
    @abstractmethod
    def execute(self, request, trace: list) -> Dict[str, Any]:
        pass

    def validate_result(self, plan: ExecutionPlan, result: Dict[str, Any]) -> PostExecutionResult:
        """
        Validate the tool's result against the plan.
        Override in each tool for domain-specific checks.
        Default: pass everything.
        """
        return PostExecutionResult()

    @property
    @abstractmethod
    def description(self) -> str:
        """What this tool does."""
        pass
