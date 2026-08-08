from typing import List, Dict, Any

class PromptBuilder:
    def __init__(self, tools_metadata):
        self.tools_metadata = tools_metadata
        self.rules = {
            "routing": [
                "Match user intent to the most specific tool",
                "If multiple tools could work, pick the most direct one",
                "If no tool matches, return 'unknown'"
            ],
            "argument_extraction": [
                "Extract arguments exactly as the user stated them",
    "For GitHub repos: extract the username AFTER the last name",
    "  Example: 'andrej karpathy's repo' → owner is 'karpathy', not 'andrejkarpathy'",
    "  Example: 'repo by john smith' → owner is 'smith' or full username if given",
    "Don't infer missing arguments — leave them empty",
    "If an argument is clearly not what the tool expects, flag it"
            ],
            "confidence": [
                "1.0: Direct match (e.g., 'weather in Delhi')",
                "0.7-0.9: Implicit intent (e.g., 'is it raining?')",
                "0.4-0.6: Ambiguous (e.g., 'Delhi')",
                "0.1-0.3: Best guess, likely wrong",
                "0.0: Cannot determine"
            ]
        }

    def build_system_prompt(self) -> str:
        # Generate prompt FROM rules
        prompt = "You are an execution planner.\n\n"

        prompt += "ROUTING RULES:\n"
        for rule in self.rules["routing"]:
            prompt += f"- {rule}\n"

        prompt += "\nARGUMENT EXTRACTION RULES:\n"
        for rule in self.rules["argument_extraction"]:
            prompt += f"- {rule}\n"

        prompt += "\nCONFIDENCE GUIDE:\n"
        for rule in self.rules["confidence"]:
            prompt += f"- {rule}\n"

        prompt += "\n" + self._build_tools_section()
        prompt += "\n" + self._build_examples()
        prompt += "\nReturn ONLY JSON."

        return prompt

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