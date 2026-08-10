"""Aegis pipeline — shared between main and test runner."""
from engine.types import ExecutionRequest, ExecutionPlan


def process_query(query: str, brain, validator, executor):
    print(f"\n{'─' * 60}")
    print(f"👤 User: {query}")

    plan = brain.think(query)
    print(f"🧠 Brain: {plan.tool}.{plan.operation}({plan.arguments}) [confidence: {plan.confidence}]")

    plan = validator.validate(plan)

    if plan.validation_status == "failed":
        confidence_errors = [e for e in plan.validation_errors if "Confidence too low" in e]
        if confidence_errors:
            print(f"⚠️  Aegis abstained: confidence {plan.confidence:.1f} below threshold")
            return None

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
        return _execute_plan(plan, executor, validator)
    else:
        print(f"❌ Could not create valid plan.")
        print(f"   Errors: {plan.validation_errors}")
        return None


def _attempt_retry(query, plan, brain, validator):
    print(f"❌ Validation failed: {plan.validation_errors}")
    print("🔄 Retrying with error feedback...")
    previous_response = f'{{"tool": "{plan.tool}", "arguments": {plan.arguments}}}'
    error_msg = "; ".join(plan.validation_errors)
    plan = brain.retry(query, error_msg, previous_response)
    return validator.validate(plan)


def _execute_plan(plan, executor, validator):
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
    return response


def _display_result(tool_name, response):
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