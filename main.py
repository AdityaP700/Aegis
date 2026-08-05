import json
from pathlib import Path
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from engine.types import ExecutionRequest
from executor import Executor

def save_to_file(response, filename):
    """Save response to Data/ folder."""
    data_dir = Path("Data")
    data_dir.mkdir(exist_ok=True)

    filepath = data_dir / filename
    with open(filepath, "w") as f:
        json.dump({
            "status": response.status,
            "result": response.result,
            "metadata": response.metadata,
            "trace": response.trace
        }, f, indent=2)

    print(f"  ✓ Saved: {filepath}")

def test_single_search(executor, query, num_results=3):
    """Test a single search query and print results."""
    print(f"\n  🔍 Query: \"{query}\"")

    request = ExecutionRequest(
        tool="search",
        arguments={
            "query": query,
            "num_results": num_results
        }
    )

    response = executor.execute(request)

    if response.status == "success":
        results = response.result.get("results", [])
        print(f"    Found {len(results)} results:")

        for i, result in enumerate(results, 1):
            print(f"\n    {i}. {result['title']}")
            print(f"       {result['url']}")
            print(f"       {result['snippet'][:120]}...")
            if result.get('source'):
                print(f"       Source: {result['source']}")

        print(f"\n    ⏱️  Duration: {response.metadata.get('duration_ms')}ms")
        print(f"    Attempts: {response.metadata.get('attempts_taken')}")

        # Save to file
        safe_filename = f"search_{query.replace(' ', '_').lower()[:50]}.json"
        save_to_file(response, safe_filename)
    else:
        print(f"    ❌ Failed: {response.error}")
        print(f"    Failed attempts: {response.metadata.get('failed_attempts')}")

def main():
    # Setup
    registry = ToolRegistry()
    registry.register(SearchTool())
    executor = Executor(registry)

    print("=" * 60)
    print("AEGIS — Search Tool Testing")
    print("=" * 60)
    print(f"Tools registered: {registry.list_tools()}")

    # Test queries
    queries = [
        "Attention Is All You Need paper",
        "best Python web framework 2026",
        "what is retrieval augmented generation",
    ]

    for query in queries:
        test_single_search(executor, query)

if __name__ == "__main__":
    main()