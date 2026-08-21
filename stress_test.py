"""Aegis — Reliability Runtime with Evaluation Harness."""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path
import requests
from brain.groq_brain import GroqBrain
from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from executor import Executor
from evals.loader import load_cases
from evals.runner import run_cases
from evals.grader import grade_all, print_grades
from evals.metrics import build_report, print_report, save_report
from evals.passk_runner import run_passk, print_passk_results, compare_passk
from evals.latency_benchmark import run_latency_benchmark


def setup_aegis():
    """Initialize all Aegis components."""
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(GitHubTool())
    registry.register(SearchTool())

    tools_metadata = _extract_tools_metadata(registry)
    brain = GroqBrain(tools_metadata)
    validator = Validator(registry)
    executor = Executor(registry)

    return brain, validator, executor


def _extract_tools_metadata(registry: ToolRegistry) -> list:
    """Tell the Brain what tools exist and what they need."""
    metadata = []
    for tool_name, tool in registry._tools.items():
        metadata.append({
            "name": tool.name,
            "description": tool.description,
            "supported_operations": getattr(tool, 'supported_operations', []),
            "capabilities": getattr(tool, 'capabilities', []),
            "required_args": getattr(tool, 'required_args', [])
        })
    return metadata


def run_single_eval(brain, validator, executor, max_cases: int = None):
    """Run Aegis evaluation (single trial per case)."""
    cases = load_cases()
    if max_cases:
        cases = cases[:max_cases]

    outcomes = run_cases(cases, brain, validator, executor)
    grades = grade_all(outcomes)
    print_grades(grades)

    report = build_report(grades, outcomes)
    print_report(report)
    save_report(report)

    return report


def run_passk_eval(brain, validator, executor, max_cases: int = None, k: int = 3):
    """Run Pass@k / Pass^k evaluation (multiple trials per case)."""
    registry = executor.registry
    cases = load_cases()
    if max_cases:
        cases = cases[:max_cases]

    print(f"\n{'=' * 80}")
    print(f"PASS@K EVALUATION")
    print(f"Cases: {len(cases)}, Trials per case: {k}")
    print(f"{'=' * 80}")

    # Phase 1: Aegis
    print(f"\n{'─' * 80}")
    print(f"PHASE 1: AEGIS (k={k} trials per case)")
    print(f"{'─' * 80}")
    aegis_results = run_passk(
        cases, brain, validator, executor, registry,
        k=k, delay=2.0, use_baseline=False
    )
    print_passk_results(aegis_results)

    # Phase 2: Baseline
    print(f"\n{'─' * 80}")
    print(f"PHASE 2: BASELINE (k={k} trials per case)")
    print(f"{'─' * 80}")
    baseline_results = run_passk(
        cases, brain, validator, executor, registry,
        k=k, delay=2.0, use_baseline=True
    )
    print_passk_results(baseline_results)

    # Phase 3: Comparison
    compare_passk(aegis_results, baseline_results)

    return aegis_results, baseline_results


def run_stochastic_eval(brain, validator, executor, k: int = 3):
    """Run stochasticity evaluation (5 representative cases)."""
    from evals.stochastic_runner import run_stochastic_eval
    return run_stochastic_eval(brain, validator, executor, executor.registry, k=k)


def run_latency_eval(brain, validator, executor, runs_per_category: int = 3):
    """Run latency benchmark (Baseline vs Aegis)."""
    results = run_latency_benchmark(
        brain, validator, executor, executor.registry,
        runs_per_category=runs_per_category,
        delay=2.0
    )
    return results


def main():
    print("=" * 60)
    print("AEGIS — Reliability Runtime")
    print("=" * 60)

    brain, validator, executor = setup_aegis()
    print(f"✓ Brain: {brain.provider_name}")
    print(f"✓ Tools: {executor.registry.list_tools()}")
    print(f"✓ Validator: ready")
    print(f"✓ Executor: ready")

    print(f"\n{'─' * 60}")
    print("EVALUATION MODES")
    print(f"{'─' * 60}")
    print("  1. Single Evaluation (1 trial per case)")
    print("  2. Pass@k Evaluation (multiple trials per case)")
    print("  3. Run Both")
    print("  4. Stochasticity Evaluation (5 cases × k trials)")
    print("  5. Latency Benchmark (Baseline vs Aegis)")
    print("  6. Stress Test (5 adversarial cases)")

    choice = input("\nSelect mode (1/2/3/4/5/6): ").strip()

    max_cases = None
    k = 3
    runs_per_category = 3

    if choice in ["1", "2", "3", "4"]:
        cases_input = input(f"Max cases (press Enter for all): ").strip()
        if cases_input:
            max_cases = int(cases_input)

    if choice == "1":
        run_single_eval(brain, validator, executor, max_cases=max_cases)

    elif choice == "2":
        k_input = input(f"Trials per case (default {k}): ").strip()
        if k_input:
            k = int(k_input)
        run_passk_eval(brain, validator, executor, max_cases=max_cases, k=k)

    elif choice == "3":
        run_single_eval(brain, validator, executor, max_cases=max_cases)
        k_input = input(f"\nTrials per case for Pass@k (default {k}): ").strip()
        if k_input:
            k = int(k_input)
        run_passk_eval(brain, validator, executor, max_cases=max_cases, k=k)

    elif choice == "4":
        k_input = input(f"Trials per case (default {k}): ").strip()
        if k_input:
            k = int(k_input)
        run_stochastic_eval(brain, validator, executor, k=k)

    elif choice == "5":
        runs_input = input(f"Runs per category (default {runs_per_category}): ").strip()
        if runs_input:
            runs_per_category = int(runs_input)
        run_latency_eval(brain, validator, executor, runs_per_category=runs_per_category)

    elif choice == "6":
        from stress_test import run_stress_test
        run_stress_test()

    else:
        print("Invalid choice. Running single evaluation...")
        run_single_eval(brain, validator, executor, max_cases=max_cases)

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)

    data_dir = Path("Data")
    data_dir.mkdir(exist_ok=True)
    filepath = data_dir / "raw_weather_api_response.json"

    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()