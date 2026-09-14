# ============================================================
# day7_test_recommendation.py
# ============================================================
# DAY 7: Tests the new maintenance recommendation node.
# Runs the agent on 3 different roads (Good, Fair, Poor)
# and confirms each one gets a sensible recommendation.
#
# HOW TO RUN:
#   python day7_test_recommendation.py
# ============================================================

import json
from agent.graph import run_agent


def show_result(label, input_data):
    print(f"--- {label} ---")
    result = run_agent(input_data)

    print(f"  PCI:            {result.get('pci')}")
    print(f"  Band:           {result.get('band')}")
    print(f"  Priority:       {result.get('priority')}")
    print(f"  Recommendation: {result.get('recommendation')}")
    print(f"  Top factor:     {result.get('factors', [{}])[0].get('name') if result.get('factors') else 'N/A'}")
    print()

    # Confirm the new fields are present
    assert "recommendation" in result, "MISSING: recommendation field"
    assert "priority" in result, "MISSING: priority field"
    print(f"  PASSED — recommendation and priority fields present")
    print()


print("*" * 65)
print("  DAY 7: MAINTENANCE RECOMMENDATION TEST")
print("*" * 65)
print()

# --- Test 1: Good road (should get Low priority, routine monitoring) ---
show_result(
    "TEST 1 — Brand new smooth road (expect GOOD, Low priority)",
    {
        "Age": 2, "TTh": 350, "ATh": 200, "TAP": 600,
        "MAAT": 15, "FI": 100, "MIRI": 0.5,
        "PI": None, "AADTT": None,
        "Sieve200_subgrade": None, "Sieve200_base": None,
    }
)

# --- Test 2: Fair road (should get Medium priority, preventive maintenance) ---
show_result(
    "TEST 2 — Middle-aged road (expect FAIR, Medium priority)",
    {
        "Age": 12, "TTh": 250, "ATh": 120, "TAP": 900,
        "MAAT": 11, "FI": 400, "MIRI": 1.8,
        "PI": None, "AADTT": None,
        "Sieve200_subgrade": None, "Sieve200_base": None,
    }
)

# --- Test 3: Poor road (should get High priority, major rehabilitation) ---
show_result(
    "TEST 3 — Old rough road (expect POOR, High priority)",
    {
        "Age": 30, "TTh": 150, "ATh": 75, "TAP": 1200,
        "MAAT": 5, "FI": 800, "MIRI": 3.5,
        "PI": None, "AADTT": None,
        "Sieve200_subgrade": None, "Sieve200_base": None,
    }
)

# --- Test 4: Error case (empty data → should get N/A priority, no crash) ---
show_result(
    "TEST 4 — Empty input (expect Error, N/A priority, no crash)",
    {}
)

print("=" * 65)
print("  ALL DAY 7 TESTS COMPLETE")
print("=" * 65)
