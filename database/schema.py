"""Idempotent SQLite schema initialization and fictional demo data."""
from __future__ import annotations

from datetime import datetime, timezone

from database.connection import get_connection


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_database(
    db_path: str | None = None,
    seed_demo_data: bool = False,
) -> None:
    """Create application tables without deleting existing records.

    Safe to run repeatedly. Existing customers and support tickets remain
    compatible with the original project schema.
    """
    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                account_status TEXT NOT NULL CHECK (
                    account_status IN ('active', 'inactive', 'suspended')
                ),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('open', 'in_progress', 'resolved', 'closed')
                ),
                priority TEXT NOT NULL CHECK (
                    priority IN ('low', 'medium', 'high', 'urgent')
                ),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_customer_id
                ON support_tickets(customer_id);
            CREATE INDEX IF NOT EXISTS idx_tickets_status
                ON support_tickets(status);

            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                customer_id TEXT,
                title TEXT NOT NULL DEFAULT 'Support conversation',
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'resolved', 'escalated', 'archived')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_customer_id
                ON conversations(customer_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                ON conversations(updated_at);

            CREATE TABLE IF NOT EXISTS conversation_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('system', 'user', 'assistant', 'tool', 'human')
                ),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON conversation_messages(conversation_id, message_id);

            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                customer_id TEXT,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'assigned', 'resolved', 'cancelled')),
                assigned_to TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolution_note TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_escalations_status
                ON escalations(status, created_at);

            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_entity
                ON audit_log(entity_type, entity_id, created_at);
            """
        )

        if seed_demo_data:
            now = _utc_now()
            connection.executemany(
                """INSERT OR IGNORE INTO customers
                   (customer_id, full_name, email, account_status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    ("CUST-1001", "Alex Morgan", "alex@example.com", "active", now),
                    ("CUST-1002", "Jordan Lee", "jordan@example.com", "active", now),
                    ("CUST-1003", "Taylor Smith", "taylor@example.com", "inactive", now),
                ],
            )
            connection.executemany(
                """INSERT OR IGNORE INTO support_tickets
                   (ticket_id, customer_id, subject, description, status, priority,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    ("TICK-2001", "CUST-1001", "Unable to log in",
                     "The customer cannot access their account.", "open", "high", now, now),
                    ("TICK-2002", "CUST-1001", "Billing question",
                     "The customer needs help understanding an invoice.", "in_progress", "medium", now, now),
                    ("TICK-2003", "CUST-1002", "Order delivery delay",
                     "The customer's order has not arrived.", "open", "urgent", now, now),
                ],
            )
