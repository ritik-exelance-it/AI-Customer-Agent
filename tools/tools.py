from types import SimpleNamespace

import pytest

from database.schema import initialize_database
from tools import customer_tools, ticket_tools


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    """Create an isolated database containing fictional demo records."""

    db_path = tmp_path / "test_support.db"

    initialize_database(
        db_path=str(db_path),
        seed_demo_data=True,
    )

    # Make the decorated LangChain tools use the temporary database.
    test_settings = SimpleNamespace(
        database_path=str(db_path),
    )

    monkeypatch.setattr(
        customer_tools,
        "get_settings",
        lambda: test_settings,
    )

    monkeypatch.setattr(
        ticket_tools,
        "get_settings",
        lambda: test_settings,
    )

    return str(db_path)


def test_find_existing_customer(demo_database):
    result = customer_tools.find_customer(
        "CUST-1001",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["customer"]["full_name"] == "Alex Morgan"
    assert result["customer"]["account_status"] == "active"
    assert "email" not in result["customer"]


def test_find_missing_customer(demo_database):
    result = customer_tools.find_customer(
        "CUST-9999",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert result["error"] == "Customer not found."


def test_customer_lookup_tool(demo_database):
    result = customer_tools.lookup_customer.invoke(
        {"customer_id": "CUST-1001"}
    )

    assert result["ok"] is True
    assert result["customer"]["customer_id"] == "CUST-1001"


def test_find_existing_ticket(demo_database):
    result = ticket_tools.find_ticket(
        "TICK-2001",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["ticket"]["status"] == "open"
    assert result["ticket"]["customer_id"] == "CUST-1001"


def test_find_customer_tickets(demo_database):
    result = ticket_tools.find_customer_tickets(
        "CUST-1001",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["count"] == 2
    assert all(
        ticket["ticket_id"] in {"TICK-2001", "TICK-2002"}
        for ticket in result["tickets"]
    )


def test_find_tickets_for_unknown_customer(demo_database):
    result = ticket_tools.find_customer_tickets(
        "CUST-9999",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert result["error"] == "Customer not found."


def test_update_ticket_status(demo_database):
    result = ticket_tools.change_ticket_status(
        ticket_id="TICK-2001",
        new_status="resolved",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["ticket"]["status"] == "resolved"

    # Verify the updated status persisted in the database.
    updated = ticket_tools.find_ticket(
        "TICK-2001",
        db_path=demo_database,
    )

    assert updated["ticket"]["status"] == "resolved"


def test_reject_invalid_ticket_status(demo_database):
    result = ticket_tools.change_ticket_status(
        ticket_id="TICK-2001",
        new_status="random_status",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert "Invalid status" in result["error"]


def test_update_unknown_ticket(demo_database):
    result = ticket_tools.change_ticket_status(
        ticket_id="TICK-9999",
        new_status="resolved",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert result["error"] == "Ticket not found."


def test_ticket_tool(demo_database):
    result = ticket_tools.get_support_ticket.invoke(
        {"ticket_id": "TICK-2001"}
    )

    assert result["ok"] is True
    assert result["ticket"]["ticket_id"] == "TICK-2001"


def test_ticket_update_tool(demo_database):
    result = ticket_tools.update_support_ticket_status.invoke(
        {
            "ticket_id": "TICK-2001",
            "new_status": "in_progress",
        }
    )

    assert result["ok"] is True
    assert result["ticket"]["status"] == "in_progress"