In the Aegis execution flow, a user submits a natural language prompt that the LLM/Agent reasons about and converts into a structured ExecutionRequest specifying a tool and arguments;

the Executor then consults the Tool Registry to retrieve the matching tool implementation (such as CalculatorTool), invokes its execute method, and receives a structured ExecutionResponse (success with result or failure with error) which it forwards unchanged, while the components maintain clear responsibilities—ExecutionRequest and ExecutionResponse as standard formats,

BaseTool as the contract, the Registry for name-to-implementation mapping, the Executor purely as orchestrator, tools for actual work, and the LLM for deciding and preparing the request—with future enhancements planned for retries, timeouts, metrics, tracing, and logging.

```User
  │
  ▼
ExecutionRequest
  │
  ▼
Executor
  │
  ▼
Registry
  │
  ▼
CalculatorTool
  │
  ▼
ExecutionResponse```