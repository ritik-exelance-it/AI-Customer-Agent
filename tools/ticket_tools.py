
"""Ticket lookup tools and guarded ticket status updates."""

from __future__ import annotations

from langchain_core.tools import tool

from config import get_settings
from database.connection import get_connection
from database.repositories.tickets import (
    get_ticket,
    list_tickets_for_customer,
    update_ticket_status,
)

VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}


def find_ticket(ticket_id: str, db_path: str | None = None) -> dict:
    """Find a support ticket by ID."""
    ticket_id = (ticket_id or "").strip()

    if not ticket_id:
        return {"ok": False, "error": "Ticket ID cannot be empty."}

    ticket = get_ticket(ticket_id, db_path=db_path)

    if ticket is None:
        return {"ok": False, "error": "Ticket not found."}

    return {"ok": True, "ticket": ticket}


def find_customer_tickets(
    customer_id: str,
    db_path: str | None = None,
) -> dict:
    """List support tickets belonging to a customer."""
    customer_id = (customer_id or "").strip()

    if not customer_id:
        return {"ok": False, "error": "Customer ID cannot be empty."}

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

    tickets = list_tickets_for_customer(customer_id, db_path=db_path)
    if tickets is None:
        return {"ok": False, "error": "Customer not found."}

    return {
        "ok": True,
        "customer_id": customer_id,
        "count": len(tickets),
        "tickets": tickets,
    }


def change_ticket_status(
    ticket_id: str,
    new_status: str,
    authorized: bool = False,
    actor: str = "system",
    db_path: str | None = None,
) -> dict:
    """Change a ticket status only when explicitly authorized."""
    ticket_id = (ticket_id or "").strip()
    new_status = (new_status or "").strip().lower()

    if not ticket_id:
        return {"ok": False, "error": "Ticket ID cannot be empty."}

    if new_status not in VALID_STATUSES:
        return {
            "ok": False,
            "error": (
                "Invalid ticket status. Choose: "
                + ", ".join(sorted(VALID_STATUSES))
                + "."
            ),
        }

    if not authorized:
        return {
            "ok": False,
            "error": "Authorization is required to update a ticket.",
        }

    try:
        updated = update_ticket_status(
            ticket_id=ticket_id,
            new_status=new_status,
            authorized=True,
            actor=actor,
            db_path=db_path,
        )
    except (ValueError, LookupError) as exc:
        return {"ok": False, "error": str(exc)}

    return updated


@tool
def get_support_ticket(ticket_id: str) -> dict:
    """Retrieve a support ticket using its ticket ID."""
    return find_ticket(
        ticket_id=ticket_id,
        db_path=get_settings().database_path,
    )


@tool
def list_customer_tickets(customer_id: str) -> dict:
    """List support tickets for a customer ID."""
    return find_customer_tickets(
        customer_id=customer_id,
        db_path=get_settings().database_path,
    )


@tool
def update_support_ticket_status(
    ticket_id: str,
    new_status: str,
) -> dict:
    """Request a ticket status change.

    This tool does not authorize itself. Status changes are rejected unless
    authorization is supplied through a trusted application service.
    """
    return change_ticket_status(
        ticket_id=ticket_id,
        new_status=new_status,
        authorized=False,
        actor="ai_tool",
        db_path=get_settings().database_path,
    )