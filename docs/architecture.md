# Aegis — Architecture

## Overview

Aegis is a reliability-oriented execution runtime for LLM-powered tool-calling agents. It separates intent planning, validation, and execution into distinct layers with defense-in-depth error handling.


## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Brain-Validator-Executor separation | Each layer has one responsibility; swappable independently |
| Pre-execution capability check | Catches mismatches before wasting API calls |
| Validation error → LLM retry | Gives the Brain one chance to self-correct |
| Graceful degradation to search | An imperfect answer beats no answer |
| Provider-agnostic Brain | Swap Groq for Gemini/Claude without touching pipeline |
| Structured tracing | Every execution produces component-level event trace |

## Failure Modes Handled

| Failure | Layer | Behavior |
|---------|-------|----------|
| LLM returns malformed JSON | Intent Parser | Fallback to search |
| LLM chooses nonexistent tool | Validator | Reject + retry |
| Missing required argument | Validator | Reject + retry |
| Wrong argument type | Validator | Reject + retry |
| Tool-intent mismatch | Validator (plausibility) | Reject + retry |
| Capability mismatch | Validator (capability) | Reject + retry |
| Low confidence | Validator | Reject + retry |
| API timeout | Executor | Retry with backoff |
| API rate limit | Executor | Retry with backoff |
| All retries exhausted | Pipeline | Graceful degradation to search |


Aegis Reliability Runtime
├── Pre-execution checks (7 layers)
│   ├── Confidence gate (≥ 0.3)
│   ├── Tool existence
│   ├── Operation support
│   ├── Capability match
│   ├── Required arguments
│   ├── Argument contract (multi-city, repo format)
│   └── Argument types + plausibility
├── Execution layer
│   ├── Retry with backoff
│   └── Timeout handling
├── Post-execution checks (3 layers)
│   ├── Integrity (structural validity)
│   ├── Plausibility (value bounds)
│   └── Completeness (plan vs result)
└── Graceful degradation
    └── Failed plans → search fallback


Evaluation Layer
Create eval/cases.json
Convert existing 22 tests into structured cases with expected behaviors.

Enhance trace markers
In pipeline.py, add events like validation_failed, fallback_to_search, recovery_attempted.

Build eval/grader.py
Deterministic checks based on final response + trace markers.

Build eval/runner.py
Loop over cases, call pipeline.process_query, capture TrialResult.

Build eval/metrics.py
Aggregate pass rate, category breakdown, recovery rate, etc.

Run and produce first evaluation report
This becomes your README's "Failure Modes & Recovery" table.

Later: baseline comparison
Add pipeline.run_baseline() and run same cases, same grader.

The system now distinguishes:
✅ Clear intent → execute → post-check
❌ Missing argument → ask user
❌ Invalid format → ask user
❌ Unsupported capability → fallback to search