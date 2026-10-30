"""Customer read operations."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from database.connection import get_connection


def get_customer(customer_id: str, db_path: str | Path | None = None) -> dict[str, Any] | None:
    customer_id = customer_id.strip()
    if not customer_id:
        return None
    with get_connection(db_path) as connection:
        row = connection.execute(
            """SELECT customer_id, full_name, account_status, created_at
               FROM customers WHERE customer_id = ?""", (customer_id,)
        ).fetchone()
    return dict(row) if row else None


def customer_exists(customer_id: str, db_path: str | Path | None = None) -> bool:
    customer_id = customer_id.strip()
    if not customer_id:
        return False
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    return row is not None
