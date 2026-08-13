"""Deterministic grader — compares TrialOutcome against expected behavior."""
from typing import Dict, Any, List
from evals.runner import TrialOutcome


class GradeResult:
    """Result of grading one trial."""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.passed = True
        self.checks: List[Dict[str, Any]] = []

    def add_check(self, name: str, expected: Any, actual: Any, passed: bool):
        """Record one check result."""
        self.checks.append({
            "check": name,
            "expected": expected,
            "actual": actual,
            "passed": passed
        })
        if not passed:
            self.passed = False

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"GradeResult(case='{self.case_id}', status='{status}')"


def grade_trial(outcome: TrialOutcome) -> GradeResult:
    """
    Grade one trial by checking behavioral invariants.

    Args:
        outcome: TrialOutcome from runner

    Returns:
        GradeResult with pass/fail and individual checks
    """
    case = outcome.case
    result = outcome.result
    expected = case.expected

    grade = GradeResult(case.id)

    # Check 1: Final status
    if "final_status" in expected:
        expected_status = expected["final_status"]
        actual_status = result.final_status
        grade.add_check(
            "final_status",
            expected_status,
            actual_status,
            actual_status == expected_status
        )

    # Check 2: Tool used
    if "expected_tool" in expected:
        expected_tool = expected["expected_tool"]
        actual_tool = result.tool
        grade.add_check(
            "tool",
            expected_tool,
            actual_tool,
            actual_tool == expected_tool
        )

    # Check 3: Operation
    if "expected_operation" in expected:
        expected_op = expected["expected_operation"]
        actual_op = result.operation
        grade.add_check(
            "operation",
            expected_op,
            actual_op,
            actual_op == expected_op
        )

    # Check 4: Capability rejected
    if "capability_rejected" in expected:
        expected_rejected = expected["capability_rejected"]
        actual_rejected = result.capability_rejected
        grade.add_check(
            "capability_rejected",
            expected_rejected,
            actual_rejected,
            actual_rejected == expected_rejected
        )

    # Check 5: Fallback triggered
    if "fallback_triggered" in expected:
        expected_fallback = expected["fallback_triggered"]
        actual_fallback = result.fallback_triggered
        grade.add_check(
            "fallback_triggered",
            expected_fallback,
            actual_fallback,
            actual_fallback == expected_fallback
        )

    # Check 6: Post-validation passed
    if "post_validation_passed" in expected:
        expected_post = expected["post_validation_passed"]
        actual_post = result.post_validation_passed
        grade.add_check(
            "post_validation_passed",
            expected_post,
            actual_post,
            actual_post == expected_post
        )

    return grade


def grade_all(outcomes: List[TrialOutcome]) -> List[GradeResult]:
    """
    Grade all trial outcomes.

    Args:
        outcomes: List of TrialOutcome objects

    Returns:
        List of GradeResult objects
    """
    grades = []
    for outcome in outcomes:
        grade = grade_trial(outcome)
        grades.append(grade)
    return grades


def print_grades(grades: List[GradeResult]):
    """Pretty-print grading results."""
    print(f"\n{'=' * 80}")
    print(f"GRADING RESULTS")
    print(f"{'=' * 80}")

    for grade in grades:
        icon = "✅" if grade.passed else "❌"
        print(f"\n{icon} {grade.case_id}")

        for check in grade.checks:
            check_icon = "✓" if check["passed"] else "✗"
            print(f"   {check_icon} {check['check']}: "
                  f"expected={check['expected']}, actual={check['actual']}")