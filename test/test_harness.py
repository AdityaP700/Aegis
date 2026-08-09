test_cases = [
    {
        "query": "Weather in Delhi yesterday",
        "expected_tool": "weather",
        "expected_failure": "capability_mismatch",  # historical vs current
        "should_execute": False
    },
    {
        "query": "Weather in Delhi",
        "expected_tool": "weather",
        "expected_failure": None,
        "should_execute": True,
        "expected_invariants_pass": True
    },
    {
        "query": "Weather in Delhi and Tokyo",
        "expected_tool": "weather",
        "expected_failure": "completeness",  # Only one city returned
        "should_execute": True
    }
]