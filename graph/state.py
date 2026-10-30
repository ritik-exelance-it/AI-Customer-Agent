"""Typed state shared by nodes in the support workflow."""
from __future__ import annotations

from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SourceReference(TypedDict):
    """A knowledge-base source used to ground an answer."""
    source: str
    chunk_index: int
    score: float


class SupportState(TypedDict):
    """State persisted by LangGraph between turns of a conversation."""
    messages: Annotated[list[AnyMessage], add_messages]
    customer_id: str | None
    ticket_id: str | None
    intent: str | None
    requires_human: bool
    sources: list[SourceReference]
    error: str | None
    # Conversation metadata is deliberately optional for backwards compatibility.
    conversation_id: str | None
    escalation_reason: str | None
