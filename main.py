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
        "city": "12341"
    }
)

response = executor.execute(request,max_attempt=5,wait=3.0)

print(response.model_dump())