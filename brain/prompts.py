from typing import List, Dict, Any

class PromptBuilder:

    def __init__(self, tools_metadata: List[Dict[str, Any]]):

        self.tools_metadata = tools_metadata

    def build_system_prompt(self) -> str:
       
        tools_section = self._build_tools_section()
        examples_section = self._build_examples()

        return f"""You are an execution planner. Your ONLY job is to route user queries to the correct tool.

You MUST return valid JSON with this exact structure:
{{"intent": "what user wants", "tool": "tool_name", "arguments": {{...}}, "confidence": 0.0-1.0}}

{tools_section}

{examples_section}

CRITICAL RULES:
1. Return ONLY JSON, no explanations
2. If user's request doesn't match any tool, use "unknown" as tool
3. Extract ALL required arguments from the user's query
4. Set confidence based on how certain you are:
   - 1.0: Perfect match (e.g., "weather in Delhi" → weather tool)
   - 0.8: Good match but some ambiguity
   - 0.5: Unsure but best guess
   - 0.0: No idea (use "unknown" tool)

Now route this user query."""

    def _build_tools_section(self) -> str:
        """Build the tools description section."""
        lines = ["AVAILABLE TOOLS:"]

        for tool in self.tools_metadata:
            name = tool["name"]
            desc = tool["description"]
            required = tool.get("required_args", [])
            optional = tool.get("optional_args", [])

            lines.append(f"\n{name}:")
            lines.append(f"  Description: {desc}")
            lines.append(f"  Required arguments: {required}")
            if optional:
                lines.append(f"  Optional arguments: {optional}")

        return "\n".join(lines)

    def _build_examples(self) -> str:
        """Build few-shot examples."""
        return """EXAMPLES:

User: "What's the weather in Tokyo?"
Response: {"intent": "get weather for Tokyo", "tool": "weather", "arguments": {"city": "Tokyo"}, "confidence": 1.0}

User: "How many stars does karpathy/nanoGPT have?"
Response: {"intent": "get GitHub stats for nanoGPT", "tool": "github", "arguments": {"repo": "karpathy/nanoGPT"}, "confidence": 1.0}

User: "What is a transformer neural network?"
Response: {"intent": "search for transformer neural network", "tool": "search", "arguments": {"query": "transformer neural network"}, "confidence": 0.9}

User: "Tell me about Python"
Response: {"intent": "ambiguous request about Python", "tool": "search", "arguments": {"query": "Python programming language"}, "confidence": 0.7}

User: "asdfghjkl"
Response: {"intent": "gibberish input", "tool": "unknown", "arguments": {}, "confidence": 0.0}"""

    def build_user_prompt(self, user_query: str) -> str:
        """Build the user prompt."""
        return f"User query: {user_query}\n\nRoute this to the correct tool."

    def build_retry_prompt(self, user_query: str, previous_error: str, previous_response: str) -> str:
        """
        Build a retry prompt when previous response was invalid.

        Args:
            user_query: Original user query
            previous_error: What was wrong with the previous response
            previous_response: The previous invalid response
        """
        return f"""Your previous response was invalid.

User query: {user_query}

Your previous response: {previous_response}

Error: {previous_error}

Please fix the error and return valid JSON again."""