"""LangGraph workflow for the AI customer support agent."""
from __future__ import annotations

from typing import Any
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agents.tools import SUPPORT_TOOLS
from graph.checkpointer import get_checkpointer
from graph.nodes import (
    collect_sources_node,
    escalation_node,
    reset_turn_node,
    support_node,
)
from graph.routing import route_after_support
from graph.state import SupportState


def build_support_graph(checkpointer: Any = None, *, persistent: bool = False):
    """Build and compile the support graph.

    Pass ``persistent=True`` to attach the SQLite checkpointer automatically,
    or pass a custom LangGraph checkpointer (useful for isolated tests).
    """
    if persistent and checkpointer is None:
        checkpointer = get_checkpointer()
        if checkpointer is None:
            raise RuntimeError(
                "Persistent conversations require langgraph-checkpoint-sqlite. "
                "Install the project's requirements.txt first."
            )

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
        {"tools": "tools", "escalation": "escalation", "end": END},
    )
    graph.add_edge("tools", "collect_sources")
    graph.add_edge("collect_sources", "support")
    graph.add_edge("escalation", END)
    return graph.compile(checkpointer=checkpointer)


# Backwards-compatible default for existing imports and tests. The app service
# should use build_support_graph(persistent=True) for durable conversation state.
support_graph = build_support_graph()
