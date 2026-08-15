"""Aggregates evaluation results into summary metrics."""
from typing import List, Dict
from collections import Counter


class EvalReport:
    """Complete evaluation report."""

    def __init__(self):
        self.total_cases = 0
        self.passed = 0
        self.failed = 0
        self.crashed = 0
        self.by_category: Dict[str, Dict[str, int]] = {}
        self.failure_reasons: Counter = Counter()
        self.latencies: List[float] = []

    def add_result(self, grade, outcome):
        """Add one trial result to the report."""
        self.total_cases += 1

        # Track pass/fail
        if grade.passed:
            self.passed += 1
        else:
            self.failed += 1

        # Track crashes
        if outcome.result.final_status == "crash":
            self.crashed += 1

        # Track by category
        category = outcome.case.category
        if category not in self.by_category:
            self.by_category[category] = {"passed": 0, "total": 0}
        self.by_category[category]["total"] += 1
        if grade.passed:
            self.by_category[category]["passed"] += 1

        # Track failure reasons
        # From the classifier
        failure_reason = outcome.result.failure_reason or "unknown"
        if not grade.passed:
            self.failure_reasons[failure_reason] += 1

        # Track latency
        if outcome.result.duration_ms > 0:
            self.latencies.append(outcome.result.duration_ms)

    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed / self.total_cases * 100

    @property
    def crash_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.crashed / self.total_cases * 100

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def p50_latency(self) -> float:
        if not self.latencies:
            return 0.0
            #sort the latencies
        sorted_latencies = sorted(self.latencies)
        index = len(sorted_latencies) // 2
        return sorted_latencies[index]


def build_report(grades, outcomes) -> EvalReport:
    """
    Build an EvalReport from grades and outcomes.

    Args:
        grades: List of GradeResult objects
        outcomes: List of TrialOutcome objects

    Returns:
        EvalReport with all metrics
    """
    report = EvalReport()

    for grade, outcome in zip(grades, outcomes):
        report.add_result(grade, outcome)

    return report


def print_report(report: EvalReport):
    """Pretty-print the evaluation report."""
    print(f"\n{'=' * 80}")
    print(f"AEGIS EVALUATION REPORT")
    print(f"{'=' * 80}")
    # Overall
    print(f"\nOVERALL")
    print(f"{'─' * 80}")
    print(f"  Total cases:      {report.total_cases}")
    print(f"  Passed:           {report.passed}")
    print(f"  Failed:           {report.failed}")
    print(f"  Crashed:          {report.crashed}")
    print(f"  Pass rate:        {report.pass_rate:.1f}%")
    print(f"  Crash rate:       {report.crash_rate:.1f}%")

    # Latency
    print(f"\nLATENCY")
    print(f"{'─' * 80}")
    print(f"  Average:          {report.avg_latency:.0f}ms")
    print(f"  P50:              {report.p50_latency:.0f}ms")
    print(f"  P95:              {report.p95_latency:.0f}ms")

    # By category
    print(f"\nBY CATEGORY")
    print(f"{'─' * 80}")
    for category, stats in sorted(report.by_category.items()):
        passed = stats["passed"]
        total = stats["total"]
        pct = passed / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"  {category:<15} {bar} {passed}/{total} ({pct:.0f}%)")

    # Failure reasons
    if report.failure_reasons:
        print(f"\nFAILURE BREAKDOWN")
        print(f"{'─' * 80}")
        for reason, count in report.failure_reasons.most_common():
            print(f"  {reason:<30} {count}")

    print(f"\n{'=' * 80}")


def save_report(report: EvalReport, filepath: str = None):
    """Save report to JSON file."""
    import json
    from pathlib import Path

    if filepath is None:
        data_dir = Path("Data")
        data_dir.mkdir(exist_ok=True)
        filepath = data_dir / "eval_report.json"
    else:
        filepath = Path(filepath)

    data = {
        "total_cases": report.total_cases,
        "passed": report.passed,
        "failed": report.failed,
        "crashed": report.crashed,
        "pass_rate": report.pass_rate,
        "crash_rate": report.crash_rate,
        "avg_latency_ms": report.avg_latency,
        "p50_latency_ms": report.p50_latency,
        "p95_latency_ms": report.p95_latency,
        "by_category": report.by_category,
        "failure_reasons": dict(report.failure_reasons)
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n📁 Report saved to: {filepath}")