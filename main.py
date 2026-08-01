from executor import Executor
from tools.registry import ToolRegistry
from tools.calculator import CalculatorTool
from engine.types import ExecutionRequest


registry = ToolRegistry()

registry.register(CalculatorTool())

executor = Executor(registry)

request = ExecutionRequest(
    tool="calculator",
    arguments={
        "expression": "25 * (17 + 3) - 8"
    }
)

response = executor.execute(request)

print(response.model_dump())