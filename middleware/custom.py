"""Small reusable input/output safety helpers."""

from __future__ import annotations

import re


# Used only for display/log sanitization. Never treat this as a full DLP system.
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
)


def redact_secrets(text: str) -> str:
    """Redact common credential-like strings before displaying diagnostic text."""
    result = str(text)
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def safe_error_message() -> str:
    """Return a stable user-facing error without leaking exception details."""
    return "Something went wrong while processing your request. Please try again or contact human support."
