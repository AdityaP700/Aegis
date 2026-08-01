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