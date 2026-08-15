Your thinking is crystal clear and I agree completely. Here's my assessment.

---

## The Key Insight

You've identified that "completeness" is actually **two different problems** at two different layers:

| Failure | Layer | Example |
|---------|-------|---------|
| Brain drops an entity | **Pre-execution** (planning) | User asks Delhi + Tokyo, Brain extracts only Delhi |
| Tool drops an entity | **Post-execution** (execution) | Plan asks Delhi + Tokyo, tool returns only Delhi |

Mixing these would make the architecture muddy. You're right to separate them.

---

## The Principle

> **The plan is the execution contract. Post-execution checks compare against the plan, not the raw user query.**

This means:

- If Brain produced a bad plan → that's a **planning failure**, caught pre-execution
- If Tool didn't fulfill a valid plan → that's an **execution completeness failure**, caught post-execution

Don't make downstream components responsible for upstream mistakes.

---

## The Clean Failure Taxonomy This Creates

| Failure | Where Detected | What It Means |
|---------|---------------|---------------|
| User asks Delhi + Tokyo, Brain extracts Delhi | Pre-execution | Planning/argument extraction failure |
| Plan says Delhi + Tokyo, tool returns Delhi | Post-execution | Execution completeness failure |
| Tool returns malformed object | Post-execution | Integrity failure |
| Tool returns temperature 9999°C | Post-execution | Plausibility failure |
| Plan asks historical, tool supports current only | Pre-execution | Capability mismatch |
| API returns 500 | Execution | Operational failure (retry) |

---

## What I'd Implement Now

For this sprint, only **execution_completeness** — compare result against plan:

```text
Post-execution checks:
    ├── integrity        ← Pydantic schema per tool
    ├── plausibility     ← Deterministic bounds per tool
    └── completeness     ← Compare plan.arguments vs response
```

`plan_completeness` (checking if Brain captured all user requirements) comes later, when evaluation data shows it's a frequent failure mode.

---

## One Line Summary

> Post-execution completeness answers: "Did the tool fulfill the plan?" — not "Did the plan fulfill the user?" That's the clean boundary.

Pre-execution catches "should I allow this plan?"
Post-execution catches "did it actually work?"

The pre-validator is too optimistic — it's letting plans through that should have been rejected.

### Create eval/cases.json
We'll convert the existing 22 test queries into evaluation cases with the following fields:

Field	Description
id	Unique identifier
category	Test category (CAPABILITY, ROUTING, etc.)
query	User input
expected	Object with behavioral expectations
The expected object will contain only the invariants we care about, like:

expected_tool (optional) – which tool should be chosen (if determinable)

expected_operation (optional) – which operation should be attempted

capability_rejected (bool) – should Aegis detect unsupported capability?

fallback_triggered (bool) – should Aegis fall back to search?

final_status (string) – "success", "failed", "unknown"

post_validation_passed (bool, optional) – if execution occurs, should post-checks pass?

User Query
   ↓
[ROUTING]        → Does the Brain pick the RIGHT TOOL?
   ↓
[ARGUMENTS]      → Does the Brain extract the RIGHT VALUES?
   ↓
[CAPABILITY]     → Does the tool SUPPORT the requested operation?
   ↓
[PLAUSIBILITY]   → Are the values BELIEVABLE?
   ↓
[DEGRADATION]    → What happens with GARBAGE input?
   ↓
[EDGE]           → Can the system handle WEIRD/ATTACK input?

Phase 2: Write a simple loader in eval/loader.py to read this JSON.

Phase 3: Enhance pipeline.py to emit trace markers like validation_failed, fallback_to_search, etc., so the grader can read them.

Phase 4: Build eval/runner.py to run each case and capture final response + trace.

Phase 5: Build eval/grader.py to compare actual behavior against expected.

Phase 6: Build eval/metrics.py to aggregate results.

Implementing the pass^k now
