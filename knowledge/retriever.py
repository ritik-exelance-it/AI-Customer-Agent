"""Dependency-light lexical retrieval for the local support knowledge base.

This is BM25-style retrieval with small exact-phrase and title/heading boosts.
It is not semantic embedding retrieval; that can be added as a separate index.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from knowledge.loader import load_documents, split_documents

_TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Normalize text into lowercase Unicode-aware word tokens."""
    return [token.casefold() for token in _TOKEN_PATTERN.findall(text or "")]


def _heading_text(text: str) -> str:
    return " ".join(line.lstrip("# ").strip() for line in text.splitlines() if line.lstrip().startswith("#"))


def search_documents(
    query: str,
    directory: str | Path | None = None,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Return the best lexical matches with source and chunk metadata."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []

    chunks = split_documents(load_documents(directory))
    if not chunks:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    tokenized = [tokenize(chunk["text"]) for chunk in chunks]
    n_docs = len(chunks)
    avg_len = sum(map(len, tokenized)) / max(n_docs, 1)
    doc_freq = Counter()
    for tokens in tokenized:
        doc_freq.update(set(tokens))

    k1, b = 1.5, 0.75
    query_phrase = " ".join(query_tokens)
    scored: list[dict[str, Any]] = []
    for chunk, tokens in zip(chunks, tokenized):
        tf = Counter(tokens)
        length = len(tokens)
        score = 0.0
        for term in set(query_tokens):
            frequency = tf[term]
            if not frequency:
                continue
            df = doc_freq[term]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / max(avg_len, 1))
            score += idf * frequency * (k1 + 1) / denominator

        content = chunk["text"].casefold()
        if query_phrase and len(query_tokens) > 1 and query_phrase in " ".join(tokens):
            score += 1.0
        headings = tokenize(_heading_text(chunk["text"]))
        heading_overlap = len(set(query_tokens).intersection(headings))
        score += 0.35 * heading_overlap
        if score > 0:
            scored.append({**chunk, "score": round(score, 4)})

    scored.sort(key=lambda item: (-item["score"], item["source"], item["chunk_index"]))
    return scored[:top_k]
