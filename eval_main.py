import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from evals.loader import load_cases
from evals.runner import run_cases
from evals.grader import grade_all, print_grades
from main import setup_aegis

def test_runner(brain, validator, executor,max_cases: int =None):
    cases = load_cases()

    if max_cases:
        cases = cases[:max_cases]

    outcomes = run_cases(cases, brain, validator, executor)
    grades = grade_all(outcomes)     # ← Grade each outcome
    print_grades(grades)

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

if __name__ == "__main__":
    brain, validator, executor = setup_aegis()
    test_runner(brain, validator, executor,max_cases=15)