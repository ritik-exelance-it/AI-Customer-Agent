from langchain_core.messages import AIMessage

from graph.state import SupportState


def route_after_support(state: SupportState) -> str:
    """Choose whether to execute tools, escalate, or finish."""

    if state.get("requires_human", False):
        return "escalation"

    if state.get("error"):
        return "end"

    messages = state.get("messages", [])

    if messages and isinstance(messages[-1], AIMessage):
        if messages[-1].tool_calls:
            return "tools"

    return "end"