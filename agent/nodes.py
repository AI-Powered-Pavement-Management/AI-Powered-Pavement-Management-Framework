# ============================================================
# agent/nodes.py — DAY 7 UPDATE
# ============================================================
# DAY 7 CHANGES:
#   - Added a NEW node: recommend_maintenance
#   - This is the "Human Oversight" input from the architecture
#   - It reads the PCI band and generates a plain-language
#     maintenance recommendation that a human engineer reviews.
#
# Nodes in this file (5 total, was 4):
#   1. validate_input          — The Security Guard
#   2. predict_pci             — The Calculator
#   3. explain_pci             — The Detective
#   4. check_output            — The Quality Inspector (+ retry loop)
#   5. recommend_maintenance   — The Advisor              [NEW - Day 7]
# ============================================================

import numpy as np
import pandas as pd
import pickle
import shap
import os

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "model",
    "model.pkl"
)

FIELD_MAP = {
    "Age":                "Age",
    "TTh":                "TTh",
    "ATh":                "ATh",
    "TAP":                "TAP",
    "MAAT":               "MAAT",
    "FI":                 "FI",
    "MIRI":               "MIRI",
    "PI":                 "PI",
    "AADTT":              "AADTT",
    "Sieve200_subgrade":  "pass Sieve 200 subgrade",
    "Sieve200_base":      "pass Sieve 200 base_subbase",
}


# ============================================================
# NODE 1: validate_input — THE SECURITY GUARD
# ============================================================

def validate_input(state):
    raw = state.get("input_data", {})

    if not raw:
        return {
            **state,
            "is_valid": False,
            "error": "No input data provided"
        }

    translated = {}
    for web_key, model_col in FIELD_MAP.items():
        val = raw.get(web_key)
        if val is None or val == "":
            translated[model_col] = np.nan
        else:
            try:
                translated[model_col] = float(val)
            except (ValueError, TypeError):
                translated[model_col] = np.nan

    return {
        **state,
        "input_data_translated": translated,
        "is_valid": True,
        "error": None
    }


# ============================================================
# NODE 2: predict_pci — THE CALCULATOR
# ============================================================

def predict_pci(state):
    try:
        with open(MODEL_PATH, "rb") as f:
            saved = pickle.load(f)

        if isinstance(saved, dict):
            model = saved["model"]
            columns = saved["columns"]
        else:
            model = saved
            columns = model.get_booster().feature_names

        translated = state["input_data_translated"]

        row = {}
        for col in columns:
            row[col] = translated.get(col, np.nan)

        df = pd.DataFrame([row], columns=columns)

        pci_raw = model.predict(df)[0]
        pci = float(np.clip(pci_raw, 0, 100))

        return {
            **state,
            "pci": round(pci, 1),
            "model_columns": columns,
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "pci": None,
            "error": f"Prediction failed: {str(e)}"
        }


# ============================================================
# NODE 3: explain_pci — THE DETECTIVE
# ============================================================

def explain_pci(state):
    try:
        with open(MODEL_PATH, "rb") as f:
            saved = pickle.load(f)

        if isinstance(saved, dict):
            model = saved["model"]
            columns = saved["columns"]
        else:
            model = saved
            columns = model.get_booster().feature_names

        translated = state["input_data_translated"]

        row = {}
        for col in columns:
            row[col] = translated.get(col, np.nan)

        df = pd.DataFrame([row], columns=columns)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df)
        vals = shap_values[0]

        pairs = list(zip(columns, vals))
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        top = pairs[:5]

        factors = [
            {"name": name, "value": round(float(v), 2)}
            for name, v in top
        ]

        return {
            **state,
            "factors": factors,
            "error": None
        }

    except Exception as e:
        return {
            **state,
            "factors": [],
            "error": f"Explanation failed: {str(e)}"
        }


MAX_RETRIES = 2


# ============================================================
# NODE 4: check_output — THE QUALITY INSPECTOR + FEEDBACK LOOP
# ============================================================

def check_output(state):
    pci = state.get("pci")
    factors = state.get("factors", [])
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    if pci is None:
        if retry_count < MAX_RETRIES:
            print(f"  [Feedback] Prediction failed. Retry {retry_count + 1}/{MAX_RETRIES}...")
            return {
                **state,
                "is_valid": False,
                "needs_retry": True,
                "retry_count": retry_count + 1,
                "error": error or "Prediction failed, retrying..."
            }
        else:
            print(f"  [Feedback] Prediction failed after {MAX_RETRIES} retries. Giving up.")
            return {
                **state,
                "is_valid": False,
                "needs_retry": False,
                "response": {
                    "pci": None,
                    "band": "Error",
                    "factors": [],
                    "note": f"Prediction failed after {MAX_RETRIES} retries: {error}"
                }
            }

    if pci < 0 or pci > 100:
        if retry_count < MAX_RETRIES:
            print(f"  [Feedback] PCI {pci} out of range. Retry {retry_count + 1}/{MAX_RETRIES}...")
            return {
                **state,
                "is_valid": False,
                "needs_retry": True,
                "retry_count": retry_count + 1,
                "error": f"PCI {pci} outside 0-100, retrying..."
            }
        else:
            print(f"  [Feedback] PCI {pci} still out of range after {MAX_RETRIES} retries.")
            return {
                **state,
                "is_valid": False,
                "needs_retry": False,
                "response": {
                    "pci": pci,
                    "band": "Error",
                    "factors": factors,
                    "note": f"PCI {pci} outside valid range after {MAX_RETRIES} retries"
                }
            }

    if pci >= 70:
        band = "Good"
    elif pci >= 40:
        band = "Fair"
    else:
        band = "Poor"

    retry_note = f" (after {retry_count} retries)" if retry_count > 0 else ""
    return {
        **state,
        "is_valid": True,
        "needs_retry": False,
        "response": {
            "pci": pci,
            "band": band,
            "factors": factors,
            "note": f"Predicted by XGBoost + SHAP via LangGraph agent{retry_note}"
        }
    }


# ============================================================
# NODE 5: recommend_maintenance — THE ADVISOR       [NEW - DAY 7]
# ============================================================
# This node runs AFTER check_output succeeds. It reads the PCI
# band and generates a plain-language maintenance recommendation
# that a human engineer will review (Approve / Reject).
#
# This is the "Human Oversight" input from the architecture
# diagram (Image 2, bottom box of the review paper).
#
# Simple rule-based logic for the prototype:
#   Poor (<40)   → Major rehabilitation
#   Fair (40-69) → Preventive maintenance
#   Good (70+)   → Routine monitoring
#
# We also mention the top SHAP factor to make the recommendation
# specific to THIS road, not just a generic band-based message.
# ============================================================

def recommend_maintenance(state):
    """
    Adds a plain-language maintenance recommendation to the response
    based on the predicted PCI band and the top contributing factor.

    Reads from state:
      - state["response"]["pci"]
      - state["response"]["band"]
      - state["response"]["factors"]

    Writes back to state:
      - state["response"]["recommendation"]  (string)
      - state["response"]["priority"]        (string: High/Medium/Low)
    """

    response = state.get("response", {})

    # Safety: if check_output already returned an error response,
    # don't try to make a recommendation — just pass through cleanly.
    if response.get("pci") is None or response.get("band") == "Error":
        response["recommendation"] = "No recommendation available — prediction was invalid."
        response["priority"] = "N/A"
        return {**state, "response": response}

    band = response.get("band")
    factors = response.get("factors", [])

    # ---- Band-based recommendation ----
    if band == "Good":
        action = (
            "Routine monitoring only. Continue scheduled inspections. "
            "No immediate maintenance action is required."
        )
        priority = "Low"
    elif band == "Fair":
        action = (
            "Preventive maintenance recommended. Consider crack sealing, "
            "surface treatment (chip seal or slurry seal), or minor patching "
            "to extend service life before the section deteriorates further."
        )
        priority = "Medium"
    else:  # Poor
        action = (
            "Major rehabilitation required. A structural overlay, "
            "mill-and-overlay, or full reconstruction should be evaluated "
            "and prioritised as soon as budget permits."
        )
        priority = "High"

    # ---- Factor-aware detail (makes recommendation specific to THIS road) ----
    detail = ""
    if factors:
        top_name = factors[0]["name"]
        top_value = factors[0]["value"]
        direction = "worsening" if top_value < 0 else "supporting"
        detail = f" Primary driver: {top_name} (currently {direction} the condition)."

    response["recommendation"] = action + detail
    response["priority"] = priority

    return {**state, "response": response}
