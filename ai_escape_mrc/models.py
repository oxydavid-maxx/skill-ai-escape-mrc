"""Model routing for local AI Escape MRC SDK calls.

Local LangGraph execution goes through ``claude_agent_sdk``. By default we do
not set ``ClaudeAgentOptions.model`` so the SDK/CLI uses the model selected by
the user's current Claude/Codex environment.
"""
from __future__ import annotations

import os

ENVIRONMENT_DEFAULT_MODEL_LABEL = "environment-default"

# Roles whose output is low-stakes/structural — they only feed web-search
# queries or coarse categorization, never the final report prose or the audits.
# These may safely run on a faster model without changing report depth.
# Everything else (is_isnt, why_*, audits, actions, verification, report,
# plan) stays on the session default (strong) model.
_FAST_ROLES = frozenset({
    "keyword_extraction",
    "meta_categorization",
    "simple_classification",
})

# Opt-in only: set CLAUDE_AI_ESCAPE_MRC_FAST_MODEL to a model id (e.g. a Haiku
# or Sonnet id) to route the structural roles to it. Unset -> no override
# (every role uses the session default, i.e. the original behavior). Kept as an
# env var rather than a hardcoded id to avoid stale model-id drift.
_FAST_MODEL_ENV = "CLAUDE_AI_ESCAPE_MRC_FAST_MODEL"


def model_for_role(role: str) -> str | None:
    """Return an explicit model override for a role, or ``None`` for default.

    Returns ``None`` (use the active CLI/session model) for every role unless
    BOTH (a) ``role`` is a low-stakes structural role and (b) the operator has
    opted in via ``CLAUDE_AI_ESCAPE_MRC_FAST_MODEL``. This keeps the strong
    model on all quality-bearing phases while letting cheap phases run faster.
    """
    if role in _FAST_ROLES:
        fast = (os.environ.get(_FAST_MODEL_ENV) or "").strip()
        if fast:
            return fast
    return None


def model_label(model: str | None) -> str:
    """Human-readable model label for progress/log metadata."""
    return model or ENVIRONMENT_DEFAULT_MODEL_LABEL
