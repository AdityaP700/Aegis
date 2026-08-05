"""centralised service to initialized the different tools"""
from tools.calculator import CalculatorTool
from tools.weather import WeatherTool
from tools.github import GitHubTool      # ← ADD THIS

__all__ = ["CalculatorTool", "WeatherTool", "GitHubTool"]