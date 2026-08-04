import json
from pathlib import Path
from tools.weather import WeatherTool
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

    print(f"✓ Saved: {filepath}")

def main():
    # Setup
    registry = ToolRegistry()
    registry.register(WeatherTool())
    executor = Executor(registry)

    # Test cities
    cities = ["London", "Tokyo", "Delhi"]

    for city in cities:
        request = ExecutionRequest(
            tool="weather",
            arguments={"city": city}
        )

        response = executor.execute(request)

        if response.status == "success":
            r = response.result
            print(f"\n{city}: {r['temperature']}°C, {r['condition']}, Humidity: {r['humidity']}%")
            save_to_file(response, f"weather_{city.lower()}.json")
        else:
            print(f"\n{city}: Failed — {response.error}")

if __name__ == "__main__":
    main()