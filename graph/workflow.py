from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agents.tools import SUPPORT_TOOLS
from graph.nodes import escalation_node, support_node
from graph.routing import route_after_support
from graph.state import SupportState


def build_support_graph():
    graph = StateGraph(SupportState)

    graph.add_node("support", support_node)
    graph.add_node("tools", ToolNode(SUPPORT_TOOLS))
    graph.add_node("escalation", escalation_node)

    graph.add_edge(START, "support")

    graph.add_conditional_edges(
        "support",
        route_after_support,
        {
            "tools": "tools",
            "escalation": "escalation",
            "end": END,
        },
    )

    # After a tool executes, send its result back to the model.
    graph.add_edge("tools", "support")

    graph.add_edge("escalation", END)

    return graph.compile()


support_graph = build_support_graph()