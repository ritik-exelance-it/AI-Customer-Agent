"""Validate and import people CSV into the additive people directory table.

Usage:
  python scripts/import_people.py --csv people_demo_seed.csv --dry-run
  python scripts/import_people.py --csv people_demo_seed.csv --apply

Rows with existing person_id or email are skipped. This importer never creates
customer accounts, tickets, credentials, or permissions. Roles default to
unassigned; assign roles only after confirming each person's purpose.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings
from database.connection import get_connection
from database.people_schema import initialize_people_schema

ALLOWED_ROLES = {"unassigned", "customer", "support_agent", "manager", "escalation_contact", "employee"}
REQUIRED = {"person_id", "full_name", "email"}

def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        rows = []
        seen_ids, seen_emails = set(), set()
        for line, raw in enumerate(reader, start=2):
            row = {key: (value or "").strip() for key, value in raw.items()}
            if not row.get("person_id") or not row.get("full_name") or not row.get("email"):
                raise ValueError(f"Line {line}: person_id, full_name, and email are required.")
            email = row["email"].lower()
            if not re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", email):
                raise ValueError(f"Line {line}: invalid email format.")
            if row["person_id"] in seen_ids or email in seen_emails:
                raise ValueError(f"Line {line}: duplicate ID or email inside the CSV.")
            seen_ids.add(row["person_id"]); seen_emails.add(email)
            role = row.get("role") or "unassigned"
            if role not in ALLOWED_ROLES:
                raise ValueError(f"Line {line}: unsupported role {role!r}.")
            row["email"] = email
            row["role"] = role
            rows.append(row)
    return rows

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Commit validated rows to the database.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing (default).")
    args = parser.parse_args()
    rows = load_rows(args.csv)
    initialize_people_schema(get_settings().database_path)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(get_settings().database_path) as conn:
        existing_ids = {r[0] for r in conn.execute("SELECT person_id FROM people")}
        existing_emails = {r[0].lower() for r in conn.execute("SELECT email FROM people")}
        ready = [r for r in rows if r["person_id"] not in existing_ids and r["email"] not in existing_emails]
        print(f"Validated: {len(rows)} | New rows: {len(ready)} | Existing rows to skip: {len(rows)-len(ready)}")
        for row in ready[:10]:
            print(f"  {row['person_id']} | {row['full_name']} | {row['role']} | {row['email']}")
        if not args.apply:
            print("Dry run only. Re-run with --apply to commit these records.")
            return 0
        conn.executemany(
            """INSERT INTO people
               (person_id, full_name, email, phone, role, department, city,
                organization, record_type, is_demo, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(r["person_id"], r["full_name"], r["email"], r.get("phone") or None,
              r["role"], r.get("department") or None, r.get("city") or None,
              r.get("organization") or None, r.get("record_type") or "person",
              1 if r.get("is_demo", "true").lower() in {"1","true","yes"} else 0,
              now, now) for r in ready]
        )
        print(f"Imported {len(ready)} people into the people table.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
