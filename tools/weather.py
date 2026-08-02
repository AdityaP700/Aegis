from abc import abstractmethod
from tools.base import BaseTool
import ast
from engine.types import ExecutionRequest, ExecutionResponse
WEATHER_DATA = {
    "london": {
        "temperature": 18,
        "condition": "Cloudy"
    },
    "tokyo": {
        "temperature": 30,
        "condition": "Sunny"
    },
    "delhi": {
        "temperature": 34,
        "condition": "Hot"
    },
    "paris": {
        "temperature": 22,
        "condition": "Rainy"
    }
}
class WeatherTool(BaseTool):
    @property
    def name(self)->str:
        return "weather"

    def _estimate(self ,city:str)-> dict:
# the city is in string ,the returning should be in dictionary cuz its a collection of info
        city_lower = city.strip().lower()
#traverse in the dictionary to find out if it exits or not
        if city_lower in WEATHER_DATA:
            return {
                #if exists then return in terms of value ,not types
                "temperature":WEATHER_DATA[city_lower]["temperature"],
                "condition":WEATHER_DATA[city_lower]["condition"]
            }
        else:
            raise ValueError(f"Invalid city name detected:{city}")
    def execute(
        self,
        request : ExecutionRequest
    )->dict:
        expression = request.arguments["city"]

        result=self._estimate(expression)
        return result



