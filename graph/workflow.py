"""LangGraph workflow for the AI customer support agent."""

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agents.tools import SUPPORT_TOOLS
from graph.nodes import (
    collect_sources_node,
    escalation_node,
    reset_turn_node,
    support_node,
)
from graph.routing import route_after_support
from graph.state import SupportState


def build_support_graph():
    """Build and compile the customer support workflow."""

    graph = StateGraph(SupportState)

    graph.add_node("reset_turn", reset_turn_node)
    graph.add_node("support", support_node)
    graph.add_node("tools", ToolNode(SUPPORT_TOOLS))
    graph.add_node("collect_sources", collect_sources_node)
    graph.add_node("escalation", escalation_node)

    graph.add_edge(START, "reset_turn")
    graph.add_edge("reset_turn", "support")

    graph.add_conditional_edges(
        "support",
        route_after_support,
        {
            "tools": "tools",
            "escalation": "escalation",
            "end": END,
        },
    )

    graph.add_edge("tools", "collect_sources")
    graph.add_edge("collect_sources", "support")

    graph.add_edge("escalation", END)

    return graph.compile()


support_graph = build_support_graph()