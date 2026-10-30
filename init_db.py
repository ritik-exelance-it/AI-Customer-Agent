"""Initialize the support SQLite database safely for local development."""
from __future__ import annotations

import argparse

from config import get_settings
from database.schema import initialize_database


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed-demo-data",
        action="store_true",
        help="Insert the project's fictional demo customers and tickets if absent.",
    )
    args = parser.parse_args()
    settings = get_settings()
    initialize_database(
        db_path=settings.database_path,
        seed_demo_data=args.seed_demo_data,
    )
    print(f"Database initialized at: {settings.database_path}")
    if args.seed_demo_data:
        print("Fictional demo records inserted where missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
