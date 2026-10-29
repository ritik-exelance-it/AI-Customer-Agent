from datetime import datetime, timezone

from langchain_core.tools import tool

from config import get_settings
from database.connection import get_connection


VALID_TICKET_STATUSES = {
    "open",
    "in_progress",
    "resolved",
    "closed",
}


def find_ticket(
    ticket_id: str,
    db_path: str | None = None,
) -> dict:
    """Retrieve a support ticket by its ID."""

    ticket_id = ticket_id.strip()

    if not ticket_id:
        return {
            "ok": False,
            "error": "Ticket ID cannot be empty.",
        }

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                ticket_id,
                customer_id,
                subject,
                description,
                status,
                priority,
                created_at,
                updated_at
            FROM support_tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    if row is None:
        return {
            "ok": False,
            "error": "Ticket not found.",
        }

    return {
        "ok": True,
        "ticket": dict(row),
    }


def find_customer_tickets(
    customer_id: str,
    db_path: str | None = None,
) -> dict:
    """List support tickets associated with a customer."""

    customer_id = customer_id.strip()

    if not customer_id:
        return {
            "ok": False,
            "error": "Customer ID cannot be empty.",
        }

    with get_connection(db_path) as connection:
        customer = connection.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()

        if customer is None:
            return {
                "ok": False,
                "error": "Customer not found.",
            }

        rows = connection.execute(
            """
            SELECT
                ticket_id,
                subject,
                status,
                priority,
                created_at,
                updated_at
            FROM support_tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (customer_id,),
        ).fetchall()

    return {
        "ok": True,
        "customer_id": customer_id,
        "tickets": [dict(row) for row in rows],
        "count": len(rows),
    }


def change_ticket_status(
    ticket_id: str,
    new_status: str,
    db_path: str | None = None,
) -> dict:
    """Update a ticket's status after validating the requested status."""

    ticket_id = ticket_id.strip()
    new_status = new_status.strip().lower()

    if not ticket_id:
        return {
            "ok": False,
            "error": "Ticket ID cannot be empty.",
        }

    if new_status not in VALID_TICKET_STATUSES:
        return {
            "ok": False,
            "error": (
                "Invalid status. Allowed values: "
                + ", ".join(sorted(VALID_TICKET_STATUSES))
            ),
        }

    now = datetime.now(timezone.utc).isoformat()

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE support_tickets
            SET status = ?, updated_at = ?
            WHERE ticket_id = ?
            """,
            (new_status, now, ticket_id),
        )

        if cursor.rowcount == 0:
            return {
                "ok": False,
                "error": "Ticket not found.",
            }

        row = connection.execute(
            """
            SELECT ticket_id, status, updated_at
            FROM support_tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    return {
        "ok": True,
        "ticket": dict(row),
        "message": "Ticket status updated successfully.",
    }


@tool
def get_support_ticket(ticket_id: str) -> dict:
    """Retrieve the details and current status of a support ticket."""

    return find_ticket(
        ticket_id=ticket_id,
        db_path=get_settings().database_path,
    )


@tool
def list_customer_tickets(customer_id: str) -> dict:
    """List support tickets associated with a customer ID."""

    return find_customer_tickets(
        customer_id=customer_id,
        db_path=get_settings().database_path,
    )


@tool
def update_support_ticket_status(
    ticket_id: str,
    new_status: str,
) -> dict:
    """Update a support ticket's status.

    Allowed statuses: open, in_progress, resolved, closed.
    Use this tool only when the requested update is authorized.
    """

    return change_ticket_status(
        ticket_id=ticket_id,
        new_status=new_status,
        db_path=get_settings().database_path,
    )