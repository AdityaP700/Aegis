from abc import ABC ,abstractmethod
from engine.types import ExecutionPlan, PostExecutionResult
from typing import List,Dict,Any
from engine.tool_contract import ToolContract

class BaseTool(ABC):
    @property
    @abstractmethod
    def contract(self)->ToolContract:
        pass

    @property
    def name(self)->str:
        return self.contract.name

    @property

    def description(self) -> str:
        """What this tool does."""
        return self.contract.description

    @property

    def capabilities(self) -> List[str]:     # ← NEW
        """List of capabilities this tool supports.
        Can this tool actually perform what the user asked?
        """
        return self.contract.capabilities

    @property
    def supported_operations(self)->List[str]:
        return self.contract.supported_operations

    @property
  
    def required_args(self) -> List[str]:
        """Required arguments for this tool."""
        return self.contract.required_args

    @property
    def argument_types(self) -> Dict[str, Any]:
        """Get argument types from contract."""
        return self.contract.argument_types

    @property
    def output_schema(self) -> Dict[str, Any]:
        """Get output schema from contract."""
        return self.contract.output_schema

    @property
    def retry_policy(self) -> str:
        """Get retry policy from contract."""
        return self.contract.retry_policy

    @property
    def timeout_seconds(self) -> float:
        """Get timeout from contract."""
        return self.contract.timeout_seconds

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
        # to Check output schema fields
        for field in self.contract.output_schema:
            if field not in result:
                post.integrity = False
                post.integrity_errors.append(f"Missing output field: '{field}'")

        return post
