import os
import requests
from typing import Dict, Any,List
from dotenv import load_dotenv
from tools.base import BaseTool
from engine.types import ExecutionRequest


load_dotenv()

class WeatherTool(BaseTool):
    """Fetches real-time weather data from OpenWeather API."""

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY not found in .env file. "
                "Get a free key at https://openweathermap.org/api"
            )
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "Fetches current weather for a city: temperature, condition, humidity"

    @property
    def required_args(self)-> List[str]:
        return ["city"]

    @property
    def capabilities(self) -> List[str]:        # ← NEW
        """This tool only supports current weather — not historical, not forecast."""
        return ["current_weather"]

    def _fetch_from_api(self, city: str) -> Dict[str, Any]:
        """
        Raw API call to OpenWeather.

        Args:
            city: City name (e.g., "London")

        Returns:
            Raw JSON response from API

        Raises:
            ValueError: If city not found or API error
            ConnectionError: If network issues
        """
        params = {
            "q": city, #sending the city as the param
            "appid": self.api_key, #sending the api key as a param
            "units": "metric"  # Celsius
        }
    # Just send raw data
        response = requests.get(self.base_url, params=params, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"City '{city}' not found")
        elif response.status_code == 401:
            raise ValueError("Invalid API key. Check your OPENWEATHER_API_KEY in .env")
        elif response.status_code == 429:
            raise ConnectionError("API rate limit exceeded. Try again later.")
        else:
            raise ConnectionError(
                f"API returned status {response.status_code}: {response.text}"
            )

    def _normalize_response(self, raw_data: Dict[str, Any], city: str) -> Dict[str, Any]:
        """
        Transform OpenWeather's verbose response into clean, normalized format.

        Args:
            raw_data: Raw JSON from OpenWeather
            city: Original city name requested

        Returns:
            Normalized dict with only the fields we care about
        """
        return {
            "city": city,
            "temperature": raw_data["main"]["temp"],
            "feels_like": raw_data["main"]["feels_like"],
            "condition": raw_data["weather"][0]["main"],
            "description": raw_data["weather"][0]["description"],
            "humidity": raw_data["main"]["humidity"],
            "pressure": raw_data["main"]["pressure"],
            "wind_speed": raw_data["wind"]["speed"],
            "country": raw_data["sys"]["country"]
        }

    def execute(self, request: ExecutionRequest, trace: list) -> Dict[str, Any]:
        """
        Execute weather lookup through Aegis.

        Args:
            request: ExecutionRequest with city in arguments
            trace: Trace list for observability

        Returns:
            Normalized weather data dict
        """
        ##read the request -> arguments -> city -> london (lets say)
        city = request.arguments.get("city")
        if not city:
            raise ValueError("'city' argument is required")

        # Trace: Starting API call
        trace.append({
            "component": "weather_tool",
            "event": "api_call_started",
            "city": city
        })

        try:
            # now define which city to be fetched
            raw_data = self._fetch_from_api(city)

            # Trace: API responded successfully
            trace.append({
                "component": "weather_tool",
                "event": "api_response_received",
                "city": city,
                "status_code": 200
            })

            # Normalize the response
            normalized = self._normalize_response(raw_data, city)

            # Trace: Normalization complete
            trace.append({
                "component": "weather_tool",
                "event": "response_normalized",
                "city": city,
                "fields_extracted": list(normalized.keys())
            })

            return normalized

        except ValueError as e:
            # City not found or bad API key — fatal, don't retry
            trace.append({
                "component": "weather_tool",
                "event": "api_error_fatal",
                "city": city,
                "error": str(e)
            })
            raise  # Re-raise for executor to handle as fatal

        except Exception as e:
            # Network errors, rate limits — retryable
            trace.append({
                "component": "weather_tool",
                "event": "api_error_operational",
                "city": city,
                "error": str(e)
            })
            raise  # Re-raise for executor to retry

