"""Runs the 10-task mini-benchmark with Pass@k."""
import time
from typing import List
from evals.loader import load_cases_from_file
from evals.passk_runner import run_passk, print_passk_results, compare_passk
from evals.metrics import build_report, print_report


def run_benchmark(brain, validator, executor, k: int = 3):
    """
    Run the 10-task benchmark comparing Baseline vs Aegis.

    Args:
        k: Trials per task (3 recommended)
    """
    cases = load_cases_from_file("eval/benchmark_cases.json")

    print(f"\n{'=' * 80}")
    print(f"AEGIS MINI-BENCHMARK")
    print(f"10 tasks × {k} trials = {len(cases) * k} executions per agent")
    print(f"{'=' * 80}")

    # Phase 1: Aegis
    print(f"\n{'─' * 80}")
    print(f"PHASE 1: AEGIS AGENT")
    print(f"{'─' * 80}")
    aegis_results = run_passk(
        cases, brain, validator, executor, executor.registry,
        k=k, delay=2.0, use_baseline=False
    )

    # Phase 2: Baseline
    print(f"\n{'─' * 80}")
    print(f"PHASE 2: BASELINE AGENT")
    print(f"{'─' * 80}")
    baseline_results = run_passk(
        cases, brain, validator, executor, executor.registry,
        k=k, delay=2.0, use_baseline=True
    )

    # Phase 3: Comparison
    compare_passk(aegis_results, baseline_results)

    # Phase 4: Detailed breakdown
    _print_benchmark_summary(aegis_results, baseline_results, k)

    return aegis_results, baseline_results


def _print_benchmark_summary(aegis_results, baseline_results, k):
    """Print detailed breakdown by category."""
    print(f"\n{'=' * 80}")
    print(f"BENCHMARK BREAKDOWN (k={k})")
    print(f"{'=' * 80}")

    categories = {}
    for case in aegis_results:
        cat = case.case.category
        if cat not in categories:
            categories[cat] = {"aegis_success": 0, "baseline_success": 0, "trials": 0}
        categories[cat]["trials"] += k
        categories[cat]["aegis_success"] += case.success_count

    for br in baseline_results:
        cat = br.case.category
        if cat in categories:
            categories[cat]["baseline_success"] += br.success_count

    print(f"\n{'Category':<15} {'Baseline':<15} {'Aegis':<15} {'Improvement':<15}")
    print(f"{'─' * 60}")

    for cat, stats in sorted(categories.items()):
        base_rate = (stats["baseline_success"] / stats["trials"] * 100) if stats["trials"] > 0 else 0
        aegis_rate = (stats["aegis_success"] / stats["trials"] * 100) if stats["trials"] > 0 else 0
        improvement = aegis_rate - base_rate
        print(f"{cat:<15} {base_rate:>10.0f}% {aegis_rate:>10.0f}% {improvement:>+10.0f}%")