"""Application service for creating support tickets."""

from __future__ import annotations

from config import get_settings
from database.repositories.tickets import create_ticket, get_ticket


def get_support_ticket(ticket_id: str) -> dict:
    """Retrieve a support ticket by ID."""
    ticket = get_ticket(
        ticket_id=ticket_id,
        db_path=get_settings().database_path,
    )
    if ticket is None:
        return {"ok": False, "error": "Ticket not found."}
    return {"ok": True, "ticket": ticket}


def create_support_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "medium",
    *,
    confirmed: bool = False,
    actor: str = "support_app",
) -> dict:
    """Create a ticket only after the user explicitly confirms submission."""
    customer_id = (customer_id or "").strip()
    subject = (subject or "").strip()
    description = (description or "").strip()
    priority = (priority or "").strip().lower()

    if not confirmed:
        return {
            "ok": False,
            "error": "Explicit confirmation is required before submitting the ticket.",
        }

    if not customer_id:
        return {"ok": False, "error": "Customer ID is required."}

    if not subject:
        return {"ok": False, "error": "Ticket subject is required."}

    if not description:
        return {"ok": False, "error": "Ticket description is required."}

    if priority not in {"low", "medium", "high", "urgent"}:
        return {"ok": False, "error": "Choose a valid ticket priority."}

    return create_ticket(
        customer_id=customer_id,
        subject=subject,
        description=description,
        priority=priority,
        actor=actor,
        db_path=get_settings().database_path,
    )