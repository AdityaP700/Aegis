Aegis is a reliability runtime for LLM tool-calling agents that validates model-generated execution plans, prevents unsupported operations, detects malformed or implausible results, tracks execution behavior, and applies recovery strategies when execution fails.

Model Comparison for Brain Routing:
| Model | Correct Tool Selection | Avg Confidence | Usable? |
|-------|----------------------|----------------|---------|
| llama-3.3-70b-versatile | High | 0.9 | ✅ Yes |
| openai/gpt-oss-20b | Medium | 0.5-0.9 | ⚠️ Partial |
| qwen-3.6-27b | None | 0.1 | ❌ No |

## Known Bugs Fixed

### Bug: Failure Classifier Returned "capability_mismatch" After Successful Recovery
**Symptom:** Capability test cases failed grading even though the system recovered successfully.
**Root Cause:** The classifier checked trace events in order and returned "capability_mismatch" as soon as it saw a rejection event — without checking if the system later recovered.
**Fix:** Moved `final_status == "success"` check to the top of the classifier.
**Lesson:** The final outcome is the source of truth. Intermediate events like `capability_rejected` are signals, not verdicts.

## result
It wraps any LLM router with 9 pre-execution checks, 3 post-execution checks, and intelligent recovery. In evaluation across 22 test cases, the baseline agent (no safety net) achieved 20% success with multiple silent failures. Aegis improved success to 50% with zero silent failures and zero crashes. The evaluation harness includes a deterministic grader, failure classifier, latency tracking, and side-by-side comparison."

## stoichastic results
In a 5-task stochastic evaluation repeated across 5 trials (25 total trials), Aegis achieved 100% Pass@5 and 80% Pass^5, compared with 0% for an unguarded baseline.

Aegis succeeded in 24/25 trials; the single failure was caused by an upstream LLM-provider rate limit and was classified separately as an external dependency failure.

Results are from a targeted 5-task reliability suite; the broader 22-task benchmark is reported separately.

Evaluated against an unprotected baseline using Pass@K/Pass^K, improving Pass@5 from 0% to 100% while eliminating silent failures. Deployed as a FastAPI service with Jaeger-based execution tracing