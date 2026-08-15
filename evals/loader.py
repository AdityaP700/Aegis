"""Loads evaluation cases from JSON into Python objects."""
import json
from pathlib import Path
from typing import Dict, List, Any


class EvalCase:
    """Single evaluation test case."""

    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.category = data.get("category", "GENERAL")
        self.query = data.get("query", "")
        self.expected = data.get("expected", {})

    def __repr__(self):
        return f"EvalCase(id='{self.id}', category='{self.category}')"

#list of dicts -> list of EvalCase objects
def load_cases(filepath: str = None) -> List[EvalCase]:
    """
    Load evaluation cases from JSON file.

    Args:
        filepath: Path to cases.json. Defaults to 'eval/cases.json'

    Returns:
        List of EvalCase objects
    """
    if filepath is None:
        filepath = Path(__file__).parent / "cases.json"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Cases file not found: {filepath}")

    with open(filepath, "r") as f:
        #here its declared json
        data = json.load(f)

    return [EvalCase(case) for case in data]

def filter_by_category(cases: List[EvalCase], category: str) -> List[EvalCase]:
    """Filter cases by category."""
    return [c for c in cases if c.category == category]


def get_case_by_id(cases: List[EvalCase], case_id: str) -> EvalCase:
    """Get a single case by its ID."""
    for case in cases:
        if case.id == case_id:
            return case
    raise ValueError(f"Case with id '{case_id}' not found")

def load_cases_from_file(filepath: str) -> List[EvalCase]:
    """Load cases from a specific JSON file."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Cases file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    return [EvalCase(case) for case in data]