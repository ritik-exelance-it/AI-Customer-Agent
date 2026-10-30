"""Validate and import people CSV into the additive people directory table."""
from __future__ import annotations
import argparse, csv, re, sys
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
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV is empty or has no header row.")
        missing = REQUIRED - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        rows, seen_ids, seen_emails = [], set(), set()
        for line, raw in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items() if k is not None}
            person_id, full_name, email = row.get("person_id", ""), row.get("full_name", ""), row.get("email", "").lower()
            if not person_id or not full_name or not email:
                raise ValueError(f"Line {line}: person_id, full_name, and email are required.")
            if not EMAIL_PATTERN.fullmatch(email):
                raise ValueError(f"Line {line}: invalid email format for {email!r}. Expected person@example.com.")
            if person_id in seen_ids:
                raise ValueError(f"Line {line}: duplicate person_id {person_id!r} inside the CSV.")
            if email in seen_emails:
                raise ValueError(f"Line {line}: duplicate email {email!r} inside the CSV.")
            role = row.get("role") or "unassigned"
            if role not in ALLOWED_ROLES:
                raise ValueError(f"Line {line}: unsupported role {role!r}.")
            seen_ids.add(person_id); seen_emails.add(email)
            row.update(person_id=person_id, full_name=full_name, email=email, role=role)
            rows.append(row)
        if not rows:
            raise ValueError("CSV contains a header but no data rows.")
        return rows

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write validated rows to the database.")
    mode.add_argument("--dry-run", action="store_true", help="Preview only (default).")
    args = parser.parse_args()
    try:
        rows = load_rows(args.csv)
        db_path = str(get_settings().database_path)
        initialize_people_schema(db_path)
        now = datetime.now(timezone.utc).isoformat()
        with get_connection(db_path) as conn:
            ids = {r[0] for r in conn.execute("SELECT person_id FROM people")}
            emails = {r[0].strip().lower() for r in conn.execute("SELECT email FROM people")}
            ready = [r for r in rows if r["person_id"] not in ids and r["email"] not in emails]
            print(f"Validated: {len(rows)} | New rows: {len(ready)} | Existing rows to skip: {len(rows)-len(ready)}")
            for r in ready[:10]:
                print(f"  {r['person_id']} | {r['full_name']} | {r['role']} | {r['email']}")
            if not args.apply:
                print("Dry run only; no people records were imported. Re-run with --apply to commit.")
                return 0
            conn.executemany(
                """INSERT INTO people
                (person_id, full_name, email, phone, role, department, city, organization, record_type, is_demo, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(r["person_id"], r["full_name"], r["email"], r.get("phone") or None, r["role"],
                  r.get("department") or None, r.get("city") or None, r.get("organization") or None,
                  r.get("record_type") or "person", 1 if r.get("is_demo", "true").lower() in {"1","true","yes"} else 0,
                  now, now) for r in ready]
            )
            print(f"Imported {len(ready)} people into the people table.")
        return 0
    except (OSError, csv.Error, ValueError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
