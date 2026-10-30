"""PATCH: replace the existing services/conversation_service.py with this version."""
from __future__ import annotations
from typing import Any
from config import get_settings
from database.repositories import conversations
from database.schema import initialize_database


def _database_path() -> str:
    return str(get_settings().database_path)


def create_support_conversation(customer_id: str | None = None, title: str = "Support conversation") -> dict[str, Any]:
    db_path = _database_path()
    initialize_database(db_path=db_path)
    return conversations.create_conversation(customer_id=customer_id, title=title, db_path=db_path)


def get_conversation_history(conversation_id: str, limit: int = 200) -> dict[str, Any]:
    db_path = _database_path()
    conversation = conversations.get_conversation(conversation_id, db_path=db_path)
    if conversation is None:
        return {"ok": False, "error": "Conversation not found."}
    messages = conversations.list_messages(conversation_id, limit=limit, db_path=db_path)
    return {"ok": True, "conversation": conversation, "messages": messages or []}


def list_support_conversations(limit: int = 100) -> list[dict[str, Any]]:
    """Return actual saved conversations, newest updated first."""
    db_path = _database_path()
    initialize_database(db_path=db_path)
    return conversations.list_conversations(limit=limit, db_path=db_path)
