"""Quick stress test: Baseline vs Aegis on 5 queries."""
from main import setup_aegis
from evals.loader import load_cases_from_file
from evals.baseline_runner import run_baseline_cases
from evals.runner import run_cases
from evals.grader import grade_all, grade_trial
from evals.metrics import build_report, print_report


STRESS_CASES = [
    {
        "id": "stress_capability",
        "category": "STRESS",
        "query": "What was the weather in Paris last Monday?",
        "expected": {
            "expected_tool": "search",
            "expected_operation": "web_search",
            "capability_rejected": True,
            "fallback_triggered": True,
            "final_status": "success",
            "failure_reason": "none"
        }
    },
    {
        "id": "stress_forecast",
        "category": "STRESS",
        "query": "Will it rain in Tokyo tomorrow?",
        "expected": {
            "expected_tool": "search",
            "expected_operation": "web_search",
            "capability_rejected": True,
            "fallback_triggered": True,
            "final_status": "success",
            "failure_reason": "none"
        }
    },
    {
        "id": "stress_invalid_city",
        "category": "STRESS",
        "query": "Weather in XYZ123",
        "expected": {
            "expected_tool": "weather",
            "capability_rejected": False,
            "fallback_triggered": False,
            "final_status": "needs_clarification",
            "failure_reason": "invalid_value"
        }
    },
    {
        "id": "stress_readme",
        "category": "STRESS",
        "query": "Show me the README of karpathy/nanoGPT",
        "expected": {
            "expected_tool": "search",
            "expected_operation": "web_search",
            "capability_rejected": True,
            "fallback_triggered": True,
            "final_status": "success",
            "failure_reason": "none"
        }
    },
    {
        "id": "stress_python",
        "category": "STRESS",
        "query": "Tell me about Python",
        "expected": {
            "expected_tool": "search",
            "fallback_triggered": False,
            "final_status": "success",
            "failure_reason": "none"
        }
    }
]


def run_stress_test():
    brain, validator, executor = setup_aegis()
    registry = executor.registry

    print("\n" + "=" * 80)
    print("STRESS TEST: BASELINE vs AEGIS")
    print("=" * 80)

    # Run Baseline
    print("\n" + "─" * 80)
    print("PHASE 1: BASELINE (No safety net)")
    print("─" * 80)
    baseline_results = []
    for case_data in STRESS_CASES:
        from evals.loader import EvalCase
        case = EvalCase(case_data)
        from evals.baseline_runner import run_baseline_query
        result = run_baseline_query(case.query, brain, registry)
        baseline_results.append({"case": case, "result": result})
        icon = "✅" if result.final_status == "success" else "❌"
        print(f"  {icon} {case.id}: {result.final_status}")

    # Run Aegis
    print("\n" + "─" * 80)
    print("PHASE 2: AEGIS (With reliability layer)")
    print("─" * 80)
    aegis_outcomes = []
    for case_data in STRESS_CASES:
        from evals.loader import EvalCase
        case = EvalCase(case_data)
        from pipeline import process_query
        result = process_query(case.query, brain, validator, executor)
        aegis_outcomes.append({"case": case, "result": result})
        icon = "✅" if result.final_status == "success" else "❌"
        print(f"  {icon} {case.id}: {result.final_status}")

    # Comparison
    print("\n" + "─" * 80)
    print("COMPARISON")
    print("─" * 80)
    print(f"{'Case':<25} {'Baseline':<15} {'Aegis':<15}")
    print("─" * 55)

    for base, aegis in zip(baseline_results, aegis_outcomes):
        base_status = base["result"].final_status
        aegis_status = aegis["result"].final_status
        base_icon = "✅" if base_status == "success" else "❌"
        aegis_icon = "✅" if aegis_status == "success" else "❌"
        print(f"{base['case'].id:<25} {base_icon} {base_status:<10} {aegis_icon} {aegis_status}")

    # Summary
    base_success = sum(1 for r in baseline_results if r["result"].final_status == "success")
    aegis_success = sum(1 for r in aegis_outcomes if r["result"].final_status == "success")

    print("\n" + "─" * 55)
    print(f"  Baseline success: {base_success}/5 ({base_success/5*100:.0f}%)")
    print(f"  Aegis success:    {aegis_success}/5 ({aegis_success/5*100:.0f}%)")
    print(f"  Improvement:      +{aegis_success - base_success} cases")


if __name__ == "__main__":
    run_stress_test()