The Fix: Use user_query for Graceful Degradation
python
def parse(self, raw_text: str, user_query: str = "") -> ExecutionPlan:
    cleaned = self._clean_response(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: If we have the original query, search it
        if user_query:
            return ExecutionPlan(
                intent="fallback search (parse failed)",
                tool="search",
                arguments={"query": user_query},
                confidence=0.1,
                validation_status="pending",
                validation_errors=[f"Failed to parse LLM response, falling back to search"]
            )
        else:
            # No query to fall back on — truly unknown
            return ExecutionPlan(
                intent="parsing failed",
                tool="unknown",
                arguments={},
                confidence=0.0,
                validation_status="failed",
                validation_errors=[f"Failed to parse LLM response: {raw_text[:100]}"]
            )

    # Build ExecutionPlan from valid JSON
    return ExecutionPlan(
        intent=data.get("intent", "unknown"),
        tool=data.get("tool", "unknown"),
        arguments=data.get("arguments", {}),
        confidence=data.get("confidence", 0.5),
        validation_status="pending"
    )
