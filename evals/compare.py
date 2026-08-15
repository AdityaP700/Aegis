"""Compares Aegis vs Baseline agent on the same test cases."""
from typing import List, Any
from evals.loader import EvalCase, load_cases
from evals.runner import run_cases, TrialOutcome
from evals.grader import grade_all, grade_trial
from evals.baseline_runner import run_baseline_cases
from evals.metrics import build_report, EvalReport


class ComparisonResult:
    """Side-by-side comparison of one case."""

    def __init__(self, case: EvalCase):
        self.case = case
        self.aegis_result = None
        self.baseline_result = None
        self.aegis_grade = None
        self.baseline_grade = None

    @property
    def aegis_passed(self) -> bool:
        return self.aegis_grade.passed if self.aegis_grade else False

    @property
    def baseline_passed(self) -> bool:
        return self.baseline_grade.passed if self.baseline_grade else False

    @property
    def improvement(self) -> str:
        """How did Aegis change the outcome?"""
        if self.aegis_passed and not self.baseline_passed:
            return "✅ IMPROVED"
        elif self.baseline_passed and not self.aegis_passed:
            return "❌ REGRESSED"
        elif self.aegis_passed and self.baseline_passed:
            return "➖ SAME (both passed)"
        else:
            return "➖ SAME (both failed)"


def run_comparison(brain, validator, executor, registry,
                   max_cases: int = None,
                   delay: float = 2.0) -> List[ComparisonResult]:
    """
    Run both Aegis and Baseline on the same cases.

    Args:
        brain: Brain instance (shared)
        validator: Validator instance (Aegis only)
        executor: Executor instance (Aegis only)
        registry: ToolRegistry (shared)
        max_cases: Limit number of cases (for quick tests)
        delay: Seconds between API calls

    Returns:
        List of ComparisonResult objects
    """
    cases = load_cases()
    if max_cases:
        cases = cases[:max_cases]

    print(f"\n{'=' * 80}")
    print(f"RUNNING COMPARISON: BASELINE vs AEGIS")
    print(f"{'=' * 80}")
    print(f"Cases: {len(cases)}")

    # Run baseline first
    print(f"\n{'─' * 80}")
    print(f"PHASE 1: BASELINE AGENT (No safety net)")
    print(f"{'─' * 80}")
    baseline_results = run_baseline_cases(cases, brain, registry, delay)

    # Run Aegis
    print(f"\n{'─' * 80}")
    print(f"PHASE 2: AEGIS AGENT (With reliability layer)")
    print(f"{'─' * 80}")
    aegis_outcomes = run_cases(cases, brain, validator, executor, delay)

    # Build comparison
    comparisons = []
    for case in cases:
        comp = ComparisonResult(case)

        # Find baseline result
        for br in baseline_results:
            if br["case"].id == case.id:
                comp.baseline_result = br["result"]
                comp.baseline_grade = _grade_baseline(case, br["result"])
                break

        # Find Aegis result
        for ao in aegis_outcomes:
            if ao.case.id == case.id:
                comp.aegis_result = ao.result
                comp.aegis_grade = ao.result
                # Grade Aegis using existing grader
                comp.aegis_grade = grade_trial(ao)
                break

        comparisons.append(comp)

    return comparisons


def run_complete_analysis(brain, validator, executor, registry, max_cases: int = None, delay: float = 2.0) -> List[ComparisonResult]:
    """Backward-compatible alias for run_comparison.

    Calls the existing run_comparison to perform the full analysis and returns the list of ComparisonResult objects.
    """
    return run_comparison(brain, validator, executor, registry, max_cases=max_cases, delay=delay)


def _grade_baseline(case: EvalCase, result) -> Any:
    """
    Grade baseline on whether it ACTUALLY fulfilled the request.
    Not just "did it execute without crashing."
    """
    class BaselineGrade:
        def __init__(self):
            self.passed = False
            self.silent_failure = False

    grade = BaselineGrade()

    # Check if execution succeeded
    if result.final_status != "success":
        grade.passed = False
        return grade

    # Check if the RIGHT tool was used
    expected_tool = case.expected.get("expected_tool", "")
    if expected_tool and result.tool != expected_tool:
        grade.passed = False
        grade.silent_failure = True
        return grade

    # Check if the RIGHT operation was attempted
    expected_operation = case.expected.get("expected_operation", "")
    if expected_operation and result.operation != expected_operation:
        grade.passed = False
        grade.silent_failure = True
        return grade

    # If we got here, baseline actually did the right thing
    grade.passed = True
    return grade

def print_comparison_table(comparisons: List[ComparisonResult]):
    """Print side-by-side comparison table."""
    print(f"\n{'=' * 80}")
    print(f"COMPARISON: BASELINE vs AEGIS")
    print(f"{'=' * 80}")
    print(f"{'Case':<20} {'Category':<12} {'Baseline':<10} {'Aegis':<10} {'Result':<20}")
    print(f"{'─' * 80}")

    for comp in comparisons:
        baseline_status = comp.baseline_result.final_status if comp.baseline_result else "?"
        aegis_status = comp.aegis_result.final_status if comp.aegis_result else "?"

        baseline_icon = "✅" if comp.baseline_passed else "❌"
        aegis_icon = "✅" if comp.aegis_passed else "❌"

        print(f"{comp.case.id:<20} {comp.case.category:<12} "
              f"{baseline_icon} {baseline_status:<8} "
              f"{aegis_icon} {aegis_status:<8} "
              f"{comp.improvement}")

    # Summary
    total = len(comparisons)
    improved = sum(1 for c in comparisons if "IMPROVED" in c.improvement)
    regressed = sum(1 for c in comparisons if "REGRESSED" in c.improvement)
    same = sum(1 for c in comparisons if "SAME" in c.improvement)

    aegis_pass = sum(1 for c in comparisons if c.aegis_passed)
    baseline_pass = sum(1 for c in comparisons if c.baseline_passed)

    print(f"\n{'─' * 80}")
    print(f"SUMMARY")
    print(f"{'─' * 80}")
    print(f"  Baseline pass rate: {baseline_pass}/{total} ({baseline_pass/total*100:.0f}%)")
    print(f"  Aegis pass rate:    {aegis_pass}/{total} ({aegis_pass/total*100:.0f}%)")
    print(f"  Cases improved:     {improved}")
    print(f"  Cases regressed:    {regressed}")
    print(f"  Cases unchanged:    {same}")
    print(f"  Reliability gain:   +{aegis_pass - baseline_pass} cases")


def save_comparison(comparisons: List[ComparisonResult], filepath: str = None):
    """Save comparison to JSON."""
    import json
    from pathlib import Path

    if filepath is None:
        data_dir = Path("Data")
        data_dir.mkdir(exist_ok=True)
        filepath = data_dir / "comparison_report.json"

    data = []
    for comp in comparisons:
        data.append({
            "case_id": comp.case.id,
            "category": comp.case.category,
            "baseline_status": comp.baseline_result.final_status if comp.baseline_result else "?",
            "aegis_status": comp.aegis_result.final_status if comp.aegis_result else "?",
            "baseline_passed": comp.baseline_passed,
            "aegis_passed": comp.aegis_passed,
            "improvement": comp.improvement
        })

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n📁 Comparison saved to: {filepath}")