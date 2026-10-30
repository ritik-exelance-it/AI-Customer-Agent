"""Tests for support-ticket creation."""

import pytest

from database.connection import get_connection
from database.schema import initialize_database
from services.ticket_service import create_support_ticket


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create an isolated SQLite database for each test."""
    db_path = str(tmp_path / "test_support.db")
    initialize_database(db_path=db_path, seed_demo_data=True)

    from config import get_settings

    monkeypatch.setattr(
        get_settings(),
        "database_path",
        db_path,
    )

    return db_path


def test_ticket_creation_requires_confirmation(test_db):
    result = create_support_ticket(
        customer_id="CUST-1001",
        subject="Cannot log in",
        description="Login fails after entering credentials.",
        confirmed=False,
    )

    assert result["ok"] is False
    assert "confirm" in result["error"].lower()


def test_create_ticket_successfully(test_db):
    result = create_support_ticket(
        customer_id="CUST-1001",
        subject="Password reset issue",
        description="Password reset email never arrives.",
        priority="high",
        confirmed=True,
    )

    assert result["ok"] is True
    ticket = result["ticket"]
    assert ticket["customer_id"] == "CUST-1001"
    assert ticket["subject"] == "Password reset issue"
    assert ticket["status"] == "open"
    assert ticket["priority"] == "high"
    assert ticket["ticket_id"].startswith("TICK-")


def test_unknown_customer_is_rejected(test_db):
    result = create_support_ticket(
        customer_id="CUST-UNKNOWN",
        subject="Test issue",
        description="This should not create a ticket.",
        confirmed=True,
    )

    assert result["ok"] is False
    assert "customer" in result["error"].lower()


@pytest.mark.parametrize(
    ("subject", "description", "priority"),
    [
        ("", "A description", "medium"),
        ("A subject", "", "medium"),
        ("A subject", "A description", "invalid"),
    ],
)
def test_invalid_ticket_fields_are_rejected(
    test_db,
    subject,
    description,
    priority,
):
    result = create_support_ticket(
        customer_id="CUST-1001",
        subject=subject,
        description=description,
        priority=priority,
        confirmed=True,
    )

    assert result["ok"] is False


def test_ticket_creation_writes_audit_record(test_db):
    result = create_support_ticket(
        customer_id="CUST-1001",
        subject="Audit test",
        description="Check that ticket creation is recorded.",
        confirmed=True,
    )

    assert result["ok"] is True
    ticket_id = result["ticket"]["ticket_id"]

    with get_connection(test_db) as connection:
        audit = connection.execute(
            """
            SELECT actor, action, entity_type, entity_id
            FROM audit_log
            WHERE entity_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    assert audit is not None
    assert audit["action"] == "ticket_created"
    assert audit["entity_type"] == "support_ticket"
    assert audit["entity_id"] == ticket_id