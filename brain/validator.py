from typing import List
from engine.types import ExecutionPlan,ExecutionRequest,PostExecutionResult
from tools.registry import ToolRegistry
"""
Validator
│
├── validate()                         ← Main entry point
│   ├── Check 1: Tool exists?
│   ├── Check 2: Required args present?
│   ├── Check 3: _validate_argument_types()
│   ├── Check 4: _validate_plausibility()
│   │   └── _check_argument_plausibility()
│   └── Check 5: Confidence threshold
"""

class Validator:
    """
    Validates ExecutionPlan against tool registry.
    Checks tool existence, required arguments, types, and plausibility.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def validate(self, plan: ExecutionPlan, user_query: str = "") -> ExecutionPlan:
        """
        Validate an ExecutionPlan.
        Modifies plan in-place and returns it.

        Args:
            plan: ExecutionPlan to validate

        Returns:
            Validated ExecutionPlan (with validation_status updated)
        """
        errors = []
        if plan.tool != "unknown" and plan.confidence < 0.3:
            errors.append(
            f"Confidence too low for execution: {plan.confidence:.1f}. "
            f"System requires confidence ≥ 0.5 to proceed."
        )

        # Check 1: Does tool exist?
        if plan.tool == "unknown":
            errors.append("No tool identified for this query")
        elif not self.registry.get(plan.tool):
            errors.append(f"Tool '{plan.tool}' is not registered")
        else:

    # Check 2: Required arguments present?
            tool = self.registry.get(plan.tool)
            if hasattr(tool, 'supported_operations') and plan.operation:
                if plan.operation not in tool.supported_operations:
                    errors.append(
                    f"Operation mismatch: '{plan.tool}' does not support "
                    f"'{plan.operation}'. Supported: {tool.supported_operations}"
                )

            if hasattr(tool, 'capabilities') and plan.requested_capability:
                if plan.requested_capability not in tool.capabilities:
                    errors.append(
                    f"Capability mismatch: requested '{plan.requested_capability}' "
                    f"but tool '{plan.tool}' only supports {tool.capabilities}"
                )

    # Use the tool we already have, don't fetch again
            if tool and hasattr(tool, 'required_args'):
                required_args = tool.required_args
            else:
                required_args = []

                for arg in required_args:
                    if arg not in plan.arguments or not plan.arguments[arg]:
                        errors.append(f"Missing required argument: '{arg}'")

    # Check 3 & 4 unchanged
                errors._extent(self._validate_argument_contract(plan))
                errors.extend(self._validate_argument_types(plan))
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

    def post_validate(self, plan: ExecutionPlan, response) -> PostExecutionResult:
        # 1. "Does the tool still exist?"
        tool = self.registry.get(plan.tool)
        if not tool:
             # Something went wrong — tool was there pre-execution but not now
            result = PostExecutionResult()
            result.integrity = False
            result.integrity_errors.append(f"Tool '{plan.tool}' not found for post-validation")
            return result
         # 2. "Can this tool validate its own results?"
        if hasattr(tool, 'validate_result'):
            # Yes → delegate to the tool. It knows its own domain.
            return tool.validate_result(plan, response.result or {})
        # 3. "Tool exists but doesn't have validation logic"
        # → Pass by default (don't block execution for missing validation)
        return PostExecutionResult()

    def _validate_argument_contract(self, plan: ExecutionPlan) -> List[str]:
        """
      Validate arguments against the tool's input contract.
      Catches structural issues before execution.
        """
        errors = []

        if plan.tool == "weather":
            city = plan.arguments.get("city", "")

        # Multi-city detection
            multi_city_markers = [" and ", " & ", ", "]
            for marker in multi_city_markers:
                if marker in city:
                    cities_found = city.split(marker)
                    errors.append(
                    f"Multi-city detected in 'city' argument: '{city}'. "
                    f"Found {len(cities_found)} cities: {cities_found}. "
                    f"Weather tool currently supports only one city per request."
                    )
                    break

        elif plan.tool == "github":
            repo = plan.arguments.get("repo", "")

        # Repo format: must be owner/repo with exactly one slash
            if repo:
                slash_count = repo.count("/")
                if slash_count == 0:
                    errors.append(
                    f"Invalid repo format: '{repo}'. "
                    f"Expected 'owner/repo' (e.g., 'karpathy/nanoGPT'). "
                    f"If only repo name is known, leave empty and let the system clarify."
                )
            elif slash_count > 1:
                errors.append(
                    f"Invalid repo format: '{repo}'. "
                    f"Too many slashes ({slash_count}). Expected exactly one: 'owner/repo'."
                )
            if " " in repo:
                errors.append(f"Repo contains spaces: '{repo}'. Repo names cannot have spaces.")

        elif plan.tool == "search":
            query = plan.arguments.get("query", "")

        # Query must be meaningful
            if query and len(query.strip()) < 3:
                errors.append(
                f"Search query too short: '{query}' ({len(query.strip())} chars). "
                f"Minimum 3 characters required."
                )

        return errors
