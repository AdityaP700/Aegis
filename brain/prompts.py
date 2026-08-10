class PromptBuilder:
    def __init__(self, tools_metadata):
        self.tools_metadata = tools_metadata
        self.rules = {
    "routing": [
        "Match user intent to the most specific tool",
        "If multiple tools could work, pick the most direct one",
        "Always output the operation the USER wants, not what the tool supports",
        "Let the validator reject unsupported operations — that's its job",
        "If a query doesn't match weather or github, use search",
        "Only return 'unknown' if the query is complete gibberish or empty"
    ],
            "argument_extraction": [
                "Extract arguments exactly as the user stated them",
    "For GitHub repositories:"
"- Preserve an explicitly stated owner/repo pair."
"- If only a repository name is provided, do not invent an owner."
"- If ownership is ambiguous, preserve the repository name and let validation/recovery handle the missing information.",
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
        #Update Prompt to Ask for Capability
        prompt += """
Return ONLY valid JSON with this exact structure:
{"intent": "what user wants", "tool": "tool_name", "operation": "specific_operation", "arguments": {...}, "requested_capability": "capability_name", "confidence": 0.0-1.0}

For 'operation', use the exact operation name from the tool's supported operations.
For 'requested_capability', use the same value as 'operation'.
If the tool is 'unknown', use empty strings for both.
"""

        return prompt

    def _build_tools_section(self) -> str:
        """Build the tools description section."""
        lines = ["AVAILABLE TOOLS (with currently supported operations):"]

        for tool in self.tools_metadata:
            name = tool["name"]
            desc = tool["description"]
            required = tool.get("required_args", [])
            operations =tool.get("supported_operations",[])
            optional = tool.get("optional_args", [])
            capabilities = tool.get("capabilities", [])
            lines.append(f"\n{name}:")
            lines.append(f"  Description: {desc}")
            lines.append(f"  Required arguments: {required}")
            lines.append(f"  Capabilities: {capabilities}")
            lines.append(f"  Supported operations: {operations}")
            if optional:
                lines.append(f"  Optional arguments: {optional}")
        lines.append("\nNOTE: If a user requests an operation not listed above, still output it.")
        lines.append("The system will handle unsupported operations gracefully.")
        return "\n".join(lines)

    def _build_examples(self) -> str:
        """Build few-shot examples."""
        return """EXAMPLES:
User: "What's the weather in Tokyo?"
Response: {"intent": "get current weather for Tokyo", "tool": "weather", "operation": "current_weather", "arguments": {"city": "Tokyo"}, "requested_capability": "current_weather", "confidence": 1.0}
User: "Is it going to be sunny?"
Response: {"intent": "check if sunny now", "tool": "weather", "operation": "current_weather", "arguments": {"city": ""}, "requested_capability": "current_weather", "confidence": 0.5},
User: "What was the weather in Delhi yesterday?"
Response: {"intent": "get historical weather for Delhi", "tool": "weather", "operation": "historical_weather", "arguments": {"city": "Delhi"}, "requested_capability": "historical_weather", "confidence": 0.9}

User: "Will it rain in Tokyo tomorrow?"
Response: {"intent": "get weather forecast for Tokyo", "tool": "weather", "operation": "weather_forecast", "arguments": {"city": "Tokyo"}, "requested_capability": "weather_forecast", "confidence": 0.9}
,
User: "How's the climate in Paris?"
Response: {"intent": "get weather for Paris", "tool": "weather", "operation": "current_weather", "arguments": {"city": "Paris"}, "requested_capability": "current_weather", "confidence": 0.9}.

User: "How many stars does karpathy/nanoGPT have?"
Response: {"intent": "get repository metadata for nanoGPT", "tool": "github", "operation": "repository_metadata", "arguments": {"repo": "karpathy/nanoGPT"}, "requested_capability": "repository_metadata", "confidence": 1.0}

User: "Show me the README of karpathy/nanoGPT"
Response: {"intent": "get README file for nanoGPT", "tool": "github", "operation": "get_readme", "arguments": {"repo": "karpathy/nanoGPT"}, "requested_capability": "get_readme", "confidence": 0.9}

User: "What's the commit history of torvalds/linux?"
Response: {"intent": "get commit history for linux", "tool": "github", "operation": "get_commits", "arguments": {"repo": "torvalds/linux"}, "requested_capability": "get_commits", "confidence": 0.9}

User: "What is a transformer neural network?"
Response: {"intent": "search for transformer neural network", "tool": "search", "operation": "web_search", "arguments": {"query": "transformer neural network"}, "requested_capability": "web_search", "confidence": 0.9}

User: "asdfghjkl"
Response: {"intent": "gibberish input", "tool": "unknown", "operation": "", "arguments": {}, "requested_capability": "", "confidence": 0.0}

IMPORTANT: Always output the operation the USER is requesting, even if the tool doesn't currently support it. The system will validate whether the operation is available. Do NOT change the operation to match what's available."""
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