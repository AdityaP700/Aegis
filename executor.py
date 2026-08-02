from tools.registry import ToolRegistry
from engine.types import ExecutionRequest,ExecutionResponse
import time

class Executor:
    """The LLM decides what should be done.
        The Executor decides who should do it.
        The Tool decides how to do it."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.max_attempts = 3
        self.retry_delay = 1
    def execute(self, request: ExecutionRequest, max_attempt: int = None, wait: float = None ):
        start = time.perf_counter()
        tool_name=request.tool
      # Smart Guard: Use the passed value. If it's empty (None),
      #  use the class default instead!
        final_max_attempts = max_attempt if max_attempt is not None else self.max_attempts
        final_wait = wait if wait is not None else self.retry_delay
        for attempt in range(1,final_max_attempts+1):
            try:
                tool = self.registry.get(tool_name)
                if not tool:
                    raise ValueError(f"Tool '{tool_name}'is not registered")

                raw_result = tool.execute(request)

                response=ExecutionResponse(
                    status="success",
                    result=raw_result,
                    metadata={
                        "tool":tool_name,
                        "attempts_taken": attempt
                }
            )

                end = time.perf_counter()
                response.metadata["duration_ms"] = round((end - start) * 1000, 3)
                return response
        # differentiating the errors
            except (KeyError) as fatal_err:
                response = ExecutionResponse(
                    status="failed",
                    error=f"Fatal Execution Error:{str(fatal_err)}",
                    metadata={"tool": tool_name,
                    "failed_attempts": attempt,

                    }
                )
                print(f"Aborting early on attempt {attempt}:{fatal_err}")
                break

            except Exception as operational_err:
            # 4. Catch any Exception globally and Build a Failure Response
                response = ExecutionResponse(
                    status="failed",
                    error=str(operational_err),
                    metadata={"tool": tool_name,
                    "failed_attempts": attempt
                    }
            )
                if attempt < max_attempt:
                    print(f"Attempt {attempt} retrying in {wait}s...")
                    time.sleep(final_wait)
                else:
                    print(f"All {final_max_attempts} attempts exhausted")

        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        response.metadata["duration_ms"] = round(duration_ms, 3)

        return response
