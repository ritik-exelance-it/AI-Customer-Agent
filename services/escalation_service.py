"""Persistence helpers for routing a conversation to human support."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from config import get_settings
from database.connection import get_connection


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_escalation(
    conversation_id: str,
    reason: str,
    customer_id: str | None = None,
    *,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Create a pending escalation and write an audit record.

    The conversation must already exist. Customer association is optional, but
    when supplied it must refer to an existing customer. This function does not
    claim that a human has been notified; notification delivery is a later step.
    """
    conversation_id = (conversation_id or "").strip()
    reason = (reason or "").strip()
    customer_id = customer_id.strip() if customer_id else None
    if not conversation_id:
        return {"ok": False, "error": "Conversation ID cannot be empty."}
    if not reason:
        return {"ok": False, "error": "An escalation reason is required."}

    if db_path is None:
        db_path = str(get_settings().database_path)

    now = _utc_now()
    with get_connection(db_path) as connection:
        conversation = connection.execute(
            "SELECT conversation_id, customer_id FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        if conversation is None:
            return {"ok": False, "error": "Conversation not found."}

        effective_customer_id = customer_id or conversation["customer_id"]
        if effective_customer_id:
            customer = connection.execute(
                "SELECT customer_id FROM customers WHERE customer_id = ?",
                (effective_customer_id,),
            ).fetchone()
            if customer is None:
                return {"ok": False, "error": "Customer not found."}

        cursor = connection.execute(
            """INSERT INTO escalations
               (conversation_id, customer_id, reason, status, created_at, updated_at)
               VALUES (?, ?, ?, 'pending', ?, ?)""",
            (conversation_id, effective_customer_id, reason[:2000], now, now),
        )
        escalation_id = cursor.lastrowid
        connection.execute(
            """INSERT INTO audit_log
               (actor, action, entity_type, entity_id, details_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "system",
                "escalation_created",
                "escalation",
                str(escalation_id),
                json.dumps({"conversation_id": conversation_id, "reason": reason[:2000]}),
                now,
            ),
        )

    return {
        "ok": True,
        "escalation": {
            "escalation_id": escalation_id,
            "conversation_id": conversation_id,
            "customer_id": effective_customer_id,
            "reason": reason[:2000],
            "status": "pending",
            "created_at": now,
        },
        "message": "Escalation recorded. This does not confirm that a human has been notified.",
    }


def get_escalation(escalation_id: int, *, db_path: str | None = None) -> dict[str, Any]:
    """Fetch a single escalation by its numeric ID."""
    if db_path is None:
        db_path = str(get_settings().database_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """SELECT escalation_id, conversation_id, customer_id, reason, status,
                      assigned_to, created_at, updated_at, resolution_note
               FROM escalations WHERE escalation_id = ?""",
            (int(escalation_id),),
        ).fetchone()
    if row is None:
        return {"ok": False, "error": "Escalation not found."}
    return {"ok": True, "escalation": dict(row)}
