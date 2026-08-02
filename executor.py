from tools.registry import ToolRegistry
from engine.types import ExecutionRequest,ExecutionResponse
import time

class Executor:
    """The LLM decides what should be done.
        The Executor decides who should do it.
        The Tool decides how to do it."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(self, request: ExecutionRequest,max_attempt:int  = 3 , wait : float = 1.0):
        start = time.perf_counter()
        tool_name=request.tool
        for attempt in range(1,max_attempt+1):
            try:
                tool = self.registry.get(tool_name)
                raw_result = tool.execute(request)
                response=ExecutionResponse(
                status="success",
                result=raw_result,
                metadata={
                    "tool":tool_name,
                    "attempts_taken": attempt
                }
            )
            except Exception as e:
            # 4. Catch any Exception globally and Build a Failure Response
                response = ExecutionResponse(
                    status="failed",
                    error=str(e),
                    metadata={"tool": tool_name,
                    "failed_attempts": attempt
                    }
            )
                if attempt < max_attempt:
                    print(f"Attempt {attempt} retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"All {max_attempt} attempts exhausted")

        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        response.metadata["duration_ms"] = round(duration_ms, 3)

        return response
