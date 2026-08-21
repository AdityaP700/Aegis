"""Save raw API response for Paris — no LLM, no Aegis, no validation."""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# This is EXACTLY what the WeatherTool sends when "last Monday" is dropped
params = {
    "q": "Paris",
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(BASE_URL, params=params, timeout=10)

# Save full response
result = {
    "requested_query": "What was the weather in Paris last Monday?",
    "what_was_sent_to_api": params,
    "what_was_dropped": "last Monday (temporal context not passed to API)",
    "http_status": response.status_code,
    "api_response": response.json() if response.status_code == 200 else None
}

data_dir = Path("Data")
data_dir.mkdir(exist_ok=True)
filepath = data_dir / "raw_weather_api_response.json"

with open(filepath, "w") as f:
    json.dump(result, f, indent=2)

print(f"Saved to: {filepath}")
print(f"\nWhat was sent to API: {params}")
print(f"What was dropped: last Monday")
print(f"API returned: Current weather for Paris")
print(f"Temperature: {result['api_response']['main']['temp']}°C")