"""Support-ticket read operations and validated status transitions."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from database.connection import get_connection

VALID_TICKET_STATUSES = frozenset({"open", "in_progress", "resolved", "closed"})


def get_ticket(ticket_id: str, db_path: str | Path | None = None) -> dict[str, Any] | None:
    ticket_id = ticket_id.strip()
    if not ticket_id:
        return None
    with get_connection(db_path) as connection:
        row = connection.execute(
            """SELECT ticket_id, customer_id, subject, description, status,
                      priority, created_at, updated_at
               FROM support_tickets WHERE ticket_id = ?""", (ticket_id,)
        ).fetchone()
    return dict(row) if row else None


def list_tickets_for_customer(
    customer_id: str, db_path: str | Path | None = None
) -> list[dict[str, Any]] | None:
    customer_id = customer_id.strip()
    if not customer_id:
        return None
    with get_connection(db_path) as connection:
        customer = connection.execute(
            "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        if customer is None:
            return None
        rows = connection.execute(
            """SELECT ticket_id, subject, status, priority, created_at, updated_at
               FROM support_tickets WHERE customer_id = ?
               ORDER BY created_at DESC, ticket_id DESC""", (customer_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    *,
    authorized: bool = False,
    actor: str = "system",
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Update status only when caller explicitly confirms authorization.

    This is a repository-level safety guard, not a replacement for verifying
    the customer's identity and permissions in the service/tool layer.
    """
    ticket_id = ticket_id.strip()
    new_status = new_status.strip().lower()
    if not ticket_id:
        return {"ok": False, "error": "Ticket ID cannot be empty."}
    if new_status not in VALID_TICKET_STATUSES:
        return {"ok": False, "error": "Invalid ticket status."}
    if not authorized:
        return {"ok": False, "error": "Authorization is required to update a ticket."}
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """UPDATE support_tickets SET status = ?, updated_at = ?
               WHERE ticket_id = ?""", (new_status, now, ticket_id)
        )
        if cursor.rowcount == 0:
            return {"ok": False, "error": "Ticket not found."}
        row = connection.execute(
            "SELECT ticket_id, status, updated_at FROM support_tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()
        connection.execute(
            """INSERT INTO audit_log
               (actor, action, entity_type, entity_id, details_json, created_at)
               VALUES (?, 'ticket_status_updated', 'support_ticket', ?, ?, ?)""",
            (actor, ticket_id, '{"status":"' + new_status + '"}', now),
        )
    return {"ok": True, "ticket": dict(row), "message": "Ticket status updated successfully."}
