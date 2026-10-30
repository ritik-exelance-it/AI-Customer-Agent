"""Customer lookup helpers and AI-accessible customer tool."""

from __future__ import annotations

from langchain_core.tools import tool

from config import get_settings
from database.connection import get_connection


def find_customer(
    customer_id: str,
    db_path: str | None = None,
) -> dict:
    """Find a customer by ID without case-sensitive matching."""

    customer_id = (customer_id or "").strip()

    if not customer_id:
        return {
            "ok": False,
            "error": "Customer ID cannot be empty.",
        }

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT customer_id, full_name, account_status, created_at
            FROM customers
            WHERE customer_id = ? COLLATE NOCASE
            """,
            (customer_id,),
        ).fetchone()

    if row is None:
        return {
            "ok": False,
            "error": "Customer not found.",
        }

    return {
        "ok": True,
        "customer": dict(row),
    }


def find_customer_by_name(
    full_name: str,
    db_path: str | None = None,
) -> dict:
    """Find a customer by full name, handling ambiguous matches safely."""

    full_name = " ".join((full_name or "").split())

    if not full_name:
        return {
            "ok": False,
            "error": "Customer name cannot be empty.",
        }

    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT customer_id, full_name, account_status, created_at
            FROM customers
            WHERE full_name = ? COLLATE NOCASE
            ORDER BY customer_id
            LIMIT 3
            """,
            (full_name,),
        ).fetchall()

    if not rows:
        return {
            "ok": False,
            "error": "Customer not found.",
        }

    if len(rows) > 1:
        return {
            "ok": False,
            "error": (
                "Multiple customers have that name. "
                "Please provide the customer's ID."
            ),
        }

    return {
        "ok": True,
        "customer": dict(rows[0]),
    }


@tool
def lookup_customer(
    customer_id: str | None = None,
    full_name: str | None = None,
) -> dict:
    """Look up a customer using their customer ID or full name.

    Supply customer_id when the customer ID is known. Otherwise, supply
    full_name. Returns the customer ID, full name, account status, and
    creation date. Does not return the customer's email address.
    """

    db_path = get_settings().database_path

    if customer_id and customer_id.strip():
        return find_customer(customer_id=customer_id, db_path=db_path)

    if full_name and full_name.strip():
        return find_customer_by_name(full_name=full_name, db_path=db_path)

    return {
        "ok": False,
        "error": "Provide a customer ID or full name.",
    }