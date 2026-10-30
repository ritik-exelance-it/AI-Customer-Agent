"""Utilities for displaying and validating knowledge-base source references."""

from __future__ import annotations

from pathlib import PurePosixPath


def normalize_source_name(source: str) -> str:
    """Return a safe relative display name; reject absolute/traversal paths."""
    normalized = (source or "").replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        return "unknown source"
    return path.as_posix()


def format_source_reference(result: dict) -> dict:
    """Convert a retrieval result to the stable shape consumed by the UI."""
    try:
        score = float(result.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    try:
        chunk_index = max(0, int(result.get("chunk_index", 0)))
    except (TypeError, ValueError):
        chunk_index = 0
    return {
        "source": normalize_source_name(str(result.get("source", ""))),
        "chunk_index": chunk_index,
        "score": score,
        "text": str(result.get("text", "")),
    }
