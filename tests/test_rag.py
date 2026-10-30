from knowledge.loader import load_documents, split_documents
from knowledge.retriever import search_documents
from tools.knowledge_tools import search_knowledge_base


def test_load_markdown_document(tmp_path):
    (tmp_path / "faq.md").write_text(
        "# Password Reset\nUse Forgot Password to reset your password.",
        encoding="utf-8",
    )

    documents = load_documents(str(tmp_path))

    assert len(documents) == 1
    assert documents[0]["source"] == "faq.md"
    assert "Forgot Password" in documents[0]["text"]


def test_ignore_unsupported_files(tmp_path):
    (tmp_path / "faq.md").write_text(
        "Password reset help.",
        encoding="utf-8",
    )
    (tmp_path / "image.png").write_bytes(b"not a real image")

    documents = load_documents(str(tmp_path))

    assert len(documents) == 1
    assert documents[0]["source"] == "faq.md"


def test_split_document_into_overlapping_chunks():
    documents = [
        {
            "source": "long.txt",
            "text": "A" * 100,
        }
    ]

    chunks = split_documents(
        documents,
        chunk_size=40,
        chunk_overlap=10,
    )

    assert len(chunks) == 3
    assert chunks[0]["text"][-10:] == chunks[1]["text"][:10]
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


def test_retrieve_relevant_document(tmp_path):
    (tmp_path / "passwords.md").write_text(
        "To reset a password, select Forgot Password on the sign-in page.",
        encoding="utf-8",
    )
    (tmp_path / "delivery.md").write_text(
        "Delivery tracking provides updates about delayed shipments.",
        encoding="utf-8",
    )

    results = search_documents(
        query="How do I reset my password?",
        directory=str(tmp_path),
    )

    assert results
    assert results[0]["source"] == "passwords.md"
    assert results[0]["score"] > 0


def test_empty_query_returns_no_results(tmp_path):
    results = search_documents(
        query="   ",
        directory=str(tmp_path),
    )

    assert results == []


def test_no_matching_documents_returns_empty_list(tmp_path):
    (tmp_path / "faq.md").write_text(
        "The delivery team tracks shipments.",
        encoding="utf-8",
    )

    results = search_documents(
        query="quantum astronomy",
        directory=str(tmp_path),
    )

    assert results == []


def test_knowledge_tool_returns_sources():
    result = search_knowledge_base.invoke(
        {"query": "How do customers reset passwords?"}
    )

    assert result["ok"] is True
    assert result["results"]

    assert any(
        item["source"] == "faq.md"
        for item in result["results"]
    )