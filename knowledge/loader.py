"""Load local support documents and split them into traceable chunks."""

from __future__ import annotations

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
SUPPORTED_SUFFIXES = {".md", ".txt"}


def load_documents(directory: str | Path | None = None) -> list[dict]:
    """Load UTF-8 Markdown/text files using stable relative source names."""
    source_dir = Path(directory) if directory is not None else DEFAULT_KNOWLEDGE_DIR
    if not source_dir.exists() or not source_dir.is_dir():
        return []

    documents = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8-sig").strip()
        except (OSError, UnicodeError):
            # One unreadable file should not make the entire knowledge base unusable.
            continue
        if content:
            documents.append({"source": path.relative_to(source_dir).as_posix(), "text": content})
    return documents


def split_documents(
    documents: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[dict]:
    """Split documents into overlapping chunks, preferring paragraph boundaries.

    Character-based chunk sizes keep this component dependency-light. Chunk IDs
    are stable within a source file for a fixed file version and configuration.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size.")

    chunks: list[dict] = []
    step = chunk_size - chunk_overlap
    for document in documents:
        source = str(document.get("source", "unknown"))
        text = str(document.get("text", "")).strip()
        if not text:
            continue
        source_index = 0
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                # Avoid cutting mid-paragraph when a boundary is nearby.
                boundary = text.rfind("\n\n", start + chunk_size // 2, end)
                if boundary > start + chunk_size // 2:
                    end = boundary
            excerpt = text[start:end].strip()
            if excerpt:
                chunks.append({"source": source, "text": excerpt, "chunk_index": source_index})
                source_index += 1
            if end >= len(text):
                break
            # Use overlap from the chosen end boundary rather than the original target.
            start = max(start + 1, end - chunk_overlap)
    return chunks
