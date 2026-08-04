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
        trace =[]
        trace.append({
            "component": "executor",
            "event": "execution_started",
            "tool": tool_name})
      # Smart Guard: Use the passed value. If it's empty (None),
      #  use the class default instead!
        final_max_attempts = max_attempt if max_attempt is not None else self.max_attempts
        final_wait = wait if wait is not None else self.retry_delay
        for attempt in range(1,final_max_attempts+1):
            try:
                trace.append({
                    "component": "executor",
                    "event": "execution_success",
                    "attempt": attempt
                })
                tool = self.registry.get(tool_name)
                if not tool:
                    raise ValueError(f"Tool '{tool_name}'is not registered")
#identify the tool and then send to that specific tool 
                raw_result = tool.execute(request,trace)
                trace.append({
                    "component": "executor",
                    "event": "attempt_started",
                    "attempt": attempt,
                    "max_attempts": final_max_attempts
                })
                response=ExecutionResponse(
                    status="success",
                    result=raw_result,
                    metadata={
                        "tool":tool_name,
                        "attempts_taken": attempt
                },
                trace =trace
            )

                end = time.perf_counter()
                response.metadata["duration_ms"] = round((end - start) * 1000, 3)
                return response
        # differentiating the errors
            except (KeyError,ValueError) as fatal_err:
                trace.append({
                    "component": "executor",
                    "event": "fatal_error_encountered",
                    "error_type": type(fatal_err).__name__,
                    "message": str(fatal_err),
                    "attempt": attempt
                })
                response = ExecutionResponse(
                    status="failed",
                    error=f"Fatal Execution Error:{str(fatal_err)}",
                    metadata={"tool": tool_name,
                    "failed_attempts": attempt,

                    },
                    trace=trace
                )
                print(f"Aborting early on attempt {attempt}:{fatal_err}")
                break

            except Exception as operational_err:
            # 4. Catch any Exception globally and Build a Failure Response
                trace.append({
                    "component": "executor",
                    "event": "operational_error_encountered",
                    "error_type": type(operational_err).__name__,
                    "message": str(operational_err),
                    "attempt": attempt
                })
                response = ExecutionResponse(
                    status="failed",
                    result=None,
                    error=str(operational_err),
                    metadata={
                    "tool": tool_name,
                    "failed_attempts": attempt
                    },
                    trace=trace
            )
                if attempt < final_max_attempts:
                    trace.append({
                        "component": "executor",
                        "event": "retry_wait_initiated",
                        "delay_seconds": wait,
                        "next_attempt": attempt + 1
                    })
                    print(f"Attempt {attempt} retrying in {final_wait}s...")
                    time.sleep(final_wait)
                else:
                    print(f"All {final_max_attempts} attempts exhausted")

        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        response.metadata["duration_ms"] = round(duration_ms, 3)

        return response
