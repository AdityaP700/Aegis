"""Runs evaluation cases through the Aegis pipeline."""
import time
from typing import List, Dict, Any
from evals.loader import EvalCase
from evals.loader import get_case_by_id
from pipeline import process_query

class TrialOutcome:
    """One trial's result — combines test case with Aegis outcome."""

    def __init__(self, case: EvalCase, result):
        self.case = case
        self.result = result  # TrialResult from pipeline

    @property
    def query(self) -> str:
        return self.case.query

    @property
    def category(self) -> str:
        return self.case.category

    @property
    def expected(self) -> Dict[str, Any]:
        return self.case.expected

    def __repr__(self):
        return f"TrialOutcome(case='{self.case.id}', status='{self.result.final_status}')"


def run_cases(cases: List[EvalCase], brain, validator, executor,
              delay_between_calls: float = 3.0) -> List[TrialOutcome]:
    """
    Run all cases through Aegis pipeline.

    Args:
        cases: List of EvalCase objects
        brain: Brain instance
        validator: Validator instance
        executor: Executor instance
        delay_between_calls: Seconds to wait between cases (rate limit protection)

    Returns:
        List of TrialOutcome objects
    """
    outcomes = []

    print(f"\n{'=' * 80}")
    print(f"RUNNING {len(cases)} EVALUATION CASES")
    print(f"{'=' * 80}")

    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case.id}")

        try:
            # Import here to avoid circular dependency
            from pipeline import process_query

            result = process_query(case.query, brain, validator, executor)
            outcome = TrialOutcome(case, result)
            outcomes.append(outcome)

        except Exception as e:
            # If pipeline crashes, record as failed trial
            from engine.types import TrialResult
            crash_result = TrialResult(
                query=case.query,
                final_status="crash",
                trace=[{
                    "component": "runner",
                    "event": "exception",
                    "error": str(e)
                }]
            )
            outcome = TrialOutcome(case, crash_result)
            outcomes.append(outcome)
            print(f"   💥 CRASHED: {e}")

        # Rate limit protection
        if i < len(cases):
            time.sleep(delay_between_calls)

    return outcomes


def run_single_case(case_id: str, cases: List[EvalCase], brain, validator, executor) -> TrialOutcome:
    """
    Run a single case by ID. Useful for debugging.

    Args:
        case_id: ID of case to run
        cases: All loaded cases
        brain, validator, executor: Aegis components

    Returns:
        Single TrialOutcome
    """

    case = get_case_by_id(cases, case_id)

    result = process_query(case.query, brain, validator, executor)

    return TrialOutcome(case, result)