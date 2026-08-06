from typing import List
from engine.types import ExecutionPlan
from tools.registry import ToolRegistry

class Validator:
    """
    Validates ExecutionPlan against tool registry.
    Checks tool existence, required arguments, types, and plausibility.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def validate(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Validate an ExecutionPlan.
        Modifies plan in-place and returns it.

        Args:
            plan: ExecutionPlan to validate

        Returns:
            Validated ExecutionPlan (with validation_status updated)
        """
        errors = []

        # Check 1: Does tool exist?
        if plan.tool == "unknown":
            errors.append("No tool identified for this query")
        elif not self.registry.get(plan.tool):
            errors.append(f"Tool '{plan.tool}' is not registered")
        else:
            # Check 2: Required arguments present?
            tool = self.registry.get(plan.tool)
            required_args = self._get_required_args(plan.tool)

            for arg in required_args:
                if arg not in plan.arguments or not plan.arguments[arg]:
                    errors.append(f"Missing required argument: '{arg}'")

            # Check 3: Argument types correct?
            errors.extend(self._validate_argument_types(plan))

            # Check 4: Plausibility checks
            errors.extend(self._validate_plausibility(plan))

        # Check 5: Confidence threshold
        if plan.confidence < 0.3:
            errors.append(f"Confidence too low: {plan.confidence}")

        # Update plan
        if errors:
            plan.validation_status = "failed"
            plan.validation_errors = errors
        else:
            plan.validation_status = "passed"

        return plan

    def _get_required_args(self, tool_name: str) -> List[str]:
        """Get required arguments for a tool."""
        # This could be pulled from tool metadata
        required_args_map = {
            "weather": ["city"],
            "github": ["repo"],
            "search": ["query"],
            "calculator": ["expression"]
        }
        return required_args_map.get(tool_name, [])

    def _validate_argument_types(self, plan: ExecutionPlan) -> List[str]:
        """Validate argument types."""
        errors = []

        if plan.tool == "weather":
            city = plan.arguments.get("city", "")
            if city and not isinstance(city, str):
                errors.append(f"'city' must be a string, got {type(city).__name__}")
            if city and city.strip().isdigit():
                errors.append(f"'city' looks like a number, not a city name: '{city}'")

        elif plan.tool == "github":
            repo = plan.arguments.get("repo", "")
            if repo and "/" not in repo:
                errors.append(f"'repo' must be in 'owner/repo' format, got: '{repo}'")

        elif plan.tool == "search":
            query = plan.arguments.get("query", "")
            if query and len(query) < 3:
                errors.append(f"Search query too short: '{query}'")

        return errors

    def _validate_plausibility(self, plan: ExecutionPlan) -> List[str]:
        """Plausibility checks — does this tool even make sense?"""
        errors = []

        # Example: If user asked about Python but Brain chose weather — reject
        # This is a simple heuristic; in production, use embeddings
        city_keywords = ["weather", "temperature", "rain", "sunny", "cold", "hot"]
        github_keywords = ["github", "repo", "stars", "repository", "fork"]

        if plan.tool == "weather":
            # Check if any GitHub keywords are present (would be suspicious)
            for kw in github_keywords:
                if kw in plan.intent.lower():
                    errors.append(
                        f"Plausibility check failed: intent mentions '{kw}' but tool is 'weather'"
                    )
                    break

        return errors