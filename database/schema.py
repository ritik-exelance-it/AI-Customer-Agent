from datetime import datetime, timezone

from database.connection import get_connection


def initialize_database(
    db_path: str | None = None,
    seed_demo_data: bool = False,
) -> None:
    """Create the database tables and optionally insert demo records."""

    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                account_status TEXT NOT NULL
                    CHECK (
                        account_status IN (
                            'active',
                            'inactive',
                            'suspended'
                        )
                    ),
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'open',
                            'in_progress',
                            'resolved',
                            'closed'
                        )
                    ),
                priority TEXT NOT NULL
                    CHECK (
                        priority IN (
                            'low',
                            'medium',
                            'high',
                            'urgent'
                        )
                    ),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(customer_id)
                    ON DELETE RESTRICT
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_tickets_customer_id
            ON support_tickets(customer_id)
            """
        )

        if seed_demo_data:
            now = datetime.now(timezone.utc).isoformat()

            connection.executemany(
                """
                INSERT OR IGNORE INTO customers (
                    customer_id,
                    full_name,
                    email,
                    account_status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        "CUST-1001",
                        "Alex Morgan",
                        "alex@example.com",
                        "active",
                        now,
                    ),
                    (
                        "CUST-1002",
                        "Jordan Lee",
                        "jordan@example.com",
                        "active",
                        now,
                    ),
                    (
                        "CUST-1003",
                        "Taylor Smith",
                        "taylor@example.com",
                        "inactive",
                        now,
                    ),
                ],
            )

            connection.executemany(
                """
                INSERT OR IGNORE INTO support_tickets (
                    ticket_id,
                    customer_id,
                    subject,
                    description,
                    status,
                    priority,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "TICK-2001",
                        "CUST-1001",
                        "Unable to log in",
                        "The customer cannot access their account.",
                        "open",
                        "high",
                        now,
                        now,
                    ),
                    (
                        "TICK-2002",
                        "CUST-1001",
                        "Billing question",
                        "The customer needs help understanding an invoice.",
                        "in_progress",
                        "medium",
                        now,
                        now,
                    ),
                    (
                        "TICK-2003",
                        "CUST-1002",
                        "Order delivery delay",
                        "The customer's order has not arrived.",
                        "open",
                        "urgent",
                        now,
                        now,
                    ),
                ],
            )