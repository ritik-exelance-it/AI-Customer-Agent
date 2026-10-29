"""State definition for the customer support workflow."""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SourceReference(TypedDict):
    """Metadata identifying a retrieved knowledge-base excerpt."""

    source: str
    chunk_index: int
    score: float


class SupportState(TypedDict):
    """Shared state passed between LangGraph nodes."""

    messages: Annotated[list[AnyMessage], add_messages]

    customer_id: str | None
    ticket_id: str | None

    intent: str | None
    requires_human: bool

    sources: list[SourceReference]
    error: str | None