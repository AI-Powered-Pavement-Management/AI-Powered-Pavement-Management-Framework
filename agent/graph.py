# ============================================================
# agent/graph.py — DAY 7 UPDATE
# ============================================================
# DAY 7 CHANGES:
#   - Imported the new recommend_maintenance node
#   - Added it to the graph
#   - Changed the conditional edge after check_output:
#       old: needs_retry ? predict_pci : END
#       new: needs_retry ? predict_pci : recommend_maintenance
#   - Added final edge: recommend_maintenance → END
#
# The workflow is now:
#
#   validate_input → (valid?) → predict_pci → explain_pci → check_output
#                                    ↑                            |
#                                    |                      needs_retry?
#                                    |                       /        \
#                                    +---- YES (loop back)  NO
#                                                            |
#                                                            v
#                                                  recommend_maintenance
#                                                            |
#                                                            v
#                                                           END
# ============================================================

from langgraph.graph import StateGraph, END
from agent.nodes import (
    validate_input,
    predict_pci,
    explain_pci,
    check_output,
    recommend_maintenance,   # DAY 7 NEW
)


def build_graph():
    """
    Builds and compiles the LangGraph workflow with:
    - Input validation
    - Prediction (XGBoost)
    - Explanation (SHAP)
    - Output validation + retry loop
    - Maintenance recommendation (Human Oversight)   [Day 7]
    """

    graph = StateGraph(dict)

    # ---- Add all 5 nodes ----
    graph.add_node("validate_input", validate_input)
    graph.add_node("predict_pci", predict_pci)
    graph.add_node("explain_pci", explain_pci)
    graph.add_node("check_output", check_output)
    graph.add_node("recommend_maintenance", recommend_maintenance)   # DAY 7 NEW

    # ---- Set the starting point ----
    graph.set_entry_point("validate_input")

    # ---- Edge after validate_input: valid → predict, invalid → END ----
    graph.add_conditional_edges(
        "validate_input",
        lambda state: "predict_pci" if state.get("is_valid") else END,
    )

    # ---- Simple edges through the middle of the graph ----
    graph.add_edge("predict_pci", "explain_pci")
    graph.add_edge("explain_pci", "check_output")

    # ---- Edge after check_output ----
    # DAY 7 CHANGE: on success we now go to recommend_maintenance
    #               (previously went straight to END)
    graph.add_conditional_edges(
        "check_output",
        lambda state: "predict_pci" if state.get("needs_retry") else "recommend_maintenance",
    )

    # ---- DAY 7 NEW: recommend_maintenance is the final node ----
    graph.add_edge("recommend_maintenance", END)

    return graph.compile()


def run_agent(input_data):
    """
    Builds the graph, runs it with input data, returns the response.
    """
    graph = build_graph()

    initial_state = {
        "input_data": input_data,
        "pci": None,
        "factors": None,
        "is_valid": None,
        "error": None,
        "retry_count": 0,
        "needs_retry": False,
    }

    final_state = graph.invoke(initial_state)

    if "response" in final_state:
        return final_state["response"]
    else:
        return {
            "pci": None,
            "band": "Error",
            "factors": [],
            "note": final_state.get("error", "Unknown error"),
            "recommendation": "No recommendation available — agent failed.",
            "priority": "N/A",
        }
