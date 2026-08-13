from evals.loader import load_cases

cases = load_cases()
print(f"Loaded {len(cases)} cases")

# Show first 3
for case in cases[:3]:
    print(f"\nID: {case.id}")
    print(f"  Category: {case.category}")
    print(f"  Query: {case.query}")
    print(f"  Expected: {case.expected}")