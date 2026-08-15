"""Runs stochasticity-focused Pass^k evaluation."""
from evals.loader import load_cases_from_file
from evals.passk_runner import run_passk, print_passk_results, compare_passk


def run_stochastic_eval(brain, validator, executor, registry, k: int = 3):
    """
    Run Pass^k on 5 representative cases testing stochasticity:
    1. Happy path
    2. Ambiguous routing
    3. Argument extraction
    4. Recovery/fallback
    5. Edge/multi-intent
    """
    cases = load_cases_from_file("evals/stochastic_cases.json")

    print(f"\n{'=' * 80}")
    print(f"STOCHASTICITY EVALUATION")
    print(f"Testing consistency under ambiguity")
    print(f"Cases: {len(cases)}, Trials per case: {k}")
    print(f"{'=' * 80}")

    # Phase 1: Aegis
    print(f"\n{'─' * 80}")
    print(f"PHASE 1: AEGIS (k={k})")
    print(f"{'─' * 80}")
    aegis_results = run_passk(
        cases, brain, validator, executor, registry,
        k=k, delay=2.0, use_baseline=False
    )
    print_passk_results(aegis_results)

    # Phase 2: Baseline
    print(f"\n{'─' * 80}")
    print(f"PHASE 2: BASELINE (k={k})")
    print(f"{'─' * 80}")
    baseline_results = run_passk(
        cases, brain, validator, executor, registry,
        k=k, delay=2.0, use_baseline=True
    )
    print_passk_results(baseline_results)

    # Phase 3: Comparison
    compare_passk(aegis_results, baseline_results)

    # Analysis
    _analyze_stochasticity(aegis_results)

    return aegis_results, baseline_results


def _analyze_stochasticity(results):
    """Analyze which cases show inconsistency."""
    print(f"\n{'─' * 80}")
    print(f"STOCHASTICITY ANALYSIS")
    print(f"{'─' * 80}")

    consistent = []
    flaky = []

    for r in results:
        if r.pass_carat_k:
            consistent.append(r.case.id)
        else:
            flaky.append({
                "case": r.case.id,
                "success_rate": f"{r.success_count}/{r.k}",
                "query": r.case.query
            })

    print(f"\n  ✅ CONSISTENT CASES (Pass^k = 1):")
    for case_id in consistent:
        print(f"     - {case_id}")

    print(f"\n  ⚠️  FLAKY CASES (Pass^k = 0):")
    if flaky:
        for item in flaky:
            print(f"     - {item['case']}: {item['success_rate']} success")
            print(f"       Query: {item['query']}")
    else:
        print(f"     (none — all cases consistent)")

    print(f"\n  INTERPRETATION:")
    if not flaky:
        print(f"     Aegis maintains 100% consistency across all 5 representative cases.")
        print(f"     The reliability layer eliminates stochastic variation from the Brain.")
    else:
        print(f"     {len(flaky)} cases show inconsistency across {results[0].k if results else 'k'} trials.")
        print(f"     These are the cases where Brain uncertainty breaks through the reliability layer.")