from langchain_core.tools import tool

from config import get_settings
from database.connection import get_connection


def find_customer(
    customer_id: str,
    db_path: str | None = None,
) -> dict:
    """Find a customer by their customer ID."""

    customer_id = customer_id.strip()

    if not customer_id:
        return {
            "ok": False,
            "error": "Customer ID cannot be empty.",
        }

    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                customer_id,
                full_name,
                account_status,
                created_at
            FROM customers
            WHERE customer_id = ?
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


@tool
def lookup_customer(customer_id: str) -> dict:
    """Look up a customer using their customer ID.

    Returns the customer's ID, name, account status, and
    creation date. Does not return the customer's email.
    """

    return find_customer(
        customer_id=customer_id,
        db_path=get_settings().database_path,
    )