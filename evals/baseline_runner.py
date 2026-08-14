"""Runs the naive baseline agent (Brain → Tool, no safety net)."""
import time
from typing import List, Dict, Any
from engine.types import ExecutionRequest, TrialResult
from evals.loader import EvalCase


def run_baseline_query(query: str, brain, registry) -> TrialResult:
    """
    Run a query through the NAIVE agent — no validation, no retry, no fallback.

    This is what most LLM tool-calling demos do.
    """
    start_time = time.perf_counter()

    result = TrialResult(query=query)

    try:
        # Step 1: Brain picks tool
        plan = brain.think(query)
        result.tool = plan.tool
        result.operation = plan.operation
        result.arguments = plan.arguments
        result.confidence = plan.confidence

        # Step 2: Get tool from registry
        tool = registry.get(plan.tool)

        if not tool:
            result.final_status = "failed"
            result.failure_reason = "tool_not_found"
            result.trace.append({
                "component": "baseline",
                "event": "tool_not_found",
                "tool": plan.tool
            })
            result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return result

        # Step 3: Execute directly — no pre-validation, no capability check
        request = ExecutionRequest(tool=plan.tool, arguments=plan.arguments)
        raw_result = tool.execute(request, [])

        # Step 4: Trust whatever came back — no post-validation
        result.final_status = "success"
        result.trace.append({
            "component": "baseline",
            "event": "executed_without_validation",
            "tool": plan.tool
        })

    except Exception as e:
        result.final_status = "failed"
        result.failure_reason = "execution_error"
        result.trace.append({
            "component": "baseline",
            "event": "execution_failed",
            "error_message": str(e)
        })

    result.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    return result


def run_baseline_cases(cases: List[EvalCase], brain, registry,
                       delay_between_calls: float = 2.0) -> List[Dict[str, Any]]:
    """
    Run all cases through baseline agent.

    Returns:
        List of dicts with case_id and TrialResult
    """
    results = []

    print(f"\n{'=' * 80}")
    print(f"RUNNING {len(cases)} BASELINE CASES")
    print(f"{'=' * 80}")

    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case.id}")

        result = run_baseline_query(case.query, brain, registry)

        results.append({
            "case": case,
            "result": result
        })

        if i < len(cases):
            time.sleep(delay_between_calls)

    return results