from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Iterator

from config import get_settings


@contextmanager
def get_connection(
    db_path: str | Path | None = None,
) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection and close it safely after use."""

    if db_path is None:
        db_path = get_settings().database_path

    database_path = str(db_path)

    # Create the parent directory for normal file-based databases.
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    connection = sqlite3.connect(
        database_path,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()