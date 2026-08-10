"""Runs the Aegis test suite and saves results."""
import time
import json
from pathlib import Path
from engine.types import ExecutionRequest


def run_full_test_suite(brain, validator, executor, save_results=True):
    """Run all test cases and display results in a table."""

    from test.test_suites import TEST_QUERIES

    results = []

    print(f"\n{'=' * 80}")
    print(f"RUNNING {len(TEST_QUERIES)} TEST CASES")
    print(f"{'=' * 80}\n")

    for category, query in TEST_QUERIES:
        display_query = query if len(query) <= 50 else query[:47] + "..."

        try:
            plan = brain.think(query)
            plan = validator.validate(plan)

            # If plan passed, execute and post-validate
            post_passed = None
            post_errors = []
            if plan.validation_status == "passed":
                request = ExecutionRequest(tool=plan.tool, arguments=plan.arguments)
                response = executor.execute(request)
                post = validator.post_validate(plan, response)
                post_passed = post.passed
                post_errors = post.all_errors

            if plan.validation_status == "passed":
                icon = "✅" if post_passed else "⚠️"
                detail = f"{plan.tool}.{plan.operation}"
            else:
                icon = "❌"
                detail = plan.validation_errors[0][:50] if plan.validation_errors else "unknown"

            results.append({
                "category": category,
                "query": display_query,
                "status": plan.validation_status,
                "tool": plan.tool,
                "operation": plan.operation,
                "capability": plan.requested_capability,
                "confidence": plan.confidence,
                "post_passed": post_passed,
                "post_errors": post_errors,
                "detail": detail,
                "icon": icon
            })

            time.sleep(3)  # Rate limit protection

        except Exception as e:
            results.append({
                "category": category,
                "query": display_query,
                "status": "CRASHED",
                "tool": "ERROR",
                "operation": "-",
                "capability": "-",
                "confidence": 0.0,
                "post_passed": None,
                "post_errors": [str(e)],
                "detail": str(e)[:50],
                "icon": "💥"
            })

    # Print table
    _print_results_table(results)

    # Save to file
    if save_results:
        _save_results(results)

    return results


def _print_results_table(results):
    """Print formatted results table."""
    print(f"\n{'─' * 80}")
    print(f"{'Cat':<12} {'Query':<35} {'St':<6} {'Tool.Operation':<22} {'Conf':<6} {'Post':<6}")
    print(f"{'─' * 80}")

    for r in results:
        post_icon = "✓" if r['post_passed'] else ("✗" if r['post_passed'] is False else "-")
        print(f"{r['category']:<12} {r['query']:<35} {r['icon']:<6} {r['tool']}.{r['operation']:<14} {r['confidence']:<6.1f} {post_icon:<6}")

    # Summary
    passed = sum(1 for r in results if r['status'] == 'passed' and r['post_passed'] != False)
    failed = sum(1 for r in results if r['status'] == 'failed' or r['post_passed'] == False)
    crashed = sum(1 for r in results if r['status'] == 'CRASHED')
    total = len(results)

    print(f"\n{'─' * 80}")
    print(f"SUMMARY")
    print(f"{'─' * 80}")
    print(f"  ✅ Passed:  {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"  ❌ Failed:  {failed}/{total} ({failed/total*100:.0f}%)")
    print(f"  💥 Crashed: {crashed}/{total} ({crashed/total*100:.0f}%)")

    # Breakdown by category
    print(f"\n{'─' * 80}")
    print(f"BY CATEGORY")
    print(f"{'─' * 80}")

    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'total': 0}
        categories[cat]['total'] += 1
        if r['status'] == 'passed' and r['post_passed'] != False:
            categories[cat]['passed'] += 1

    for cat, stats in categories.items():
        pct = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"  {cat:<15} {bar} {stats['passed']}/{stats['total']}")


def _save_results(results):
    """Save test results to JSON file."""
    data_dir = Path("Data")
    data_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = data_dir / f"test_results_{timestamp}.json"

    # Convert to serializable format
    serializable = []
    for r in results:
        serializable.append({
            "category": r["category"],
            "query": r["query"],
            "status": r["status"],
            "tool": r["tool"],
            "operation": r["operation"],
            "confidence": r["confidence"],
            "post_validation_passed": r["post_passed"],
            "post_errors": r["post_errors"]
        })

    with open(filepath, "w") as f:
        json.dump(serializable, f, indent=2)

    print(f"\n📁 Results saved to: {filepath}")