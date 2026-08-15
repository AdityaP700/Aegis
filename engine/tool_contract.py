"""Tool Contract — the rulebook every tool must declare."""
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class ToolContract:
    """Self-contained specification for a tool."""

    name: str                                    # Unique identifier
    description: str                             # What the tool does
    supported_operations: List[str]              # Operations this tool can perform
    required_args: List[str] = field(default_factory=list)  # Args that MUST be present
    optional_args: List[str] = field(default_factory=list)  # Args that MAY be present
    argument_types: Dict[str, Any] = field(default_factory=dict)  # Expected type per arg
    output_schema: Dict[str, Any] = field(default_factory=dict)   # Expected output structure
    retry_policy: str = "none"                   # "none", "exponential", "fixed"
    timeout_seconds: float = 10.0                # Max execution time
    capabilities: List[str] = field(default_factory=list)  # High-level capabilities

    def validate_arguments(self, arguments: Dict[str, Any]) -> List[str]:
        """
        Validate arguments against this contract.
        Returns list of error messages (empty = valid).
        """
        errors = []

        # Check required args
        for arg in self.required_args:
            if arg not in arguments or not arguments[arg]:
                errors.append(f"Missing required argument: '{arg}'")

        # Check argument types
        for arg_name, expected_type in self.argument_types.items():
            if arg_name in arguments and arguments[arg_name]:
                value = arguments[arg_name]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Argument '{arg_name}' must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

        return errors
# Operations = specific actions
    def supports_operation(self, operation: str) -> bool:
        """Check if this tool supports the given operation."""
        return operation in self.supported_operations
# Capabilities = high-level abilities
    def supports_capability(self, capability: str) -> bool:
        """Check if this tool supports the given capability."""
        return capability in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for prompt building."""
        return {
            "name": self.name,
            "description": self.description,
            "supported_operations": self.supported_operations,
            "capabilities": self.capabilities,
            "required_args": self.required_args,
            "optional_args": self.optional_args
        }