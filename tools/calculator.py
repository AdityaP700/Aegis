from abc import abstractmethod
from tools.base import BaseTool
import ast
from engine.types import ExecutionRequest, ExecutionResponse
class CalculatorTool(BaseTool):
    @property
    def name(self)->str:
        return "calculator"
    def _evaluate(self ,node:ast.AST)-> float | int:
        if isinstance(node,ast.Constant) and isinstance(node.value, (int, float)):
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
        else:
            raise ValueError(f"Invalid non-numeric item detected: {type(node).__name__}")
    def execute(
        self,
        request : ExecutionRequest,
        trace : list
    )->ExecutionResponse:
        trace.append(f"Calculator Tool: Received request for expression :'{request.arguments.get('expression')}'")
        expression = request.arguments["expression"]


        result = ast.parse(expression,mode='eval')
        trace.append("Calculator Tool : Matching record found in database. Returning results.")
        return self._evaluate(result.body)
