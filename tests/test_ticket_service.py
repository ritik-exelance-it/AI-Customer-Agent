from types import SimpleNamespace

import pytest

from database.connection import get_connection
from database.schema import initialize_database
from services import ticket_service


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create an isolated database with fictional demo customers."""
    db_path = tmp_path / "tickets_test.db"

    initialize_database(
        db_path=str(db_path),
        seed_demo_data=True,
    )

    settings = SimpleNamespace(database_path=str(db_path))

    monkeypatch.setattr(
        ticket_service,
        "get_settings",
        lambda: settings,
    )

    return str(db_path)


def test_ticket_creation_requires_confirmation(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject="Login issue",
        description="Cannot log into the application.",
    )

    assert result["ok"] is False
    assert "confirmation" in result["error"].lower()


def test_create_ticket_success(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject="Login issue",
        description="Cannot log into the application.",
        priority="high",
        confirmed=True,
        actor="test_agent",
    )

    assert result["ok"] is True
    assert result["ticket"]["customer_id"] == "CUST-1001"
    assert result["ticket"]["subject"] == "Login issue"
    assert result["ticket"]["priority"] == "high"
    assert result["ticket"]["status"] == "open"
    assert result["ticket"]["ticket_id"].startswith("TICK-")


def test_unknown_customer_is_rejected(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-9999",
        subject="Login issue",
        description="Cannot log in.",
        confirmed=True,
    )

    assert result["ok"] is False
    assert result["error"] == "Customer not found."


def test_invalid_priority_is_rejected(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject="Login issue",
        description="Cannot log in.",
        priority="critical-but-invalid",
        confirmed=True,
    )

    assert result["ok"] is False
    assert "priority" in result["error"].lower()


def test_empty_subject_is_rejected(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject=" ",
        description="Cannot log in.",
        confirmed=True,
    )

    assert result["ok"] is False
    assert "subject" in result["error"].lower()


def test_ticket_creation_writes_audit_record(test_db):
    result = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject="Billing question",
        description="I have a question about my bill.",
        confirmed=True,
        actor="test_agent",
    )

    assert result["ok"] is True
    ticket_id = result["ticket"]["ticket_id"]

    with get_connection(test_db) as conn:
        audit = conn.execute(
            """
            SELECT actor, action, entity_id
            FROM audit_log
            WHERE entity_type = 'support_ticket'
              AND entity_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    assert audit is not None
    assert audit["actor"] == "test_agent"
    assert audit["action"] == "ticket_created"


def test_get_support_ticket(test_db):
    created = ticket_service.create_support_ticket(
        customer_id="CUST-1001",
        subject="Test ticket",
        description="Testing ticket lookup.",
        confirmed=True,
    )

    result = ticket_service.get_support_ticket(
        created["ticket"]["ticket_id"]
    )

    assert result["ok"] is True
    assert result["ticket"]["subject"] == "Test ticket"


def test_get_missing_ticket(test_db):
    result = ticket_service.get_support_ticket("TICK-NOT-FOUND")

    assert result["ok"] is False
    assert result["error"] == "Ticket not found."