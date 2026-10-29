
"""Build and compile the customer support workflow."""

from langgraph.graph import END, START, StateGraph

from graph.nodes import escalation_node, support_node
from graph.routing import route_request
from graph.state import SupportState


def build_support_graph():
    """Create and compile the support workflow."""

    graph = StateGraph(SupportState)

    graph.add_node("support", support_node)
    graph.add_node("escalation", escalation_node)

    graph.add_edge(START, "support")

    graph.add_conditional_edges(
        "support",
        route_request,
        {
            "support": END,
            "escalation": "escalation",
            "end": END,
        },
    )

    graph.add_edge("escalation", END)

    return graph.compile()


support_graph = build_support_graph()
