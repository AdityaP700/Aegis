"""Aegis — Reliability Runtime with Evaluation Harness."""
from brain.groq_brain import GroqBrain
from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from executor import Executor
from evals.compare import run_complete_analysis, print_comparison_table, save_comparison


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
        contract = tool.contract
        metadata.append({
            "name": contract.name,
            "description": contract.description,
            "supported_operations": contract.supported_operations,
            "capabilities": contract.capabilities,
            "required_args": contract.required_args
        })
    return metadata


def main():
    """Run complete evaluation: Baseline vs Aegis."""
    print("=" * 60)
    print("AEGIS — Reliability Runtime")
    print("=" * 60)

    # Setup
    brain, validator, executor = setup_aegis()
    registry = executor.registry

    print(f"✓ Brain: {brain.provider_name}")
    print(f"✓ Tools: {registry.list_tools()}")
    print(f"✓ Validator: ready")
    print(f"✓ Executor: ready")

    # Run complete analysis
    # Set max_cases=None to run all 22, or a number for quick test
    comparisons = run_complete_analysis(
        brain=brain,
        validator=validator,
        executor=executor,
        registry=registry,
        max_cases=10,        # ← Change to None for full 22 cases
        delay=2.0            # ← Seconds between API calls (rate limit protection)
    )

    # Display comparison table
    print_comparison_table(comparisons)

    # Save comparison report
    save_comparison(comparisons)

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()