from evals.loader import load_cases
from evals.runner import run_cases

def test_runner(brain, validator, executor):
    cases = load_cases()

    # Run all cases
    outcomes = run_cases(cases, brain, validator, executor)

    # Print summary
    print(f"\n{'=' * 80}")
    print(f"COMPLETED {len(outcomes)} CASES")
    print(f"{'=' * 80}")

    for outcome in outcomes:
        result = outcome.result
        print(f"\nCase: {outcome.case.id}")
        print(f"  Status: {result.final_status}")
        print(f"  Tool: {result.tool}.{result.operation}")
        print(f"  Fallback: {result.fallback_triggered}")
        print(f"  Capability Rejected: {result.capability_rejected}")
        print(f"  Post-Validation Passed: {result.post_validation_passed}")
        print(f"  Duration: {result.duration_ms}ms")

    return outcomes