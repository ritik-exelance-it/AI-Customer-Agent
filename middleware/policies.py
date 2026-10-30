"""Deterministic policy checks shared by the agent and application layer.

These checks are guardrails, not a substitute for authentication, authorization,
or human review of high-impact decisions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


MAX_USER_MESSAGE_CHARS = 8_000

HUMAN_REQUEST_PATTERNS = (
    r"\b(speak|talk|connect|transfer)\s+(to\s+)?(a\s+)?human\b",
    r"\b(real|live)\s+(person|agent|representative)\b",
    r"\b(human|manager|supervisor)\s+(support|agent|representative)\b",
)
HIGH_RISK_PATTERNS = (
    r"\b(lawsuit|legal action|attorney|lawyer)\b",
    r"\b(fraud|identity theft|data breach|account compromised)\b",
    r"\b(threaten|threatening|harassment|discrimination)\b",
    r"\b(refund|chargeback)\b.*\b(exception|override|bypass)\b",
)
SUPPORT_SCOPE_PATTERNS = (
    r"\b(account|profile|login|log in|sign in|password|username|access|email|address)\b",
    r"\b(order|purchase|shipping|delivery|tracking|package|return|exchange|cancel|cancellation)\b",
    r"\b(refund|billing|bill|bills|invoice|invoices|statement|statements|receipt|receipts|payment|charge|subscription|pricing|plan)\b",
    r"\b(ticket|case|support|representative)\b",
    r"\b(product|service|feature|app|software|warranty|policy|faq)\b",
    r"\b(troubleshoot|troubleshooting|setup|install|configure|reset|bug|error|crash|outage)\b",
    r"\b(issue|problem|complaint|not working|doesn't work|does not work|can't use|cannot use)\b",
)
SUPPORT_CONVERSATION_PATTERNS = (
    r"\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b",
    r"\b(thanks|thank you|goodbye|bye)\b",
    r"\b(what can you do|what can you help me with|how can you help|who are you)\b",
)
SUPPORT_CLARIFICATION_PATTERNS = (
    r"\b(customer|ticket|order)\s+(id|number|reference)\b",
    r"\bdescribe\b.{0,40}\b(issue|problem|happening|going on)\b",
    r"\bwhat(?:'s| is)\s+going on\b",
    r"\bwhat support issue\b",
    r"\bwhich\s+(account|order|ticket|product)\b",
    r"\bshare\b.{0,30}\b(customer|ticket|order)\b",
)
SUPPORT_FOLLOW_UP_PATTERNS = (
    r"^(?:i am|i'm|my name is)\s+[a-z][a-z .'-]{0,79}[.!?]?$",
    r"^(?:(?:my\s+)?(?:customer\s+)?(?:id|number)\s*(?:is|:)?\s*)"
    r"[a-z0-9][a-z0-9_-]{1,31}[.!?]?$",
    r"^[a-z]{2,10}[-_]\d{2,12}[.!?]?$",
)


@dataclass(frozen=True)
class PolicyDecision:
    """A deterministic policy result that can be shown in logs or the UI."""

    allowed: bool
    requires_human: bool = False
    reason: str | None = None


def validate_user_message(message: str) -> PolicyDecision:
    """Reject empty or excessively long user messages."""
    if not isinstance(message, str) or not message.strip():
        return PolicyDecision(False, reason="Message cannot be empty.")
    if len(message) > MAX_USER_MESSAGE_CHARS:
        return PolicyDecision(
            False,
            reason=f"Message exceeds the {MAX_USER_MESSAGE_CHARS}-character limit.",
        )
    return PolicyDecision(True)


def requires_human_review(message: str) -> PolicyDecision:
    """Detect explicit human requests and common sensitive complaint signals."""
    text = (message or "").strip().lower()
    if not text:
        return PolicyDecision(True, requires_human=True, reason="No usable message was provided.")

    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HUMAN_REQUEST_PATTERNS):
        return PolicyDecision(True, requires_human=True, reason="The customer requested a human representative.")

    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in HIGH_RISK_PATTERNS):
        return PolicyDecision(True, requires_human=True, reason="The issue may require specialist review.")

    return PolicyDecision(True)


def is_in_scope_support_request(
    message: str,
    conversation_context: list[object] | None = None,
) -> bool:
    """Allow support topics and relevant clarification replies, not general Q&A."""
    text = (message or "").strip().casefold()
    if any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in SUPPORT_SCOPE_PATTERNS + SUPPORT_CONVERSATION_PATTERNS
    ):
        return True

    is_support_follow_up = any(
        re.fullmatch(pattern, text, flags=re.IGNORECASE)
        for pattern in SUPPORT_FOLLOW_UP_PATTERNS
    )
    if not is_support_follow_up:
        return False

    latest_assistant = next(
        (
            getattr(item, "content", "")
            for item in reversed(conversation_context or [])
            if getattr(item, "type", None) == "ai"
        ),
        "",
    )
    if not isinstance(latest_assistant, str):
        return False
    return any(
        re.search(pattern, latest_assistant, flags=re.IGNORECASE)
        for pattern in SUPPORT_CLARIFICATION_PATTERNS
    )


def tool_is_allowed(tool_name: str, allowed_tool_names: set[str]) -> bool:
    """Fail closed when a requested tool is not in the current allowlist."""
    return bool(tool_name) and tool_name in allowed_tool_names
