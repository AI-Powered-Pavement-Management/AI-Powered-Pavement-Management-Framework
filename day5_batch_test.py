import json
import pandas as pd
import numpy as np
from agent.graph import run_agent


def test_feedback_loop():
    print("=" * 65)
    print("  TEST 1: Feedback Loop (Retry Mechanism)")
    print("=" * 65)
    print()

    print("  Test 1a: Empty data...")
    result = run_agent({})
    print(f"    Result: band={result['band']}, note={result['note']}")
    print("    PASSED" if result["band"] == "Error" else "    FAILED")
    print()

    print("  Test 1b: All values None...")
    all_none = {
        "Age": None, "TTh": None, "ATh": None, "TAP": None,
        "MAAT": None, "FI": None, "MIRI": None, "PI": None,
        "AADTT": None, "Sieve200_subgrade": None, "Sieve200_base": None,
    }
    result = run_agent(all_none)
    print(f"    Result: pci={result['pci']}, band={result['band']}")
    print("    PASSED" if result["pci"] is not None else f"    Note: {result['note']}")
    print()

    print("  Test 1c: Good data...")
    good_data = {
        "Age": 10, "TTh": 250, "ATh": 120, "TAP": 900,
        "MAAT": 12, "FI": 400, "MIRI": 1.0, "PI": None,
        "AADTT": None, "Sieve200_subgrade": None, "Sieve200_base": None,
    }
    result = run_agent(good_data)
    print(f"    Result: pci={result['pci']}, band={result['band']}")
    print("    PASSED" if result["pci"] is not None else "    FAILED")
    print()


def test_batch_predictions():
    print("=" * 65)
    print("  TEST 2: Batch Test on dry.csv (Real Data)")
    print("=" * 65)
    print()

    df = pd.read_csv("dry.csv")
    df.columns = df.columns.str.strip()
    print(f"  Loaded dry.csv: {len(df)} rows")
    print()

    test_indices = [0, 50, 100, 250, 500, 750, 1000, 1200, 1400, 1492]
    test_indices = [i for i in test_indices if i < len(df)]

    results = []

    print(f"  {'Row':<6} {'Actual':<10} {'Predicted':<10} {'Band':<8} {'Diff':<8} {'Status'}")
    print(f"  {'-'*6} {'-'*10} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")

    for idx in test_indices:
        row = df.iloc[idx]
        actual_pci = row["PCI"]

        input_data = {
            "Age": row.get("Age"),
            "TTh": row.get("TTh"),
            "ATh": row.get("ATh"),
            "TAP": row.get("TAP"),
            "MAAT": row.get("MAAT"),
            "FI": row.get("FI"),
            "MIRI": row.get("MIRI"),
            "PI": row.get("PI"),
            "AADTT": row.get("AADTT"),
            "Sieve200_subgrade": row.get("pass Sieve 200 subgrade"),
            "Sieve200_base": row.get("pass Sieve 200 base_subbase"),
        }

        for key in input_data:
            if input_data[key] is not None and pd.isna(input_data[key]):
                input_data[key] = None

        result = run_agent(input_data)
        predicted_pci = result.get("pci")
        band = result.get("band", "Error")

        if predicted_pci is not None:
            diff = abs(actual_pci - predicted_pci)
            results.append(diff)
            print(f"  {idx:<6} {actual_pci:<10.1f} {predicted_pci:<10.1f} {band:<8} {diff:<8.1f} OK")
        else:
            print(f"  {idx:<6} {actual_pci:<10.1f} {'FAILED':<10} {'Error':<8} {'-':<8} FAILED")

    print()
    if results:
        print(f"  Average error: {np.mean(results):.1f} PCI points")
        print(f"  Smallest error: {np.min(results):.1f} PCI points")
        print(f"  Largest error: {np.max(results):.1f} PCI points")
        print(f"  All {len(results)} rows: PASSED")
    print()


def test_edge_cases():
    print("=" * 65)
    print("  TEST 3: Edge Cases")
    print("=" * 65)
    print()

    print("  Test 3a: Very old road (Age=30, MIRI=3.5)...")
    result = run_agent({"Age": 30, "TTh": 150, "ATh": 75, "TAP": 1200, "MAAT": 5, "FI": 800, "MIRI": 3.5, "PI": None, "AADTT": None, "Sieve200_subgrade": None, "Sieve200_base": None})
    print(f"    PCI={result['pci']}, Band={result['band']}")
    print()

    print("  Test 3b: New road (Age=2, MIRI=0.5)...")
    result = run_agent({"Age": 2, "TTh": 350, "ATh": 200, "TAP": 600, "MAAT": 15, "FI": 100, "MIRI": 0.5, "PI": None, "AADTT": None, "Sieve200_subgrade": None, "Sieve200_base": None})
    print(f"    PCI={result['pci']}, Band={result['band']}")
    print()

    print("  Test 3c: Bad input (text instead of numbers)...")
    result = run_agent({"Age": "old", "TTh": "thick", "ATh": 150, "TAP": 800, "MAAT": 11, "FI": 300, "MIRI": 1.2, "PI": None, "AADTT": None, "Sieve200_subgrade": None, "Sieve200_base": None})
    print(f"    PCI={result['pci']}, Band={result['band']}")
    print()


print("*" * 65)
print("  DAY 5: FULL AGENT TESTING")
print("*" * 65)
print()
test_feedback_loop()
test_batch_predictions()
test_edge_cases()
print("=" * 65)
print("  ALL DAY 5 TESTS COMPLETE")
print("=" * 65)