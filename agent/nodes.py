# ============================================================
# agent/nodes.py
# ============================================================
# This file contains the 4 "worker" functions (nodes) for our
# LangGraph agent. Each node does ONE job:
#
#   1. validate_input  — The Security Guard
#   2. predict_pci     — The Calculator
#   3. explain_pci     — The Detective
#   4. check_output    — The Quality Inspector
#
# Every node receives the "state" dictionary (the clipboard),
# does its job, and returns the updated state.
# ============================================================

import numpy as np
import pandas as pd
import pickle
import shap
import os

# ============================================================
# WHERE IS THE SAVED MODEL?
# ============================================================
# This path tells the code where to find your model.pkl file.
# It looks in a folder called "model" inside your project.
# If your model.pkl is somewhere else, change this path.
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "model",
    "model.pkl"
)

# ============================================================
# FIELD-NAME TRANSLATION DICTIONARY
# ============================================================
# Student B's web form uses short names like "Sieve200_subgrade".
# Our model expects the original CSV names like "pass Sieve 200 subgrade".
# This dictionary translates between them.
#
# Most fields have the SAME name on both sides.
# Only the last 2 (Sieve fields) are DIFFERENT.
# ============================================================

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
    "Sieve200_subgrade":  "pass Sieve 200 subgrade",       # TRANSLATED
    "Sieve200_base":      "pass Sieve 200 base_subbase",   # TRANSLATED
}


# ============================================================
# NODE 1: validate_input — THE SECURITY GUARD
# ============================================================
# This is the FIRST node that runs.
# It does 5 jobs:
#   Job 1: Check if any data was provided at all
#   Job 2: Translate field names (web form names → model names)
#   Job 3: Handle missing values (blank → NaN)
#   Job 4: Convert everything to numbers (text "25" → number 25.0)
#   Job 5: Write results back to state and mark as valid
# ============================================================

def validate_input(state):
    """
    Checks the input data, translates field names, converts
    values to numbers, and handles missing data.
    """

    # ---- Job 1: Check if any data was provided ----
    # Look at the state clipboard for "input_data"
    # If it's empty or missing, stop everything and return an error
    raw = state.get("input_data", {})

    if not raw:
        # No data at all — mark as invalid and return
        return {
            **state,
            "is_valid": False,
            "error": "No input data provided"
        }

    # ---- Job 2 + 3 + 4: Translate names, handle missing, convert to numbers ----
    translated = {}

    for web_key, model_col in FIELD_MAP.items():
        # Get the value that the web form sent for this field
        val = raw.get(web_key)

        # Job 3: If the value is missing (None) or blank ("")
        if val is None or val == "":
            # Set it to NaN — XGBoost can handle NaN values
            translated[model_col] = np.nan
        else:
            # Job 4: Try to convert the text to a number
            try:
                translated[model_col] = float(val)
            except (ValueError, TypeError):
                # If conversion fails (e.g., someone typed "abc")
                # treat it as missing data (NaN)
                translated[model_col] = np.nan

    # ---- Job 5: Write results back to state ----
    return {
        **state,
        "input_data_translated": translated,  # cleaned data ready for model
        "is_valid": True,                      # data passed all checks
        "error": None                          # no errors
    }


# ============================================================
# NODE 2: predict_pci — THE CALCULATOR
# ============================================================
# This node does 4 things:
#   1. Loads the saved model (model.pkl) from disk
#   2. Gets the list of columns the model expects
#   3. Creates a one-row table (DataFrame) with the input data
#   4. Runs the model's .predict() method to get a PCI score
# ============================================================

def predict_pci(state):
    """
    Loads the saved XGBoost model and predicts the PCI score.
    """

    try:
        # ---- Step 1: Load the saved model from disk ----
        # pickle.load() reads the model.pkl file and gives us
        # back the trained model object we saved on Day 2
        with open(MODEL_PATH, "rb") as f:
            saved = pickle.load(f)

        # ---- Step 2: Get the model and its expected columns ----
        # When we saved the model on Day 2, we saved BOTH:
        #   - The trained model itself
        #   - The list of column names the model was trained on
        # This way the model knows which columns to expect
        if isinstance(saved, dict):
            # If we saved it as a dictionary with "model" and "columns" keys
            model = saved["model"]
            columns = saved["columns"]
        else:
            # If we saved just the model object directly
            model = saved
            # Get the column names from the model's feature names
            columns = model.get_booster().feature_names

        # ---- Step 3: Create a one-row table from the input data ----
        # The model expects data in a specific order (matching the columns)
        # We create a DataFrame (table) with one row
        translated = state["input_data_translated"]

        row = {}
        for col in columns:
            # For each column the model expects, get the value
            # If a value is missing, use NaN
            row[col] = translated.get(col, np.nan)

        # Create a one-row DataFrame
        df = pd.DataFrame([row], columns=columns)

        # ---- Step 4: Predict the PCI score ----
        pci_raw = model.predict(df)[0]

        # Clip to 0-100 range (PCI can't be below 0 or above 100)
        pci = float(np.clip(pci_raw, 0, 100))

        # Write the PCI score back to state
        return {
            **state,
            "pci": round(pci, 1),       # round to 1 decimal place
            "model_columns": columns,     # save columns for explain_pci to use
            "error": None
        }

    except Exception as e:
        # If anything goes wrong (file not found, model error, etc.)
        # write the error message to state instead of crashing
        return {
            **state,
            "pci": None,
            "error": f"Prediction failed: {str(e)}"
        }


# ============================================================
# NODE 3: explain_pci — THE DETECTIVE
# ============================================================
# This node does 4 things:
#   1. Loads the saved model again
#   2. Creates the same one-row table from the input data
#   3. Runs SHAP TreeExplainer to find feature contributions
#   4. Returns the top 5 most important features
#
# SHAP tells us WHY the PCI is what it is:
#   - Negative SHAP value = pushing PCI DOWN (bad for road)
#   - Positive SHAP value = pushing PCI UP (good for road)
# ============================================================

def explain_pci(state):
    """
    Uses SHAP to explain which features drove the PCI prediction.
    Returns the top 5 most influential features.
    """

    try:
        # ---- Step 1: Load the saved model ----
        with open(MODEL_PATH, "rb") as f:
            saved = pickle.load(f)

        if isinstance(saved, dict):
            model = saved["model"]
            columns = saved["columns"]
        else:
            model = saved
            columns = model.get_booster().feature_names

        # ---- Step 2: Create the same one-row table ----
        translated = state["input_data_translated"]

        row = {}
        for col in columns:
            row[col] = translated.get(col, np.nan)

        df = pd.DataFrame([row], columns=columns)

        # ---- Step 3: Run SHAP TreeExplainer ----
        # TreeExplainer is designed for tree-based models like XGBoost
        # It calculates how much each feature "pushed" the prediction
        # up or down from the average
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df)

        # shap_values is a 2D array: [[val1, val2, val3, ...]]
        # We take the first (and only) row: shap_values[0]
        vals = shap_values[0]

        # ---- Step 4: Sort by importance and take top 5 ----
        # Pair each column name with its SHAP value
        pairs = list(zip(columns, vals))

        # Sort by absolute value (biggest impact first)
        # abs() means we care about SIZE of impact, not direction
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)

        # Take the top 5
        top = pairs[:5]

        # Format as a list of dictionaries
        # Each dictionary has "name" (feature name) and "value" (SHAP value)
        factors = [
            {"name": name, "value": round(float(v), 2)}
            for name, v in top
        ]

        # Write factors back to state
        return {
            **state,
            "factors": factors,
            "error": None
        }

    except Exception as e:
        # If SHAP fails, return empty factors with error message
        return {
            **state,
            "factors": [],
            "error": f"Explanation failed: {str(e)}"
        }


# ============================================================
# MAXIMUM RETRIES
# ============================================================
# If the prediction fails, the agent will retry up to this
# many times before giving up. This is the "continuous feedback
# loop" from the architecture diagram.
# ============================================================

MAX_RETRIES = 2


# ============================================================
# NODE 4: check_output — THE QUALITY INSPECTOR + FEEDBACK LOOP
# ============================================================
# This is the LAST node. It now does 5 things:
#   1. Checks if the PCI prediction exists
#   2. Checks if the PCI is within the valid range (0-100)
#   3. If check fails AND retries are left → marks for RETRY
#   4. Assigns a band label: Good (70+), Fair (40-69), Poor (<40)
#   5. Formats the final JSON response for Student B's web form
#
# DAY 5 ADDITION: The retry/feedback loop.
# If validation fails, the node checks how many retries
# have been attempted. If retries are left, it marks the state
# for retry (needs_retry = True). The graph will then route
# back to predict_pci to try again. If max retries are reached,
# it gives up and returns the error.
#
# This is the "continuous feedback loop" (dashed arrow) from
# the architecture diagram (Image 2 in the review paper).
# ============================================================

def check_output(state):
    """
    Validates the prediction result and formats the final response.
    Includes retry logic: if validation fails and retries are left,
    marks for retry instead of giving up immediately.
    """

    pci = state.get("pci")
    factors = state.get("factors", [])
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    # ---- Check 1: Did the prediction fail? ----
    if pci is None:
        # Can we retry?
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
            # Max retries reached — give up
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

    # ---- Check 2: Is the PCI in a reasonable range? ----
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

    # ---- Check 3: Assign the band label ----
    if pci >= 70:
        band = "Good"
    elif pci >= 40:
        band = "Fair"
    else:
        band = "Poor"

    # ---- Check 4: Format the final response ----
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