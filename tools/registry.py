#its like a dictionary containing
#different tools
from tools.base import BaseTool


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    #Slots labeled with the brand name ("Sony", "Samsung")
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    #You snap a remote into its slot. The dock automatically
    # looks at the remote's label (tool.name) and places it in the matching slot.
    def get(self, tool_name: str) -> BaseTool:
        return self._tools[tool_name]
    #When you want to watch the Sony TV, you yell to the dock: "Give me the Sony remote!" The dock instantly
    #pulls the correct remote out of the "Sony" slot and hands it to you.
    def list_tools(self) -> list:
        """List all registered tool names."""
        return list(self._tools.keys())