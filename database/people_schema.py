"""Additive schema migration for generic people directory."""
from __future__ import annotations

from database.connection import get_connection


def initialize_people_schema(db_path: str | None = None) -> None:
    """Create people table and indexes without changing existing customer records."""
    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS people (
                person_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'unassigned'
                    CHECK (role IN ('unassigned', 'customer', 'support_agent', 'manager', 'escalation_contact', 'employee')),
                department TEXT,
                city TEXT,
                organization TEXT,
                record_type TEXT NOT NULL DEFAULT 'person',
                is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_people_name ON people(full_name);
            CREATE INDEX IF NOT EXISTS idx_people_role ON people(role);
            """
        )
