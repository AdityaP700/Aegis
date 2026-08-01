from tools.types import ExecutionRequest
request = ExecutionRequest(
    tool="calculator",
    arguments = {
        "expression":"25*13"
    }

)
print(request)
print()
print(request.model_dump())
