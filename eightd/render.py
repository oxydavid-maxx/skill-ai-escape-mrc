# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: Phase 10 gate emission must be deterministic — never depend on LLM output.
#   The render helper builds a minimal plan header from structured action data alone,
#   so gate-file writing can succeed even when call_claude() is unavailable or fails.
# WIKI-ACTION: render_plan_header() is pure-Python with no LLM dependency; used as
#   a fallback header source in test assertions to prove Phase 10 independence.
"""Deterministic plan rendering helpers — no LLM dependency.

These utilities produce plan.md skeleton content from structured action dicts.
Phase 10 (gate-file emission) must remain independent of Phase 9's LLM call quality;
render_plan_header() makes that invariant testable.

WIKI-EXEMPT: silent-staleness — this module has no staleness surface (pure computation).
"""
from __future__ import annotations

from typing import Sequence


def render_plan_header(actions: Sequence[dict], topic: str = "") -> str:
    """Build a minimal plan Markdown header from action dicts — no LLM call.

    Produces the `# <topic> Implementation Plan` header plus one `## Task N:` line
    per action.  Intended as a deterministic fallback / skeleton renderer for tests
    and as proof that gate-file emission does not require LLM output.

    Args:
        actions: Sequence of action dicts with at least a ``title`` key.
        topic: Human-readable topic string for the plan header.

    Returns:
        A Markdown string suitable as a minimal plan.md skeleton.
    """
    header = f"# {topic or 'Implementation'} Plan\n\n"
    if not actions:
        header += "_No actions provided._\n"
        return header
    lines = []
    for idx, action in enumerate(actions, start=1):
        title = action.get("title") or f"Action {idx}"
        lines.append(f"## Task {idx}: {title}\n")
        desc = action.get("description", "")
        if desc:
            lines.append(f"{desc}\n")
        files = action.get("files_touched") or []
        if files:
            joined = ", ".join(str(f) for f in files)
            lines.append(f"**Files:** {joined}\n")
        lines.append("")
    return header + "\n".join(lines)
