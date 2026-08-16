"""Aegis FastAPI service — one endpoint: POST /execute."""
from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace

from main import setup_aegis
from pipeline import process_query

app = FastAPI(title="Aegis", version="1.0.0")

# Initialize once at startup
brain, validator, executor = setup_aegis()
tracer = trace.get_tracer("aegis-api")


class QueryRequest(BaseModel):
    query: str


@app.post("/execute")
async def execute(request: QueryRequest):
    """
    Execute a natural language query through the Aegis runtime.
    Returns status, result, trace_id, tool, operation, duration.
    """
    with tracer.start_as_current_span("http.execute") as span:
        span.set_attribute("query", request.query)
        trace_id = format(span.get_span_context().trace_id, "032x")

        result = process_query(request.query, brain, validator, executor)

        return {
            "status": result.final_status,
            "tool": result.tool,
            "operation": result.operation,
            "duration_ms": result.duration_ms,
            "trace_id": trace_id,
            "result": result.model_dump() if hasattr(result, "model_dump") else None,
        }


@app.get("/health")
async def health():
    return {"status": "ok"}