from tools.registry import ToolRegistry
from engine.types import ExecutionRequest
import time

class Executor:
    """The LLM decides what should be done.
        The Executor decides who should do it.
        The Tool decides how to do it."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, request: ExecutionRequest):
        start = time.perf_counter()
        tool = self.registry.get(request.tool)
        response = tool.execute(request)
        end=time.perf_counter()
        duration_ms=(end-start)*1000
        response.metadata["duration_ms"]=round(duration_ms,3)

        return response
