"""Classifies failure reasons from TrialResult trace events."""
from typing import Optional


def classify_failure(result) -> str:
    """
    Determine the failure reason from trace events.
    """
    trace = result.trace

    # Check capability rejection first (most specific)
    for event in trace:
        if event.get("event") == "capability_rejected":
            return "capability_mismatch"

    # Check low confidence abstention
    for event in trace:
        if event.get("event") == "abstained_low_confidence":
            return "low_confidence"

    # Check execution failures
    for event in trace:
        if event.get("event") == "execution_failed":
            error_msg = event.get("error_message", "").lower()

            if "required" in error_msg:
                return "missing_argument"
            elif "not found" in error_msg:
                return "invalid_value"
            elif "rate limit" in error_msg or "timeout" in error_msg:
                return "transient_error"
            elif "invalid" in error_msg or "format" in error_msg:
                return "invalid_format"
            else:
                return "execution_error"

    # Check validation failures (non-capability)
    for event in trace:
        if event.get("event") == "validation_failed":
            errors = event.get("errors", [])
            if any("Missing required" in e for e in errors):
                return "missing_argument"
            elif any("too short" in e for e in errors):
                return "invalid_format"
            elif any("Confidence too low" in e for e in errors):
                return "low_confidence"
            else:
                return "validation_error"

    # Check fallback
    for event in trace:
        if event.get("event") == "fallback_to_search":
            return "recovered_via_fallback"

    # Check success
    if result.final_status == "success":
        return "none"

    if result.final_status == "needs_clarification":
        return "needs_clarification"

    if result.final_status == "failed":
        return "failed"

    if result.final_status == "crash":
        return "crash"

    return "unknown"