import math
import re
from collections import Counter

from knowledge.loader import load_documents, split_documents


def tokenize(text: str) -> list[str]:
    """Convert text into lowercase word tokens."""

    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


def search_documents(
    query: str,
    directory: str | None = None,
    top_k: int = 4,
) -> list[dict]:
    """Retrieve the most relevant document chunks for a query."""

    if not query or not query.strip():
        return []

    if top_k <= 0:
        return []

    documents = load_documents(directory)
    chunks = split_documents(documents)

    if not chunks:
        return []

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    tokenized_chunks = [
        tokenize(chunk["text"])
        for chunk in chunks
    ]

    document_count = len(chunks)
    average_length = (
        sum(len(tokens) for tokens in tokenized_chunks) / document_count
    )

    document_frequencies = Counter()

    for tokens in tokenized_chunks:
        document_frequencies.update(set(tokens))

    k1 = 1.5
    b = 0.75
    scored_results = []

    for chunk, tokens in zip(chunks, tokenized_chunks):
        term_frequencies = Counter(tokens)
        document_length = len(tokens)
        score = 0.0

        for term in query_tokens:
            frequency = term_frequencies[term]

            if frequency == 0:
                continue

            document_frequency = document_frequencies[term]

            inverse_document_frequency = math.log(
                1
                + (
                    document_count - document_frequency + 0.5
                )
                / (document_frequency + 0.5)
            )

            denominator = frequency + k1 * (
                1 - b + b * document_length / max(average_length, 1)
            )

            score += (
                inverse_document_frequency
                * frequency
                * (k1 + 1)
                / denominator
            )

        if score > 0:
            scored_results.append(
                {
                    **chunk,
                    "score": round(score, 4),
                }
            )

    scored_results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    return scored_results[:top_k]