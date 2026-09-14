# ============================================================
# day4_test_agent.py — Tests the full LangGraph agent
# Run: python day4_test_agent.py
# ============================================================

import json
from agent.graph import run_agent

print("=" * 60)
print("  DAY 4 TEST: Running the LangGraph Agent")
print("=" * 60)

# Sample input data (like Student B's web form would send)
sample_input = {
    "Age":                12,
    "TTh":                300,
    "ATh":                150,
    "TAP":                800,
    "MAAT":               11,
    "FI":                 300,
    "MIRI":               1.2,
    "PI":                 None,     # missing on purpose
    "AADTT":              None,     # missing on purpose
    "Sieve200_subgrade":  None,     # missing on purpose
    "Sieve200_base":      None,     # missing on purpose
}

print("\nINPUT DATA:")
print("-" * 40)
for key, value in sample_input.items():
    status = "provided" if value is not None else "MISSING"
    print(f"  {key:25s} = {str(value):10s}  ({status})")

print("\nRunning agent...\n")

result = run_agent(sample_input)

print("RESULT:")
print("-" * 40)
print(json.dumps(result, indent=2))

print("\nQUICK CHECKS:")
print("-" * 40)

pci = result.get("pci")
if pci is not None:
    print(f"  PCI:     {pci}")
    print(f"  Band:    {result.get('band')}")
    print(f"  Factors: {len(result.get('factors', []))}")
    for f in result.get("factors", []):
        arrow = "DOWN" if f["value"] < 0 else "UP"
        print(f"    {f['name']:25s} {f['value']:+.2f}  (pushing PCI {arrow})")
    print(f"\n  TEST PASSED!")
else:
    print(f"  ERROR: {result.get('note')}")

print("=" * 60)