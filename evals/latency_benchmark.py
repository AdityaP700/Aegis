"""Latency benchmark: Baseline vs Aegis across 3 query categories."""
import time
import json
from pathlib import Path
from typing import List, Dict, Any
from engine.types import ExecutionRequest
from pipeline import process_query
from evals.baseline_runner import run_baseline_query


LATENCY_QUERIES = {
    "happy_path": [
        "What's the weather in Delhi?",
        "What's the weather in London?",
        "What's the weather in Tokyo?",
    ],
    "capability_mismatch": [
        "What was the weather in Paris last Monday?",
        "Will it rain in Tokyo tomorrow?",
        "Show me the README of karpathy/nanoGPT",
    ],
    "invalid_input": [
        "Weather in XYZ123",
        "Weather in ABC999",
        "GitHub stars for this/repo/that",
    ]
}

def run_latency_benchmark(brain, validator, executor, registry,
                          runs_per_category: int = 3,
                          delay: float = 2.0) -> Dict[str, Any]:
    """
    Run latency benchmark comparing Baseline vs Aegis.

    Args:
        runs_per_category: Number of runs per category (3-5 for exploratory)
        delay: Seconds between API calls

    Returns:
        Dict with per-category latency stats
    """
    results = {
        "baseline": {},
        "aegis": {},
        "summary": {}
    }

    print(f"\n{'=' * 80}")
    print(f"LATENCY BENCHMARK")
    print(f"Runs per category: {runs_per_category}")
    print(f"{'=' * 80}")

    for category, queries in LATENCY_QUERIES.items():
        print(f"\n{'─' * 80}")
        print(f"CATEGORY: {category}")
        print(f"{'─' * 80}")

        base_latencies = []
        aegis_latencies = []
        aegis_breakdown = {
            "plan": [],
            "validation": [],
            "tool": [],
            "recovery": [],
            "total": []
        }

        for i, query in enumerate(queries[:runs_per_category], 1):
            print(f"\n  [{i}/{runs_per_category}] Query: {query}")

            # Baseline
            print(f"    Baseline...")
            start = time.perf_counter()
            baseline_result = run_baseline_query(query, brain, registry)
            base_duration = (time.perf_counter() - start) * 1000
            base_latencies.append(base_duration)
            print(f"    ✅ {base_duration:.0f}ms (status: {baseline_result.final_status})")

            time.sleep(delay)

            # Aegis
            print(f"    Aegis...")
            start = time.perf_counter()
            aegis_result = process_query(query, brain, validator, executor)
            aegis_duration = (time.perf_counter() - start) * 1000
            aegis_latencies.append(aegis_duration)
            aegis_breakdown["total"].append(aegis_duration)
            print(f"    ✅ {aegis_duration:.0f}ms (status: {aegis_result.final_status})")

            # Extract stage timings from trace
            plan_ms = _extract_stage_timing(aegis_result, "agent.plan")
            validation_ms = _extract_stage_timing(aegis_result, "validation")
            tool_ms = _extract_stage_timing(aegis_result, "tool.execute")
            recovery_ms = _extract_stage_timing(aegis_result, "recovery")

            aegis_breakdown["plan"].append(plan_ms)
            aegis_breakdown["validation"].append(validation_ms)
            aegis_breakdown["tool"].append(tool_ms)
            aegis_breakdown["recovery"].append(recovery_ms)

            print(f"    Breakdown: plan={plan_ms:.0f}ms, validation={validation_ms:.0f}ms, "
                  f"tool={tool_ms:.0f}ms, recovery={recovery_ms:.0f}ms")

            time.sleep(delay)

        # Calculate stats
        results["baseline"][category] = {
            "latencies": base_latencies,
            "p50": _percentile(base_latencies, 50),
            "p95": _percentile(base_latencies, 95),
            "avg": sum(base_latencies) / len(base_latencies) if base_latencies else 0
        }
        results["aegis"][category] = {
            "latencies": aegis_latencies,
            "p50": _percentile(aegis_latencies, 50),
            "p95": _percentile(aegis_latencies, 95),
            "avg": sum(aegis_latencies) / len(aegis_latencies) if aegis_latencies else 0,
            "breakdown": {
                stage: {
                    "p50": _percentile(times, 50),
                    "avg": sum(times) / len(times) if times else 0
                }
                for stage, times in aegis_breakdown.items()
            }
        }

    # Print summary
    _print_latency_summary(results)

    # Save
    _save_results(results)

    return results


def _extract_stage_timing(result, stage_name: str) -> float:
    """Extract stage timing from trace events."""
    for event in result.trace:
        if event.get("event") == stage_name or event.get("component") == stage_name:
            return event.get("duration_ms", 0)
    return 0.0


def _percentile(values: List[float], p: float) -> float:
    """Calculate percentile."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * (p / 100))
    return sorted_values[min(index, len(sorted_values) - 1)]


def _print_latency_summary(results: Dict[str, Any]):
    """Print latency comparison table."""
    print(f"\n{'=' * 80}")
    print(f"LATENCY SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n{'Category':<25} {'Baseline p50':<15} {'Aegis p50':<15} {'Aegis p95':<15}")
    print(f"{'─' * 70}")

    for category in LATENCY_QUERIES.keys():
        base = results["baseline"][category]
        aegis = results["aegis"][category]
        print(f"{category:<25} {base['p50']:>10.0f}ms {aegis['p50']:>10.0f}ms {aegis['p95']:>10.0f}ms")

    print(f"\n{'=' * 80}")
    print(f"AEGIS STAGE BREAKDOWN (p50)")
    print(f"{'=' * 80}")
    print(f"{'Category':<25} {'Plan':<10} {'Validation':<12} {'Tool':<10} {'Recovery':<10}")
    print(f"{'─' * 67}")

    for category in LATENCY_QUERIES.keys():
        bd = results["aegis"][category]["breakdown"]
        print(f"{category:<25} "
              f"{bd['plan']['p50']:>6.0f}ms "
              f"{bd['validation']['p50']:>6.0f}ms "
              f"{bd['tool']['p50']:>6.0f}ms "
              f"{bd['recovery']['p50']:>6.0f}ms")


def _save_results(results: Dict[str, Any]):
    """Save latency benchmark to JSON."""
    data_dir = Path("Data")
    data_dir.mkdir(exist_ok=True)

    filepath = data_dir / "latency_benchmark.json"

    # Remove raw latencies for cleaner file
    clean = {"baseline": {}, "aegis": {}}
    for agent, categories in results.items():
        if agent == "summary":
            continue
        for category, stats in categories.items():
            clean[agent][category] = {
                "p50_ms": stats["p50"],
                "p95_ms": stats["p95"],
                "avg_ms": stats["avg"]
            }

    with open(filepath, "w") as f:
        json.dump(clean, f, indent=2)

    print(f"\n📁 Saved to: {filepath}")