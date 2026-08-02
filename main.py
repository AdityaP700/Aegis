from tools.weather import WeatherTool
from executor import Executor
from tools.registry import ToolRegistry
from tools.calculator import CalculatorTool
from engine.types import ExecutionRequest
from tools.weather import WeatherTool

registry = ToolRegistry()

registry.register(CalculatorTool())
registry.register(WeatherTool())
executor = Executor(registry)

request = ExecutionRequest(
    tool="weather",
    arguments={
        "city": "jakarta"
    }
)

response = executor.execute(request)

print(response.model_dump())