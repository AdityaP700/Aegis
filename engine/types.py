#this is the language every component speaks
# we will define the contracts

from typing import Any,List
from pydantic import BaseModel ,Field

#define two of the classes : executioneRequest ,ExecutionResponse
class ExecutionRequest(BaseModel):
    tool:str
    arguments: dict[str,Any]

class ExecutionResponse(BaseModel):
    status : str
    result : Any | None = None
    error : str | None = None
    metadata : dict[str,Any ]= Field(default_factory=dict)
    trace : List[str]=[]