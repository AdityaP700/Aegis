"""Runs the Aegis test suite and saves results."""
import time
import json
from pathlib import Path
from engine.types import ExecutionRequest
from pipeline  import process_query

def run_full_test_suite(brain, validator, executor, save_results=True):
    from test.test_suites import TEST_QUERIES

    results = []
    print(f"\n{'=' * 80}")
    print(f"RUNNING {len(TEST_QUERIES)} TEST CASES")
    print(f"{'=' * 80}\n")

    for category, query in TEST_QUERIES:
        display_query = query if len(query) <= 50 else query[:47] + "..."

        try:
            response = process_query(query, brain, validator, executor)

            if response and response.status == "success":
                icon = "✅"
                status = "passed"
                tool = response.metadata.get("tool", "search")
                operation = "web_search"
                post_passed = True
            elif response:
                icon = "❌"
                status = "failed"
                tool = response.metadata.get("tool", "unknown")
                operation = ""
                post_passed = False
            else:
                icon = "❌"
                status = "failed"
                tool = "unknown"
                operation = ""
                post_passed = None

            results.append({
                "category": category,
                "query": display_query,
                "status": status,
                "tool": tool,
                "operation": operation,
                "capability": "",
                "confidence": 0.3,
                "post_passed": post_passed,
                "post_errors": [],
                "detail": "Processed via pipeline",
                "icon": icon
            })

            time.sleep(3)

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

    _print_results_table(results)
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