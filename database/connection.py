"""SQLite connection management for the support application."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from config import get_settings


def _resolve_database_path(db_path: str | Path | None = None) -> str:
    if db_path is None:
        db_path = get_settings().database_path
    return str(db_path)


@contextmanager
def get_connection(
    db_path: str | Path | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Yield a configured SQLite connection and commit/rollback safely.

    A fresh connection is created per operation. File-backed databases get
    parent-directory creation, foreign-key enforcement, and a busy timeout.
    """
    database_path = _resolve_database_path(db_path)
    if database_path != ":memory:":
        Path(database_path).expanduser().resolve().parent.mkdir(
            parents=True, exist_ok=True
        )

    connection = sqlite3.connect(
        database_path,
        timeout=15.0,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")
    if database_path != ":memory:":
        connection.execute("PRAGMA journal_mode = WAL")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
