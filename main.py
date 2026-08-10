import time
import json
from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from engine.types import ExecutionRequest, ExecutionPlan
from executor import Executor
from brain.groq_brain import GroqBrain
from test.test_runner import run_full_test_suite


def setup_aegis():
    """Initialize all Aegis components."""
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(GitHubTool())
    registry.register(SearchTool())

    tools_metadata = _extract_tools_metadata(registry)
    brain = GroqBrain(tools_metadata)
    validator = Validator(registry)
    executor = Executor(registry)

    return brain, validator, executor


def _extract_tools_metadata(registry: ToolRegistry) -> list:
    metadata = []
    for tool_name, tool in registry._tools.items():
        metadata.append({
            "name": tool.name,
            "description": tool.description,
            "supported_operations": getattr(tool, 'supported_operations', []),
            "capabilities": getattr(tool, 'capabilities', []),
            "required_args": getattr(tool, 'required_args', [])
        })
    return metadata


def process_query(query: str, brain, validator, executor):
    """Full Aegis pipeline for a single user query."""
    print(f"\n{'─' * 60}")
    print(f"👤 User: {query}")

    plan = brain.think(query)
    print(f"🧠 Brain: {plan.tool}.{plan.operation}({plan.arguments}) [confidence: {plan.confidence}]")

    plan = validator.validate(plan)

    if plan.validation_status == "failed":
        plan = _attempt_retry(query, plan, brain, validator)

    if plan.validation_status == "failed" or plan.tool == "unknown":
        print("🔄 Falling back to search...")
        plan = ExecutionPlan(
            intent="fallback search",
            tool="search",
            operation="web_search",
            arguments={"query": query},
            requested_capability="web_search",
            confidence=0.3,
            validation_status="passed"
        )

    if plan.validation_status == "passed":
        _execute_plan(plan, executor, validator)
    else:
        print(f"❌ Could not create valid plan.")
        print(f"   Errors: {plan.validation_errors}")


def _attempt_retry(query: str, plan: ExecutionPlan, brain, validator) -> ExecutionPlan:
    print(f"❌ Validation failed: {plan.validation_errors}")
    print("🔄 Retrying with error feedback...")
    previous_response = f'{{"tool": "{plan.tool}", "arguments": {plan.arguments}}}'
    error_msg = "; ".join(plan.validation_errors)
    plan = brain.retry(query, error_msg, previous_response)
    plan = validator.validate(plan)
    return plan


def _execute_plan(plan: ExecutionPlan, executor, validator):
    operation = plan.operation or "not specified"
    print(f"✅ Plan: {plan.tool}.{operation}({plan.arguments})")

    request = ExecutionRequest(tool=plan.tool, arguments=plan.arguments)
    response = executor.execute(request)

    if response.status == "success":
        post = validator.post_validate(plan, response)
        if post.passed:
            print(f"   ✅ Post-check: integrity ✓ | plausibility ✓ | completeness ✓")
        else:
            print(f"   ⚠️  Post-check FAILED:")
            for err in post.all_errors:
                print(f"      - {err}")

    _display_result(plan.tool, response)


def _display_result(tool_name: str, response):
    if response.status != "success":
        print(f"   ❌ Execution failed: {response.error}")
        return

    result = response.result

    if tool_name == "weather":
        print(f"   🌤️  {result.get('city', '?')}: {result.get('temperature', '?')}°C, {result.get('condition', '?')}")
        print(f"   💧 Humidity: {result.get('humidity', '?')}%")
    elif tool_name == "github":
        print(f"   📦 {result.get('full_name', '?')}")
        print(f"   ⭐ Stars: {result.get('stars', '?'):,}")
        print(f"   🔧 Language: {result.get('language', '?')}")
    elif tool_name == "search":
        results = result.get("results", [])
        print(f"   🔍 Found {len(results)} results:")
        for i, r in enumerate(results[:3], 1):
            print(f"      {i}. {r.get('title', '?')[:80]}")

    print(f"   ⏱️  {response.metadata.get('duration_ms', 0)}ms")


def main():
    print("=" * 60)
    print("AEGIS — Reliability Runtime")
    print("=" * 60)

    brain, validator, executor = setup_aegis()
    print(f"✓ Brain: {brain.provider_name}")
    print(f"✓ Tools: {executor.registry.list_tools()}")

    # Run full test suite with post-validation
    results = run_full_test_suite(brain, validator, executor)


if __name__ == "__main__":
    main()