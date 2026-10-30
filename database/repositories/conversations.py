"""Persistence helpers for conversation sessions and their messages."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from database.connection import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_conversation(
    customer_id: str | None = None,
    title: str = "Support conversation",
    metadata: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    conversation_id = str(uuid.uuid4())
    now = _now()
    with get_connection(db_path) as connection:
        if customer_id:
            exists = connection.execute(
                "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id.strip(),)
            ).fetchone()
            if exists is None:
                return {"ok": False, "error": "Customer not found."}
            customer_id = customer_id.strip()
        connection.execute(
            """INSERT INTO conversations
               (conversation_id, customer_id, title, status, created_at, updated_at, metadata_json)
               VALUES (?, ?, ?, 'active', ?, ?, ?)""",
            (conversation_id, customer_id, title.strip() or "Support conversation",
             now, now, json.dumps(metadata or {}, ensure_ascii=False)),
        )
    return {"ok": True, "conversation": {
        "conversation_id": conversation_id, "customer_id": customer_id,
        "title": title.strip() or "Support conversation", "status": "active",
        "created_at": now, "updated_at": now,
    }}


def get_conversation(
    conversation_id: str, db_path: str | Path | None = None
) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            """SELECT conversation_id, customer_id, title, status, created_at,
                      updated_at, metadata_json FROM conversations
               WHERE conversation_id = ?""", (conversation_id.strip(),)
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["metadata"] = json.loads(result.pop("metadata_json") or "{}")
    return result


def append_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    role = role.strip().lower()
    if role not in {"system", "user", "assistant", "tool", "human"}:
        return {"ok": False, "error": "Unsupported message role."}
    if not content.strip():
        return {"ok": False, "error": "Message content cannot be empty."}
    now = _now()
    with get_connection(db_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM conversations WHERE conversation_id = ?",
            (conversation_id.strip(),),
        ).fetchone()
        if exists is None:
            return {"ok": False, "error": "Conversation not found."}
        cursor = connection.execute(
            """INSERT INTO conversation_messages
               (conversation_id, role, content, created_at, metadata_json)
               VALUES (?, ?, ?, ?, ?)""",
            (conversation_id.strip(), role, content, now,
             json.dumps(metadata or {}, ensure_ascii=False)),
        )
        message_id = cursor.lastrowid
        connection.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (now, conversation_id.strip()),
        )
    return {"ok": True, "message": {
        "message_id": message_id, "conversation_id": conversation_id.strip(),
        "role": role, "content": content, "created_at": now,
        "metadata": metadata or {},
    }}


def list_messages(
    conversation_id: str,
    limit: int = 200,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]] | None:
    limit = max(1, min(int(limit), 1000))
    with get_connection(db_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM conversations WHERE conversation_id = ?",
            (conversation_id.strip(),),
        ).fetchone()
        if exists is None:
            return None
        rows = connection.execute(
            """SELECT message_id, conversation_id, role, content, created_at, metadata_json
               FROM conversation_messages WHERE conversation_id = ?
               ORDER BY message_id ASC LIMIT ?""",
            (conversation_id.strip(), limit),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


def set_conversation_status(
    conversation_id: str,
    status: str,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    allowed = {"active", "resolved", "escalated", "archived"}
    status = status.strip().lower()
    if status not in allowed:
        return {"ok": False, "error": "Invalid conversation status."}
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "UPDATE conversations SET status = ?, updated_at = ? WHERE conversation_id = ?",
            (status, _now(), conversation_id.strip()),
        )
        if cursor.rowcount == 0:
            return {"ok": False, "error": "Conversation not found."}
    return {"ok": True, "conversation_id": conversation_id.strip(), "status": status}

def list_conversations(limit: int = 100, db_path=None) -> list[dict]:
    limit = max(1, min(int(limit), 500))
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """SELECT conversation_id, customer_id, title, status, created_at, updated_at
               FROM conversations ORDER BY updated_at DESC, created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]