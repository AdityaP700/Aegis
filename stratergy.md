Why Pydantic?
it gives us :
- validation
- serialization
- type checking
- API compatibility

well in the case of the
metadata:dict[str,Any ]= Field(default_factory=dict)
"""{}"""

model_dump() : "Convert this Pydantic object into a plain Python dictionary."

ABC : abstract base classes
The BaseTool ABC is the design standard for a Universal TV Remote Control Interface.Every TV remote on earth has a Power Button and a Volume Up Button.

No matter if the remote is made by Sony, Samsung, or LG, the buttons look and act the same to the human finger.The Interface (ABC): The physical layout layout of the remote (Power Button, Volume Up Button).

The Implementation (Concrete Classes): The actual infrared/Bluetooth chips inside the Sony, Samsung, or LG remotes that send different signals to different TVs.

Abstract Class
↓
Promise
↓
Implementation
↓
Excecution

An Abstract Base Class doesn't provide behavior. It provides a contract that guarantees behavior exists.

Python is the building inspector.
BaseTool is just the blueprint.

Prompt
↓
LLM chooses tool
↓
Executor
↓
CalculatorTool
↓
ExecutionResponse

meanwhile
BaseTool
↓
Only guarantees

CalculatorTool has
name
execute()

                   User
                    │
                    ▼
           "What is 25 × 17?"
                    │
                    ▼
               LLM / Agent
                    │
                    ▼
          ExecutionRequest
        ┌──────────────────────┐
        │ tool = calculator    │
        │ expression = 25*17   │
        └──────────────────────┘
                    │
                    ▼
                 Executor
                    │
          tools["calculator"]
                    │
                    ▼
        CalculatorTool.execute()
                    │
         expression = "25*17"
                    │
             result = 425
                    │
                    ▼
            ExecutionResponse
        ┌──────────────────────┐
        │ status = success     │
        │ result = 425         │
        │ metadata = {...}     │
        └──────────────────────┘
                    │
                    ▼
                   User


__init_subclass__
Think of this like a tracking chip built into the master blueprint. The moment a factory manufactures a new remote model, the chip broadcasts a signal to the docking station to create a slot for it automatically.

 (colon) is used to declare a Type Hint (a rule describing what data type is allowed), while = (equals sign) is used to assign a Value (the actual data stored in memory).

In the Aegis execution flow, a user submits a natural language prompt that the LLM/Agent reasons about and converts into a structured ExecutionRequest specifying a tool and arguments;

the Executor then consults the Tool Registry to retrieve the matching tool implementation (such as CalculatorTool), invokes its execute method, and receives a structured ExecutionResponse (success with result or failure with error) which it forwards unchanged, while the components maintain clear responsibilities—ExecutionRequest and ExecutionResponse as standard formats,

BaseTool as the contract, the Registry for name-to-implementation mapping, the Executor purely as orchestrator, tools for actual work, and the LLM for deciding and preparing the request—with future enhancements planned for retries, timeouts, metrics, tracing, and logging.

- ast.parse() : it is an X-Ray Architecture Machine: It can scan a complex blueprint for a house or an engine. It doesn't build the house; it just gives you a map of the layout so you can look for hidden security flaws before giving the builder approval.


time.perf_counter()
- monotonic
- high precision
- made for measuring execution time

✅ Removed eval()
✅ Built a safe AST interpreter
✅ Execution timing (perf_counter())
✅ Structured metadata