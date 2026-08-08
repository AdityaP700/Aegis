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

        tool = self.registry.get(tool_name)  # Use the parameter, not plan.tool
        if tool and hasattr(tool, 'required_args'):
            return tool.required_args  #  It's already a list
        return []

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

        errors = []

    # Signal words for each tool domain
        signals = {
        "weather": ["weather", "temperature", "rain", "sunny", "cold", "hot",
                     "celsius", "forecast", "humid", "climate"],
        "github": ["github", "repo", "stars", "repository", "fork", "pull request",
                    "code", "open source", "license"],
        "search": ["what is", "who is", "how to", "define", "explain", "why",
                   "difference between", "tutorial"]
    }

        intent_lower = plan.intent.lower()
        chosen_tool = plan.tool

    # For each tool domain, check if intent has signals for a DIFFERENT tool
        for domain, keywords in signals.items():
            if domain == chosen_tool:
                continue  # Skip the chosen tool's own signals

            for kw in keywords:
                if kw in intent_lower:
                    errors.append(
                    f"Plausibility: intent mentions '{kw}' ({domain} signal) "
                    f"but tool is '{chosen_tool}'"
                )
                    break  # One mismatch per domain is enough

    # Additional heuristic
        errors.extend(self._check_argument_plausibility(plan))
        return errors

    def _check_argument_plausibility(self, plan: ExecutionPlan) -> List[str]:
        errors = []

        if plan.tool == "weather":
            city = plan.arguments.get("city", "")
        # City names are rarely purely numeric
            if city and city.strip().isdigit():
                errors.append(f"Plausibility: city '{city}' looks like a number, not a city")
        # City names rarely contain special characters
            if city and any(c in city for c in ["/", "\\", "<", ">"]):
                errors.append(f"Plausibility: city '{city}' contains unusual characters")

        elif plan.tool == "github":
            repo = plan.arguments.get("repo", "")
        # Repo must have owner/repo format
            if repo and "/" not in repo:
                errors.append(f"Plausibility: repo '{repo}' missing owner/ format")
        # Repo names don't have spaces
            if repo and " " in repo:
                errors.append(f"Plausibility: repo '{repo}' contains spaces")

        elif plan.tool == "search":
            query = plan.arguments.get("query", "")
        # Search queries should be meaningful
            if query and len(query) < 3:
                errors.append(f"Plausibility: search query too short: '{query}'")

        return errors




