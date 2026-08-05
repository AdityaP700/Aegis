import json
from pathlib import Path
from tools.github import GitHubTool
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

def test_single_repo(executor, repo):
    """Test a single repo and print results."""
    print(f"\n  Repo: {repo}")

    request = ExecutionRequest(
        tool="github",
        arguments={"repo": repo}
    )

    response = executor.execute(request)

    if response.status == "success":
        r = response.result
        print(f"    ⭐ {r['stars']:,} stars")
        print(f"    🔧 Language: {r['language']}")
        print(f"    📜 License: {r['license']}")
        print(f"    🍴 Forks: {r['forks']:,}")
        print(f"    ⚠️  Open Issues: {r['open_issues']}")
        print(f"    📝 {r['description'][:100] if r['description'] else 'No description'}...")
        print(f"    🔗 {r['url']}")
        print(f"    ⏱️  Duration: {response.metadata.get('duration_ms')}ms")
        save_to_file(response, f"github_{repo.replace('/', '_')}.json")
    else:
        print(f"    ❌ Failed: {response.error}")
        print(f"    Failed attempts: {response.metadata.get('failed_attempts')}")

def main():
    # Setup
    registry = ToolRegistry()
    registry.register(GitHubTool())
    executor = Executor(registry)

    print("=" * 60)
    print("AEGIS — GitHub Tool Testing")
    print("=" * 60)
    print(f"Tools registered: {registry.list_tools()}")

    # Test cases
    repos_to_test = [
        "karpathy/nanoGPT",
        "torvalds/linux",
        "AdityaP700/exora-task",
        "nonexistent/repo12345",     # Should fail: 404
        "invalidformat",             # Should fail: bad format
    ]

    for repo in repos_to_test:
        test_single_repo(executor, repo)



if __name__ == "__main__":
    main()