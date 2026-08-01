from abc import abstractmethod
from tools.base import BaseTool
import ast
from engine.types import ExecutionRequest, ExecutionResponse
class CalculatorTool(BaseTool):
    @property
    def name(self)->str:
        return "calculator"
    def _evaluate(self ,node:ast.AST)-> float | int:
        if isinstance(node,ast.Constant):
            return node.value

        elif isinstance(node,ast.BinOp):
            left_value=self._evaluate(node.left)
            right_value=self._evaluate(node.right)

            if isinstance(node.op,ast.Add):
                return left_value+right_value
            elif isinstance(node.op,ast.Mult):
                return left_value*right_value
            elif isinstance(node.op,ast.Sub):
                return left_value-right_value
            elif isinstance(node.op,ast.Div):
                if right_value==0:
                    raise ZeroDivisionError("cannot divide by zero")
                return left_value/right_value

    def execute(
        self,
        request : ExecutionRequest
    )->ExecutionResponse:
        expression = request.arguments["expression"]

        try:
            result = ast.parse(expression,mode='eval')
            final_math_result = self._evaluate(result.body)
            return ExecutionResponse(
                status = "success",
                result=final_math_result,
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







