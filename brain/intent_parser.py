import json
from engine.types import ExecutionPlan

class IntentParser:
    """
    Parses raw LLM output into a typed ExecutionPlan.
    Handles messy LLM responses (markdown, bad JSON, etc.).
    """

    def parse(self, raw_text: str, user_query: str = "") -> ExecutionPlan:
        """
        Parse raw LLM text into ExecutionPlan.

        Args:
            raw_text: Raw output from LLM
            user_query: Original user query (for fallback)

        Returns:
            ExecutionPlan object
        """
        # Clean up the response
        cleaned = self._clean_response(raw_text)

        # Try to parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: return unknown plan
            return ExecutionPlan(
                intent="parsing failed",
                tool="unknown",
                arguments={},
                confidence=0.0,
                validation_status="failed",
                validation_errors=[f"Failed to parse LLM response: {raw_text[:100]}"]
            )

        # Build ExecutionPlan
        return ExecutionPlan(
            intent=data.get("intent", "unknown"),
            tool=data.get("tool", "unknown"),
            arguments=data.get("arguments", {}),
            confidence=data.get("confidence", 0.5),
            validation_status="pending"
        )

    def _clean_response(self, raw_text: str) -> str:
        """Clean LLM response (remove markdown, etc.)."""
        text = raw_text.strip()

        # Remove markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        return text.strip()