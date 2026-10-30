"""SQLite-backed LangGraph checkpoint persistence.

Use a stable ``thread_id`` in graph config for each conversation. Checkpoints
are application state; user-visible message history is stored separately in
``database.repositories.conversations``.
"""
from __future__ import annotations

import atexit
import os
from contextlib import AbstractContextManager
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import get_settings

_manager: AbstractContextManager[Any] | None = None


def _configured_checkpoint_path() -> str:
    """Resolve the current checkpoint setting with the legacy override."""
    return os.getenv("SUPPORT_CHECKPOINT_DB_PATH") or get_settings().checkpoint_path


@lru_cache(maxsize=1)
def get_checkpointer():
    """Return a process-wide SQLite saver, keeping its connection open.

    If the optional SQLite checkpoint package is not installed yet, return
    ``None`` so importing the graph remains possible during staged setup. The
    application should install requirements.txt before relying on persistence.
    """
    global _manager
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError:
        return None

    raw_path = _configured_checkpoint_path()
    path = Path(raw_path).expanduser()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    _manager = SqliteSaver.from_conn_string(str(path))
    saver = _manager.__enter__()
    atexit.register(_close_checkpointer)
    return saver


def _close_checkpointer() -> None:
    """Close the saver connection at process shutdown."""
    global _manager
    if _manager is not None:
        try:
            _manager.__exit__(None, None, None)
        finally:
            _manager = None
            get_checkpointer.cache_clear()
