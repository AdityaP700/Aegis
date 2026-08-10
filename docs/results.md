### As of now what the latest execution is doing
Layer 1 (Pre-execution): 8 failures caught
  - 4 CAPABILITY mismatches (historical_weather, forecast, get_readme, get_commits)
  - 2 DEGRADATION (gibberish/empty → unknown)
  - 2 EDGE cases

Layer 2 (Post-execution): 6 failures caught
  - Missing/invalid arguments that slipped past pre-check
  - API failures that returned errors
  - Malformed arguments that the API rejected

  Query: "weather" (no city)

  Before 
→ Pre-check: PASSES (weather tool exists, operation supported)
→ Executor: Calls API with empty city
→ API: Returns error or garbage
→ Post-check: ✗ Catches the failure

Result: Wasted API call + caught after the fact

After
Query: "weather" (no city)
→ Pre-check: ❌ Confidence 0.4 < 0.5 → ABSTAIN
→ "Could you clarify what you mean?"
→ No API call made

Result: Zero cost, immediate feedback