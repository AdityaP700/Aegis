#this is the language every component speaks
# we will define the contracts

from typing import Any,List,Dict,Literal,Optional
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
    trace : List[Dict[str,Any]]=[] # string keys, any values

class ExecutionPlan(BaseModel):
    """
    in a brain ,what are the thing we first think of :
    10 pehli baat toh yeh hai ki ,for any of the action
    there is the interpretation
    based on the interpretation ,we have to decide
    do i need to send signal to any of the body parts ?/
    if yes what type of signal based on the request
    and once the request has been sent ,what could be the response
    and then final orchestration
    """

    intent : str = Field(description="what the user wants to do")
    tool : str = Field(description ="Tool to execute")
    arguments : Dict[str,Any]=Field(description="Arguments for the tool")
    confidence : float = Field(default=1.0,ge=0.0,le=1.0)
    #You should use that exact syntax when you want to restrict a variable
    #  to a strict, pre-defined set o
    #when u dont want to use heavy enums
    validation_status: Literal["pending", "passed", "failed"] = "pending"
    validation_errors: List[str] = []
    requested_capability:str=Field(
        default=""

        #LLm classifies what user wants
    )
    """Operation : what to do with that system"""
    operation:str=Field(
        default="",
        description="specific operation requested (e.g. current_weather ,'historical_weather'"
    )

class PostExecutionResult(BaseModel):
    """Result of post-execution validation."""
    integrity: bool = True
    integrity_errors: List[str] = []
    plausibility: bool = True
    plausibility_errors: List[str] = []
    completeness: bool = True
    completeness_errors: List[str] = []

    @property
    def passed(self) -> bool:
        return self.integrity and self.plausibility and self.completeness

    @property
    def all_errors(self) -> List[str]:
        return self.integrity_errors + self.plausibility_errors + self.completeness_errors

class TrialResult(BaseModel):
    """Structured result of running one query through Aegis."""
    query: str = ""
    final_status: str = "pending"  # "success", "failed", "unknown", "crash"
    tool: str = ""
    operation: str = ""
    arguments: Dict[str, Any] = {}
    confidence: float = 0.0
    fallback_triggered: bool = False
    capability_rejected: bool = False
    validation_failed: bool = False
    retry_attempted: bool = False
    post_validation_passed: Optional[bool] = None
    post_validation_errors: List[str] = []
    trace: List[Dict[str, Any]] = []
    duration_ms: float = 0.0