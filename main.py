from brain.validator import Validator
from tools.weather import WeatherTool
from tools.github import GitHubTool
from tools.search_tool import SearchTool
from tools.registry import ToolRegistry
from executor import Executor
from brain.groq_brain import GroqBrain
from test.test_runner import run_full_test_suite

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

def main():
    print("=" * 60)
    print("AEGIS — Reliability Runtime")
    print("=" * 60)

    brain, validator, executor = setup_aegis()
    print(f"✓ Brain: {brain.provider_name}")
    print(f"✓ Tools: {executor.registry.list_tools()}")

    # Run full test suite with post-validation
    results = run_full_test_suite(brain, validator, executor)


if __name__ == "__main__":
    main()