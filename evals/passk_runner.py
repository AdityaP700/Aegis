"""Pass@k and Pass^k evaluation — measures consistency across multiple trials."""
import time
from typing import List, Dict, Any
from evals.loader import EvalCase, load_cases
from evals.runner import run_single_case
from evals.grader import grade_trial
from evals.runner import TrialOutcome
from evals.baseline_runner import run_baseline_query


class PassKResult:
    """Result of running k trials for one task."""

    def __init__(self, case: EvalCase):
        self.case = case
        self.trials = []  # List of TrialResult objects
        self.grades = []  # List of GradeResult objects

    @property
    def k(self) -> int:
        return len(self.trials)

    @property
    def pass_at_k(self) -> bool:
        """Did it succeed at least once?"""
        return any(g.passed for g in self.grades)

    @property
    def pass_carat_k(self) -> bool:
        """Did it succeed every time?"""
        return all(g.passed for g in self.grades)

    @property
    def success_count(self) -> int:
        return sum(1 for g in self.grades if g.passed)

    def __repr__(self):
        return (f"PassKResult(case='{self.case.id}', "
                f"pass@{self.k}={self.pass_at_k}, "
                f"pass^{self.k}={self.pass_carat_k}, "
                f"success={self.success_count}/{self.k})")


def run_passk(cases: List[EvalCase], brain, validator, executor, registry,
              k: int = 3, delay: float = 2.0, use_baseline: bool = False) -> List[PassKResult]:
    """
    Run k trials for each case.

    Args:
        cases: List of EvalCase objects
        brain, validator, executor: Aegis components
        registry: Tool registry
        k: Number of trials per case
        delay: Seconds between API calls
        use_baseline: If True, run baseline instead of Aegis

    Returns:
        List of PassKResult objects
    """
    results = []

    print(f"\n{'=' * 80}")
    print(f"RUNNING PASS@K EVALUATION (k={k})")
    print(f"Mode: {'BASELINE' if use_baseline else 'AEGIS'}")
    print(f"{'=' * 80}")

    for case_idx, case in enumerate(cases, 1):
        passk = PassKResult(case)

        print(f"\n[{case_idx}/{len(cases)}] {case.id}")

        for trial in range(1, k + 1):
            print(f"  Trial {trial}/{k}...")

            try:
                if use_baseline:
                    result = run_baseline_query(case.query, brain, registry)
                    grade = _grade_baseline_result(case, result)
                else:
                    from pipeline import process_query
                    result = process_query(case.query, brain, validator, executor)
                    outcome = TrialOutcome(case, result)
                    grade = grade_trial(outcome)

                passk.trials.append(result)
                passk.grades.append(grade)

                icon = "✅" if grade.passed else "❌"
                print(f"    {icon} Trial {trial}: {result.final_status}")

            except Exception as e:
                print(f"    💥 Trial {trial} crashed: {e}")
                from engine.types import TrialResult
                crash_result = TrialResult(
                    query=case.query,
                    final_status="crash",
                    failure_reason="crash"
                )
                crash_grade = _grade_crash(case)
                passk.trials.append(crash_result)
                passk.grades.append(crash_grade)

            if trial < k:
                time.sleep(delay)

        results.append(passk)

    return results


def _grade_baseline_result(case: EvalCase, result) -> Any:
    """Grade baseline result deterministically."""
    class BaselineGrade:
        def __init__(self):
            self.passed = False

    grade = BaselineGrade()

    if result.final_status != "success":
        grade.passed = False
        return grade

    expected_tool = case.expected.get("expected_tool", "")
    if expected_tool and result.tool != expected_tool:
        grade.passed = False
        return grade

    grade.passed = True
    return grade


def _grade_crash(case: EvalCase) -> Any:
    """Grade a crashed trial as failed."""
    class CrashGrade:
        def __init__(self):
            self.passed = False

    return CrashGrade()


def print_passk_results(results: List[PassKResult]):
    """Print Pass@k and Pass^k results."""
    print(f"\n{'=' * 80}")
    print(f"PASS@K vs PASS^K RESULTS")
    print(f"{'=' * 80}")
    print(f"{'Case':<20} {'K':<3} {'Success':<10} {'Pass@k':<8} {'Pass^k':<8}")
    print(f"{'─' * 80}")

    for r in results:
        print(f"{r.case.id:<20} {r.k:<3} {r.success_count}/{r.k:<7} "
              f"{'✅' if r.pass_at_k else '❌':<6} "
              f"{'✅' if r.pass_carat_k else '❌':<6}")

    # Summary
    total = len(results)
    pass_at = sum(1 for r in results if r.pass_at_k)
    pass_carat = sum(1 for r in results if r.pass_carat_k)

    print(f"\n{'─' * 80}")
    print(f"SUMMARY")
    print(f"{'─' * 80}")
    print(f"  Total tasks:          {total}")
    print(f"  Pass@{results[0].k if results else 'k'}:            {pass_at}/{total} ({pass_at/total*100:.0f}%)")
    print(f"  Pass^{results[0].k if results else 'k'}:            {pass_carat}/{total} ({pass_carat/total*100:.0f}%)")
    print(f"  Consistency gap:      {pass_at - pass_carat} tasks work sometimes but not always")


def compare_passk(aegis_results: List[PassKResult], baseline_results: List[PassKResult]):
    """Compare Pass@k and Pass^k between baseline and Aegis."""
    print(f"\n{'=' * 80}")
    print(f"PASS@K COMPARISON: BASELINE vs AEGIS")
    print(f"{'=' * 80}")
    print(f"{'Case':<20} {'Base@k':<8} {'Aegis@k':<8} {'Base^k':<8} {'Aegis^k':<8}")
    print(f"{'─' * 80}")

    for aegis_r, base_r in zip(aegis_results, baseline_results):
        print(f"{aegis_r.case.id:<20} "
              f"{'✅' if base_r.pass_at_k else '❌':<6} "
              f"{'✅' if aegis_r.pass_at_k else '❌':<6} "
              f"{'✅' if base_r.pass_carat_k else '❌':<6} "
              f"{'✅' if aegis_r.pass_carat_k else '❌':<6}")

    # Summary
    total = len(aegis_results)
    k = aegis_results[0].k if aegis_results else 0

    base_at = sum(1 for r in baseline_results if r.pass_at_k)
    aegis_at = sum(1 for r in aegis_results if r.pass_at_k)
    base_carat = sum(1 for r in baseline_results if r.pass_carat_k)
    aegis_carat = sum(1 for r in aegis_results if r.pass_carat_k)

    print(f"\n{'─' * 80}")
    print(f"SUMMARY (k={k})")
    print(f"{'─' * 80}")
    print(f"  Pass@{k}:  Baseline {base_at}/{total} ({base_at/total*100:.0f}%) | "
          f"Aegis {aegis_at}/{total} ({aegis_at/total*100:.0f}%)")
    print(f"  Pass^{k}:  Baseline {base_carat}/{total} ({base_carat/total*100:.0f}%) | "
          f"Aegis {aegis_carat}/{total} ({aegis_carat/total*100:.0f}%)")
    print(f"  Consistency improvement: +{aegis_carat - base_carat} tasks")