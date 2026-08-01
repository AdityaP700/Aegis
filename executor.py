from tools.registry import ToolRegistry
from engine.types import ExecutionRequest


class Executor:
    """The LLM decides what should be done.
        The Executor decides who should do it.
        The Tool decides how to do it."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, request: ExecutionRequest):

        tool = self.registry.get(request.tool)

        return tool.execute(request)

