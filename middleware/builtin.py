"""Application-level guardrail entry points."""

from middleware.policies import PolicyDecision, requires_human_review, validate_user_message


def evaluate_incoming_message(message: str) -> tuple[PolicyDecision, PolicyDecision]:
    """Run basic validation and human-review policy checks in a predictable order."""
    validation = validate_user_message(message)
    if not validation.allowed:
        return validation, PolicyDecision(False, reason="Human-review policy skipped because input validation failed.")
    return validation, requires_human_review(message)
