"""Aegis pipeline — shared between main and test runner."""
from engine.types import ExecutionRequest, ExecutionPlan,TrialResult
from engine.otel import setup_tracing
import time

tracer = setup_tracing()

def process_query(query: str, brain, validator, executor) -> TrialResult:
    start_time = time.perf_counter()
    result = TrialResult(query=query)

    with tracer.start_as_current_span("agent.request") as parent:
        parent.set_attribute("query", query)

        # Brain span
        with tracer.start_as_current_span("agent.plan") as span:
            plan = brain.think(query)
            result.confidence = plan.confidence
            result.tool = plan.tool
            result.operation = plan.operation
            result.arguments = plan.arguments
            span.set_attribute("tool", plan.tool)
            span.set_attribute("operation", plan.operation)
            span.set_attribute("confidence", plan.confidence)
        print(f"Brain: {plan.tool}.{plan.operation}({plan.arguments}) [confidence: {plan.confidence}]")

        # Model guard — check immediately after Brain
        if plan.confidence < 0.2 and plan.tool == "search":
            result.trace.append({
                "component": "brain",
                "event": "model_did_not_understand",
                "confidence": plan.confidence
            })
            result.final_status = "model_failure"
            result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return result

        with tracer.start_as_current_span("validation") as span:
            plan = validator.validate(plan)
            span.set_attribute("status", plan.validation_status)

        if plan.validation_status == "failed":
            result.validation_failed = True
            result.trace.append({
                "component": "validator",
                "event": "validation_failed",
                "errors": plan.validation_errors,
                "error_type": "validation_error"
            })
            capability_errors = [e for e in plan.validation_errors
                                if "Operation mismatch" in e or "Capability mismatch" in e]
            if capability_errors:
                result.capability_rejected = True
                result.trace.append({
                    "component": "validator",
                    "event": "capability_rejected",
                    "errors": capability_errors,
                    "error_type": "capability_mismatch"
                })
            else:
                plan = _attempt_retry(query,plan,brain,validator)
                result.retry_attempted = True
                result.trace.append({
                "component":"pipeline",
                "event": "retry_attempted"
            })

        if plan.validation_status == "failed":
            confidence_errors = [e for e in plan.validation_errors if "Confidence too low" in e]
            if confidence_errors:
                result.trace.append({
                    "component": "validator",
                    "event": "abstained_low_confidence",
                    "confidence": plan.confidence,
                    "error_type": "low_confidence"
                })
                result.final_status = "abstained"
                result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return result

        if plan.validation_status == "failed" or plan.tool == "unknown":
            with tracer.start_as_current_span("recovery") as span:
                span.set_attribute("type", "fallback")
                span.set_attribute("from", plan.tool)
                span.set_attribute("to", "search")
            result.fallback_triggered = True
            result.trace.append({
                "component": "pipeline",
                "event": "fallback_to_search",
                "reason": "validation_failed" if plan.validation_status == "failed" else "unknown_tool"
            })
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
            result.tool = "search"
            result.operation = "web_search"
            result.arguments = {"query": query}

        if plan.validation_status == "passed":
            response = _execute_plan(plan, executor, validator)
            if response and response.status != "success":
                result.trace.append({
                    "component": "executor",
                    "event": "execution_failed",
                    "error_type": type(response.error).__name__ if response.error else "Unknown",
                    "error_message": response.error or "",
                    "tool": plan.tool
                })
                result.final_status = "needs_clarification"
            else:
                result.final_status = response.status if response else "failed"
                result.post_validation_passed = getattr(response, 'post_passed', None)
                result.trace.extend(getattr(response, 'trace', []))
        else:
            result.final_status = "failed"
            print(f"❌ Could not create valid plan.")
            print(f"   Errors: {plan.validation_errors}")

        result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return result#its just a method right ??
def _attempt_retry(query, plan, brain, validator):
    print(f" Validation failed: {plan.validation_errors}")
    print("Retrying with error feedback...")
    previous_response = f'{{"tool": "{plan.tool}", "arguments": {plan.arguments}}}'
    error_msg = "; ".join(plan.validation_errors)
    with tracer.start_as_current_span("agent.retry") as span:
        span.set_attribute("attempt", 1)
        plan = brain.retry(query, error_msg, previous_response)
    return validator.validate(plan)


def _execute_plan(plan, executor, validator):
    operation = plan.operation or "not specified"
    print(f"✅ Plan: {plan.tool}.{operation}({plan.arguments})")
    with tracer.start_as_current_span("tool.execute") as span:
        span.set_attribute("tool", plan.tool)
        request = ExecutionRequest(tool=plan.tool, arguments=plan.arguments)
        response = executor.execute(request)

        if response.status == "success":
            post = validator.post_validate(plan, response)
            response.post_passed = post.passed
            response.post_errors = post.all_errors
            if post.passed:
                print(f"   ✅ Post-check: integrity ✓ | plausibility ✓ | completeness ✓")
            else:
                span.set_attribute("errors",str(post.all_errors))
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