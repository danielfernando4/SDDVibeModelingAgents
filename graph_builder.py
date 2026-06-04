from langgraph.graph import StateGraph, END
from state import AgentState

from nodes.selector import selector_node
from nodes.phase_node import product_node, requirements_node, design_node


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("selector", selector_node)
    builder.add_node("product_node", product_node)
    builder.add_node("requirements_node", requirements_node)
    builder.add_node("design_node", design_node)

    builder.set_entry_point("selector")

    builder.add_conditional_edges(
        "selector",
        _route,
        {
            "product_node": "product_node",
            "requirements_node": "requirements_node",
            "design_node": "design_node",
            "END": END,
        },
    )

    builder.add_edge("product_node", "selector")
    builder.add_edge("requirements_node", "selector")
    builder.add_edge("design_node", "selector")

    return builder


def _route(state: AgentState) -> str:
    target_phase = state.get("target_phase", "")

    if target_phase == "product":
        return "product_node"
    if target_phase == "requirements":
        return "requirements_node"
    if target_phase == "design":
        return "design_node"
    return "END"
