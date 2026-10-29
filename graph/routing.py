
"""Routing rules for the customer support graph."""

from graph.state import SupportState


def route_request(state: SupportState) -> str:
    """Route requests based on the current workflow state."""

    if state.get("requires_human", False):
        return "escalation"

    if state.get("error"):
        return "end"

    return "support"
