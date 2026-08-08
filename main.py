from brain.gemini_brain import GeminiBrain
from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from engine.types import ExecutionRequest, ExecutionPlan
from executor import Executor
from brain.groq_brain import GroqBrain
def setup_aegis():
    """Initialize all Aegis components. Called once at startup."""

    # Registry
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(GitHubTool())
    registry.register(SearchTool())

    # Brain
    tools_metadata = _extract_tools_metadata(registry)
    brain = GroqBrain(tools_metadata)

    # Validator
    validator = Validator(registry)

    # Executor
    executor = Executor(registry)

    return brain, validator, executor


def _extract_tools_metadata(registry: ToolRegistry) -> list:
    """Tell the Brain what tools exist and what they need."""
    required_args_map = {
        "weather": ["city"],
        "github": ["repo"],
        "search": ["query"],
    }

    metadata = []
    for tool_name, tool in registry._tools.items():
        metadata.append({
            "name": tool.name,
            "description": tool.description,
            "required_args": required_args_map.get(tool_name, [])
        })
    return metadata


def process_query(query: str, brain, validator, executor):
    """
    Full Aegis pipeline for a single user query.

    User → Brain → Plan → Validate → Retry? → Execute → Response
    """
    print(f"\n{'─' * 60}")
    print(f" User: {query}")

    # Step 1: Think
    plan = brain.think(query)
    print(f" Brain: {plan.tool}({plan.arguments}) [confidence: {plan.confidence}]")
    # returns the plan
    # Step 2: Validate
    plan = validator.validate(plan)

    # Step 3: Retry if needed (one attempt)
    if plan.validation_status == "failed":
        plan = _attempt_retry(query, plan, brain, validator)

    # Step 4: Execute or fail
    if plan.validation_status == "passed":
        _execute_plan(plan, executor)
    else:
        print(f"❌ Could not create valid plan after retry.")
        print(f"   Errors: {plan.validation_errors}")


def _attempt_retry(query: str, plan: ExecutionPlan, brain, validator) -> ExecutionPlan:
    """Try one Brain retry with error feedback."""
    print(f"❌ Validation failed: {plan.validation_errors}")
    print("🔄 Retrying with error feedback...")

    previous_response = f'{{"tool": "{plan.tool}", "arguments": {plan.arguments}}}'
    error_msg = "; ".join(plan.validation_errors)

    plan = brain.retry(query, error_msg, previous_response)
    plan = validator.validate(plan)

    return plan


def _execute_plan(plan: ExecutionPlan, executor):
    """Convert plan to request and execute."""
    print(f"✅ Plan: {plan.tool}({plan.arguments})")

    request = ExecutionRequest(
        tool=plan.tool,
        arguments=plan.arguments
    )

    response = executor.execute(request)
    _display_result(plan.tool, response)


def _display_result(tool_name: str, response):
    """Pretty-print the result based on tool type."""
    if response.status != "success":
        print(f"   ❌ Execution failed: {response.error}")
        return

    result = response.result

    if tool_name == "weather":
        print(f"   🌤️  {result['city']}: {result['temperature']}°C, {result['condition']}")
        print(f"   💧 Humidity: {result['humidity']}%")

    elif tool_name == "github":
        print(f"   📦 {result['full_name']}")
        print(f"   ⭐ Stars: {result['stars']:,}")
        print(f"   🔧 Language: {result['language']}")
        print(f"   📜 License: {result['license']}")

    elif tool_name == "search":
        results = result.get("results", [])
        print(f"   🔍 Found {len(results)} results:")
        for i, r in enumerate(results[:3], 1):
            print(f"      {i}. {r['title'][:80]}")
            print(f"         {r['snippet'][:100]}...")

    print(f"   ⏱️  {response.metadata.get('duration_ms')}ms")


def main():
    print("=" * 60)
    print("AEGIS — Intent Planner")
    print("=" * 60)

    # Setup once
    brain, validator, executor = setup_aegis()
    print(f"✓ Brain: {brain.provider_name}")
    print(f"✓ Tools: {executor.registry.list_tools()}")
    print("✓ Ready\n")

    # Test ONE query at a time
    query = input("👤 You: ").strip()

    if not query:
        query = "What's the weather in Delhi?"
        print(f"   (using default: '{query}')")

    process_query(query, brain, validator, executor)


if __name__ == "__main__":
    main()