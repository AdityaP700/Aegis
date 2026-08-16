from tools.registry import ToolRegistry
from engine.otel import setup_tracing
from engine.types import ExecutionRequest,ExecutionResponse
import time

tracer = setup_tracing()

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
        with tracer.start_as_current_span("tool.execute") as span:
            span.set_attribute("tool", tool_name)
            span.set_attribute("max_attempts", max_attempt or self.max_attempts)

            final_max_attempts = max_attempt if max_attempt is not None else self.max_attempts
            final_wait = wait if wait is not None else self.retry_delay
            for attempt in range(1,final_max_attempts+1):
                try:

                    tool = self.registry.get(tool_name)
                    if not tool:
                        raise ValueError(f"Tool '{tool_name}'is not registered")
#identify the tool and then send to that specific tool
                    raw_result = tool.execute(request,[])

                    response=ExecutionResponse(
                        status="success",
                        result=raw_result,
                        metadata={
                        "tool":tool_name,
                        "attempts_taken": attempt
                },
                trace =[]
            )
                    span.set_attribute("status","success")
                    span.set_attribute("attempts_taken",attempt)

                    end = time.perf_counter()
                    response.metadata["duration_ms"] = round((end - start) * 1000, 3)
                    return response
        # differentiating the errors
                except (KeyError,ValueError) as fatal_err:
                    span.set_attribute("status", "fatal_error")
                    span.set_attribute("error_type", type(fatal_err).__name__)
                    span.set_attribute("error_message", str(fatal_err))

                    response = ExecutionResponse(
                    status="failed",
                    error=f"Fatal Execution Error:{str(fatal_err)}",
                    metadata={"tool": tool_name,
                    "failed_attempts": attempt,

                    },
                    trace=[]
                )

                    print(f"Aborting early on attempt {attempt}:{fatal_err}")
                    break
                except Exception as operational_err:
                    span.set_attribute("status", "operational_error")
                    span.set_attribute("error_type", type(operational_err).__name_)


                    if attempt < final_max_attempts:
                        span.add_event(
                            "tool_retry",
                            {
                                "attempt": attempt,
                                "next_attempt": attempt + 1,
                                "delay_seconds": final_wait,
                                "reason": "operational_error"
                            }
                        )
                        print(f"attempt{attempt} failed ,retrying in {final_wait}")
                        time.sleep(final_wait)
                    else:
                        span.add_event(
                            "all_attempts_exhausted",
                            {
                                "attempts_used": attempt,
                                "max_attempts": final_max_attempts
                            }
                        )
                        print(f"All {final_max_attempts} attempts exhausted")

            end = time.perf_counter()
            duration_ms = (end - start) * 1000
            response = ExecutionResponse(
                status="failed",
                error="All attempts exhausted",
                metadata={
                    "tool": tool_name,
                    "failed_attempts": final_max_attempts,
                    "duration_ms": duration_ms
                },
                trace=[]
            )

            return response
