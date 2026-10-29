from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"


def load_documents(directory: str | Path | None = None) -> list[dict]:
    """Load Markdown and text documents from a directory."""

    source_dir = (
        Path(directory)
        if directory is not None
        else DEFAULT_KNOWLEDGE_DIR
    )

    if not source_dir.exists():
        return []

    documents = []

    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue

        text = path.read_text(encoding="utf-8").strip()

        if text:
            documents.append(
                {
                    "source": path.relative_to(source_dir).as_posix(),
                    "text": text,
                }
            )

    return documents


def split_documents(
    documents: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[dict]:
    """Split documents into overlapping character-based chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size."
        )

    chunks = []
    step = chunk_size - chunk_overlap

    for document in documents:
        text = document["text"]
        source = document["source"]

        for start in range(0, len(text), step):
            chunk_text = text[start : start + chunk_size].strip()

            if chunk_text:
                chunks.append(
                    {
                        "source": source,
                        "text": chunk_text,
                        "chunk_index": len(
                            [
                                item for item in chunks
                                if item["source"] == source
                            ]
                        ),
                    }
                )

    return chunks