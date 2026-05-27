"""Model routing for local AI Escape MRC SDK calls.

Local LangGraph execution goes through ``claude_agent_sdk``. By default we do
not set ``ClaudeAgentOptions.model`` so the SDK/CLI uses the model selected by
the user's current Claude/Codex environment.
"""
from __future__ import annotations


ENVIRONMENT_DEFAULT_MODEL_LABEL = "environment-default"


def model_for_role(role: str) -> None:
    """Return no explicit model override for every local LangGraph role.

    The ``role`` argument is kept so phase code can stay descriptive. Returning
    ``None`` means "use the active CLI/session model", avoiding stale hardcoded
    model IDs and avoiding API-key-only model discovery in local runs.
    """
    return None


def model_label(model: str | None) -> str:
    """Human-readable model label for progress/log metadata."""
    return model or ENVIRONMENT_DEFAULT_MODEL_LABEL
