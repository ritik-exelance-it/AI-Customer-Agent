"""Repository functions for support-ticket operations."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database.connection import get_connection

VALID_TICKET_STATUSES = frozenset(
    {"open", "in_progress", "resolved", "closed"}
)
VALID_TICKET_PRIORITIES = frozenset(
    {"low", "medium", "high", "urgent"}
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "medium",
    *,
    actor: str = "support_app",
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Create a ticket for an existing customer and record an audit event."""
    customer_id = (customer_id or "").strip()
    subject = (subject or "").strip()
    description = (description or "").strip()
    priority = (priority or "").strip().lower()

    if not customer_id:
        return {"ok": False, "error": "Customer ID is required."}
    if not subject:
        return {"ok": False, "error": "Ticket subject is required."}
    if not description:
        return {"ok": False, "error": "Ticket description is required."}
    if priority not in VALID_TICKET_PRIORITIES:
        return {"ok": False, "error": "Invalid ticket priority."}

    now = _now()
    ticket_id = f"TICK-{secrets.token_hex(4).upper()}"

    with get_connection(db_path) as connection:
        customer = connection.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = ? COLLATE NOCASE
            """,
            (customer_id,),
        ).fetchone()

        if customer is None:
            return {"ok": False, "error": "Customer not found."}

        canonical_customer_id = customer["customer_id"]

        connection.execute(
            """
            INSERT INTO support_tickets (
                ticket_id,
                customer_id,
                subject,
                description,
                status,
                priority,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (
                ticket_id,
                canonical_customer_id,
                subject,
                description,
                priority,
                now,
                now,
            ),
        )

        connection.execute(
            """
            INSERT INTO audit_log (
                actor,
                action,
                entity_type,
                entity_id,
                details_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                actor,
                "ticket_created",
                "support_ticket",
                ticket_id,
                json.dumps(
                    {
                        "customer_id": canonical_customer_id,
                        "priority": priority,
                    }
                ),
                now,
            ),
        )

    return {
        "ok": True,
        "ticket": {
            "ticket_id": ticket_id,
            "customer_id": canonical_customer_id,
            "subject": subject,
            "description": description,
            "status": "open",
            "priority": priority,
            "created_at": now,
            "updated_at": now,
        },
        "message": "Ticket created successfully.",
    }


def get_ticket(
    ticket_id: str,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve a ticket by ID."""
    ticket_id = (ticket_id or "").strip()
    if not ticket_id:
        return None

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT ticket_id, customer_id, subject, description, status,
                   priority, created_at, updated_at
            FROM support_tickets
            WHERE ticket_id = ? COLLATE NOCASE
            """,
            (ticket_id,),
        ).fetchone()

    return dict(row) if row else None


def list_tickets_for_customer(
    customer_id: str,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]] | None:
    """List tickets for an existing customer."""
    customer_id = (customer_id or "").strip()
    if not customer_id:
        return None

    with get_connection(db_path) as connection:
        customer = connection.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = ? COLLATE NOCASE
            """,
            (customer_id,),
        ).fetchone()

        if customer is None:
            return None

        rows = connection.execute(
            """
            SELECT ticket_id, customer_id, subject, status, priority,
                   created_at, updated_at
            FROM support_tickets
            WHERE customer_id = ? COLLATE NOCASE
            ORDER BY created_at DESC, ticket_id DESC
            """,
            (customer["customer_id"],),
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
    """Update ticket status only when the caller has authorized the change."""
    ticket_id = (ticket_id or "").strip()
    new_status = (new_status or "").strip().lower()

    if not ticket_id:
        return {"ok": False, "error": "Ticket ID cannot be empty."}

    if new_status not in VALID_TICKET_STATUSES:
        return {"ok": False, "error": "Invalid ticket status."}

    if not authorized:
        return {
            "ok": False,
            "error": "Authorization is required to update a ticket.",
        }

    now = _now()

    with get_connection(db_path) as connection:
        existing = connection.execute(
            """
            SELECT ticket_id
            FROM support_tickets
            WHERE ticket_id = ? COLLATE NOCASE
            """,
            (ticket_id,),
        ).fetchone()

        if existing is None:
            return {"ok": False, "error": "Ticket not found."}

        canonical_ticket_id = existing["ticket_id"]

        connection.execute(
            """
            UPDATE support_tickets
            SET status = ?, updated_at = ?
            WHERE ticket_id = ?
            """,
            (new_status, now, canonical_ticket_id),
        )

        connection.execute(
            """
            INSERT INTO audit_log (
                actor,
                action,
                entity_type,
                entity_id,
                details_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                actor,
                "ticket_status_updated",
                "support_ticket",
                canonical_ticket_id,
                json.dumps({"status": new_status}),
                now,
            ),
        )

    return {
        "ok": True,
        "ticket": {
            "ticket_id": canonical_ticket_id,
            "status": new_status,
            "updated_at": now,
        },
        "message": "Ticket status updated successfully.",
    }