from abc import abstractmethod
from tools.base import BaseTool
import ast
from engine.types import ExecutionRequest, ExecutionResponse
class CalculatorTool(BaseTool):
    @property
    def name(self)->str:
        return "calculator"

    def execute(
        self,
        request : ExecutionRequest

    )->ExecutionResponse:
        expression = request.arguments["expression"]

        try:
            result = ast.parse(expression)
            return ExecutionResponse(
                status = "success",
                result=result,
                metadata={
                    "tool":self.name
                }
            )

        except Exception as e:
            return ExecutionResponse(
                status = "failed",
                error= str(e),
                metadata={
                    # the name of the method is allowed right??
                    "tool":self.name
                }
            )







