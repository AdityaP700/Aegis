"""Aegis Evaluation Harness."""
from evals.loader import load_cases, EvalCase
from evals.runner import run_cases, run_single_case, TrialOutcome
from evals.grader import grade_trial, grade_all, GradeResult
from evals.classifier import classify_failure
from evals.metrics import build_report ,print_report ,save_report ,EvalReport
from evals.baseline_runner import run_baseline_query, run_baseline_cases
from evals.compare import run_comparison, print_comparison_table, save_comparison
from evals.passk_runner import run_passk,print_passk_results,compare_passk
__all__ = [
    "load_cases",
    "EvalCase",
    "filter_by_category",
    "get_case_by_id",
    "run_cases",
    "run_single_case",
    "TrialOutcome",
    "grade_trial",
    "grade_all",
    "GradeResult",
    "classify_failure",
    "build_report",
    "print_report",
    "save_report",
    "EvalReport",
    "run_baseline_query",
    "run_baseline_cases",
    "run_comparison",
    "print_comparison_table",
    "save_comparison",
    "run_passk",
    "print_passk_results",
    "compare_passk"
    ]