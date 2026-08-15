from typing import List
from engine.types import ExecutionPlan, PostExecutionResult
from tools.registry import ToolRegistry
from engine.tool_contract import ToolContract


class Validator:
    """Validates ExecutionPlan against tool contracts."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def validate(self, plan: ExecutionPlan, user_query: str = "") -> ExecutionPlan:
        errors = []

        if plan.tool == "unknown":
            errors.append("No tool identified for this query")
        elif not self.registry.get(plan.tool):
            errors.append(f"Tool '{plan.tool}' is not registered")
        else:
            tool = self.registry.get(plan.tool)
            contract: ToolContract = tool.contract

            # Operation check
            if plan.operation and not contract.supports_operation(plan.operation):
                errors.append(
                    f"Operation mismatch: '{plan.tool}' does not support "
                    f"'{plan.operation}'. Supported: {contract.supported_operations}"
                )

            # Capability check
            if plan.requested_capability and not contract.supports_capability(plan.requested_capability):
                errors.append(
                    f"Capability mismatch: requested '{plan.requested_capability}' "
                    f"but tool only supports {contract.capabilities}"
                )

            # Argument validation
            errors.extend(contract.validate_arguments(plan.arguments))

        if plan.confidence < 0.3:
            errors.append(f"Confidence too low: {plan.confidence}")

        if errors:
            plan.validation_status = "failed"
            plan.validation_errors = errors
        else:
            plan.validation_status = "passed"

        return plan

    def post_validate(self, plan, response) -> PostExecutionResult:
        tool = self.registry.get(plan.tool)
        if not tool:
            result = PostExecutionResult()
            result.integrity = False
            result.integrity_errors.append(f"Tool '{plan.tool}' not found for post-validation")
            return result

        if hasattr(tool, 'validate_result'):
            return tool.validate_result(plan, response.result or {})

        return PostExecutionResult()