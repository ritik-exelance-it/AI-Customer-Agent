
"""Nodes used by the customer support graph."""

from langchain_core.messages import AIMessage, SystemMessage

from agents.prompts import CUSTOMER_SUPPORT_SYSTEM_PROMPT
from graph.state import SupportState
from model import llm


def support_node(state: SupportState) -> dict:
    """Generate a response to the customer's latest message."""

    messages = state.get("messages", [])

    if not messages:
        return {
            "error": "No messages were provided.",
            "requires_human": False,
        }

    prompt_messages = [
        SystemMessage(content=CUSTOMER_SUPPORT_SYSTEM_PROMPT),
        *messages,
    ]

    try:
        response = llm.invoke(prompt_messages)

        return {
            "messages": [response],
            "error": None,
        }

    except Exception:
        return {
            "error": "The support response could not be generated.",
            "messages": [
                AIMessage(
                    content=(
                        "I'm sorry, but I'm having trouble processing "
                        "your request right now. Please try again shortly."
                    )
                )
            ],
        }


def escalation_node(state: SupportState) -> dict:
    """Prepare a response when human assistance is required."""

    return {
        "requires_human": True,
        "messages": [
            AIMessage(
                content=(
                    "Your request may need assistance from a human "
                    "support representative. Please provide any relevant "
                    "ticket number so the support team can follow up."
                )
            )
        ],
    }
