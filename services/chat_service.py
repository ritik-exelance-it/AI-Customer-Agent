"""Orchestrate validated customer messages through the support graph."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterator

from langchain_core.messages import AIMessage, HumanMessage

from config import get_settings
from database.repositories import conversations
from database.schema import initialize_database
from graph.workflow import build_support_graph
from middleware.builtin import evaluate_incoming_message
from services.escalation_service import create_escalation


def _db_path() -> str:
    return str(get_settings().database_path)


@lru_cache(maxsize=1)
def _persistent_graph():
    """Compile one graph with a durable SQLite checkpointer per process."""
    return build_support_graph(persistent=True)


def _plain_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip() if content is not None else ""


def _assistant_text(state: dict[str, Any]) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            text = _plain_text(message.content)
            if text:
                return text
    return "I'm sorry, but I couldn't prepare a response. Please try again or request human support."


def _validate_conversation(conversation_id: str) -> dict[str, Any] | None:
    return conversations.get_conversation(conversation_id, db_path=_db_path())


def stream_chat(conversation_id: str, message: str) -> Iterator[dict[str, Any]]:
    """Yield activity events followed by one final answer event.

    Event format is intentionally UI-neutral so Streamlit or another client can
    consume it. This is activity streaming, not token-by-token model streaming.
    """
    db_path = _db_path()
    initialize_database(db_path=db_path)
    conversation_id = (conversation_id or "").strip()
    user_message = message if isinstance(message, str) else ""

    validation, review = evaluate_incoming_message(user_message)
    if not validation.allowed:
        yield {"type": "error", "message": validation.reason or "Invalid message."}
        return

    conversation = _validate_conversation(conversation_id)
    if conversation is None:
        yield {"type": "error", "message": "Conversation not found. Create a conversation first."}
        return

    saved_user = conversations.append_message(
        conversation_id, "user", user_message.strip(), db_path=db_path
    )
    if not saved_user.get("ok"):
        yield {"type": "error", "message": saved_user.get("error", "Could not save message.")}
        return

    yield {"type": "activity", "stage": "accepted", "message": "Message received."}

    if review.requires_human:
        reason = review.reason or "Human review requested by support policy."
        escalation = create_escalation(
            conversation_id,
            reason,
            customer_id=conversation.get("customer_id"),
            db_path=db_path,
        )
        conversations.set_conversation_status(conversation_id, "escalated", db_path=db_path)
        answer = (
            "I understand this may need specialist attention. I've recorded a request "
            "for human support. This does not mean a representative has been notified yet."
        ) if escalation.get("ok") else (
            "This request needs human support, but I couldn't record the escalation. "
            "Please contact the support team directly."
        )
        conversations.append_message(
            conversation_id, "assistant", answer,
            metadata={"requires_human": True, "escalation": escalation.get("escalation")},
            db_path=db_path,
        )
        yield {"type": "activity", "stage": "escalation", "message": "Human review is required."}
        yield {"type": "final", "answer": answer, "sources": [], "requires_human": True,
               "escalation": escalation.get("escalation")}
        return

    yield {"type": "activity", "stage": "retrieval_and_reasoning", "message": "Checking available support information."}
    try:
        graph = _persistent_graph()
        graph_input = {
            "messages": [HumanMessage(content=user_message.strip())],
            "conversation_id": conversation_id,
            "customer_id": conversation.get("customer_id"),
            "requires_human": False,
            "escalation_reason": None,
            "sources": [],
            "error": None,
        }
        config = {"configurable": {"thread_id": conversation_id}}
        final_state: dict[str, Any] = {}
        for update in graph.stream(graph_input, config=config, stream_mode="updates"):
            if not isinstance(update, dict):
                continue
            for node_name, node_update in update.items():
                if node_name == "tools":
                    yield {"type": "activity", "stage": "tools", "message": "Using a support tool."}
                elif node_name == "collect_sources":
                    yield {"type": "activity", "stage": "sources", "message": "Collecting answer sources."}
                if isinstance(node_update, dict):
                    if "messages" in node_update:
                        final_state.setdefault("messages", []).extend(node_update["messages"])
                    final_state.update({k: v for k, v in node_update.items() if k != "messages"})

        # Read the checkpointed aggregate state for reliable final sources and flags.
        try:
            snapshot = graph.get_state(config)
            if getattr(snapshot, "values", None):
                final_state = dict(snapshot.values)
        except Exception:
            pass
        answer = _assistant_text(final_state)
        sources = final_state.get("sources", []) or []
        requires_human = bool(final_state.get("requires_human", False))
        metadata = {"sources": sources, "requires_human": requires_human}
        conversations.append_message(conversation_id, "assistant", answer, metadata=metadata, db_path=db_path)
        if requires_human:
            conversations.set_conversation_status(conversation_id, "escalated", db_path=db_path)
        yield {"type": "final", "answer": answer, "sources": sources,
               "requires_human": requires_human, "error": final_state.get("error")}
    except Exception:
        fallback = "I'm sorry, but the support service is temporarily unavailable. Please try again shortly."
        conversations.append_message(conversation_id, "assistant", fallback,
                                     metadata={"error": "support_service_unavailable"}, db_path=db_path)
        yield {"type": "error", "message": "The support workflow could not be completed."}
        yield {"type": "final", "answer": fallback, "sources": [], "requires_human": False}


def chat(conversation_id: str, message: str) -> dict[str, Any]:
    """Non-streaming convenience wrapper; returns the final event as a dict."""
    final: dict[str, Any] | None = None
    for event in stream_chat(conversation_id, message):
        if event.get("type") in {"final", "error"}:
            if event.get("type") == "final":
                final = event
            elif final is None:
                final = {"ok": False, **event}
    return final or {"ok": False, "error": "No response was produced."}
