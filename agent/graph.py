# ============================================================
# agent/graph.py — The LangGraph workflow builder (Day 5 update)
# ============================================================
# DAY 5 CHANGES:
#   - Added a conditional edge AFTER check_output
#   - If needs_retry is True AND retries left → loop back to predict_pci
#   - If needs_retry is False → go to END (either success or gave up)
#   - This is the "continuous feedback loop" from the architecture diagram
#
# The workflow is now:
#
#   validate_input → (valid?) → predict_pci → explain_pci → check_output
#                                    ↑                            |
#                                    |                      needs_retry?
#                                    |                       /        \
#                                    +---- YES (loop back)  NO → END
# ============================================================

from langgraph.graph import StateGraph, END
from agent.nodes import validate_input, predict_pci, explain_pci, check_output


def build_graph():
    """
    Builds and compiles the LangGraph workflow with feedback loop.
    """

    graph = StateGraph(dict)

    # Add all 4 nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("predict_pci", predict_pci)
    graph.add_node("explain_pci", explain_pci)
    graph.add_node("check_output", check_output)

    # Set the starting point
    graph.set_entry_point("validate_input")

    # CONDITIONAL EDGE 1: After validate_input
    # If valid → predict. If invalid → stop.
    graph.add_conditional_edges(
        "validate_input",
        lambda state: "predict_pci" if state.get("is_valid") else END,
    )

    # Simple edges: predict → explain → check
    graph.add_edge("predict_pci", "explain_pci")
    graph.add_edge("explain_pci", "check_output")

    # DAY 5 ADDITION: CONDITIONAL EDGE 2: After check_output
    # If needs_retry → loop back to predict_pci (the feedback loop!)
    # If no retry needed → END (either success or gave up after max retries)
    graph.add_conditional_edges(
        "check_output",
        lambda state: "predict_pci" if state.get("needs_retry") else END,
    )

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
        "retry_count": 0,       # DAY 5: track retry attempts
        "needs_retry": False,   # DAY 5: flag for feedback loop
    }

    final_state = graph.invoke(initial_state)

    if "response" in final_state:
        return final_state["response"]
    else:
        return {
            "pci": None, "band": "Error", "factors": [],
            "note": final_state.get("error", "Unknown error"),
        }