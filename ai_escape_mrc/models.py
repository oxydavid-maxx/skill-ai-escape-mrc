"""Model routing for local AI Escape MRC SDK calls.

Local LangGraph execution goes through ``claude_agent_sdk``. By default we do
not set ``ClaudeAgentOptions.model`` so the SDK/CLI uses the model selected by
the user's current Claude/Codex environment.
"""
from __future__ import annotations

import os

ENVIRONMENT_DEFAULT_MODEL_LABEL = "environment-default"

# Quality-bearing roles that MUST stay on the strong session-default model.
# The audits are the core reasoning; they re-examine earlier phases' output, so
# they also act as a safety net when cheaper phases run on a faster model.
_STRONG_ROLES = frozenset({
    "rc_audit",
    "prevention_audit",
    "report_generation",
})

# Opt-in only: set CLAUDE_AI_ESCAPE_MRC_FAST_MODEL to a model id (e.g. a Sonnet
# id) to route every NON-strong role to it. Unset -> no override (every role
# uses the session default, i.e. the original behavior). Kept as an env var
# rather than a hardcoded id to avoid stale model-id drift.
_FAST_MODEL_ENV = "CLAUDE_AI_ESCAPE_MRC_FAST_MODEL"


def model_for_role(role: str) -> str | None:
    """Return an explicit model override for a role, or ``None`` for default.

    Returns ``None`` (use the active CLI/session strong model) for the audit /
    report roles, and for ALL roles when the operator has not opted in. When
    ``CLAUDE_AI_ESCAPE_MRC_FAST_MODEL`` is set, every non-strong (structural /
    first-pass-reasoning) role is routed to that faster model to cut runtime
    while the audits keep the strong model and re-check their output.
    """
    if role in _STRONG_ROLES:
        return None
    fast = (os.environ.get(_FAST_MODEL_ENV) or "").strip()
    return fast or None


def model_label(model: str | None) -> str:
    """Human-readable model label for progress/log metadata."""
    return model or ENVIRONMENT_DEFAULT_MODEL_LABEL
