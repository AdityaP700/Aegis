from brain.gemini_brain import GeminiBrain
from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from engine.types import ExecutionRequest, ExecutionPlan
from executor import Executor

def get_tools_metadata(registry: ToolRegistry) -> list:
    """Extract tool metadata for the Brain."""
    metadata = []
    for tool_name, tool in registry._tools.items():
        metadata.append({
            "name": tool.name,
            "description": tool.description,
            "required_args": ["city"] if tool_name == "weather" else
                           ["repo"] if tool_name == "github" else
                           ["query"] if tool_name == "search" else []
        })
    return metadata

def main():
    print("=" * 60)
    print("AEGIS — Intent Planner (Sprint 3)")
    print("=" * 60)

    # Setup Registry
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(GitHubTool())
    registry.register(SearchTool())
    print(f"\n✓ Tools registered: {registry.list_tools()}")

    # Setup Brain
    tools_metadata = get_tools_metadata(registry)
    brain = GeminiBrain(tools_metadata)
    print(f"✓ Brain initialized: {brain.provider_name}")

    # Setup Validator
    validator = Validator(registry)
    print("✓ Validator initialized")

    # Setup Executor
    executor = Executor(registry)
    print("✓ Executor ready")

    # Test queries
    queries = [
        "What's the weather in Delhi?",
        "How many stars does karpathy/nanoGPT have?",
        "What is a transformer neural network?",
        "Tell me about weather in 12345",  # Should fail plausibility
        "asdfghjkl",                       # Should fail confidence
    ]

    for query in queries:
        print(f"\n{'─' * 60}")
        print(f"👤 User: {query}")

        # Step 1: Brain creates ExecutionPlan
        plan = brain.think(query)
        print(f"🧠 Plan: {plan.tool}({plan.arguments}) [confidence: {plan.confidence}]")

        # Step 2: Validate the plan
        plan = validator.validate(plan)

        if plan.validation_status == "failed":
            print(f"❌ Validation failed: {plan.validation_errors}")

            # Brain Retry (one attempt)
            print("🔄 Brain retry with error feedback...")
            previous_response = f'{{"tool": "{plan.tool}", "arguments": {plan.arguments}}}'
            error_msg = "; ".join(plan.validation_errors)

            plan = brain.retry(query, error_msg, previous_response)
            plan = validator.validate(plan)

            if plan.validation_status == "failed":
                print(f"❌ Retry also failed. Falling back to search.")
                plan = ExecutionPlan(
                    intent="fallback search",
                    tool="search",
                    arguments={"query": query},
                    confidence=0.3,
                    validation_status="passed"
                )

        # Step 3: Convert to ExecutionRequest
        if plan.validation_status == "passed":
            print(f"✅ Plan validated: {plan.tool}({plan.arguments})")

            request = ExecutionRequest(
                tool=plan.tool,
                arguments=plan.arguments
            )

            # Step 4: Execute
            response = executor.execute(request)

            if response.status == "success":
                if plan.tool == "weather":
                    r = response.result
                    print(f"   🌤️  {r['city']}: {r['temperature']}°C, {r['condition']}")
                elif plan.tool == "github":
                    r = response.result
                    print(f"   📦 {r['full_name']}: ⭐{r['stars']:,}")
                elif plan.tool == "search":
                    results = response.result.get("results", [])
                    print(f"   🔍 Found {len(results)} results")
            else:
                print(f"   ❌ Execution failed: {response.error}")

if __name__ == "__main__":
    main()