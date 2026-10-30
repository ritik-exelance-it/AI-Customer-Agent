from types import SimpleNamespace

import pytest

from database.schema import initialize_database
from tools import ticket_tools


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    """Prepare an isolated database with fictional demo records."""
    db_path = tmp_path / "ticket_tools_test.db"

    initialize_database(
        db_path=str(db_path),
        seed_demo_data=True,
    )

    settings = SimpleNamespace(database_path=str(db_path))

    monkeypatch.setattr(
        ticket_tools,
        "get_settings",
        lambda: settings,
    )

    return str(db_path)


def test_find_existing_ticket(demo_database):
    result = ticket_tools.find_ticket(
        "TICK-2001",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["ticket"]["ticket_id"] == "TICK-2001"
    assert result["ticket"]["customer_id"] == "CUST-1001"


def test_find_missing_ticket(demo_database):
    result = ticket_tools.find_ticket(
        "TICK-9999",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert result["error"] == "Ticket not found."


def test_find_ticket_requires_id(demo_database):
    result = ticket_tools.find_ticket(
        " ",
        db_path=demo_database,
    )

    assert result["ok"] is False


def test_list_customer_tickets(demo_database):
    result = ticket_tools.find_customer_tickets(
        "CUST-1001",
        db_path=demo_database,
    )

    assert result["ok"] is True
    assert result["count"] == 2


def test_unknown_customer_ticket_list(demo_database):
    result = ticket_tools.find_customer_tickets(
        "CUST-9999",
        db_path=demo_database,
    )

    assert result["ok"] is False
    assert result["error"] == "Customer not found."


def test_get_support_ticket_tool(demo_database):
    result = ticket_tools.get_support_ticket.invoke(
        {"ticket_id": "TICK-2001"}
    )

    assert result["ok"] is True
    assert result["ticket"]["ticket_id"] == "TICK-2001"


def test_list_customer_tickets_tool(demo_database):
    result = ticket_tools.list_customer_tickets.invoke(
        {"customer_id": "CUST-1001"}
    )

    assert result["ok"] is True
    assert result["count"] == 2