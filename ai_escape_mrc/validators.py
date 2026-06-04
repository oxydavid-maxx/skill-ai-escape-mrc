# WIKI-CONSULTED: silent-staleness#three-layer-defense
# WIKI-FINDING: Output validation is layer 2 of the silent-staleness defense:
#   detect degraded output before it propagates to downstream consumers.
#   Phase 9 can silently emit a too-short or structurally invalid plan.md;
#   without this check the FSM transitions to Phase 10 with a broken artifact.
# WIKI-ACTION: validate_phase9_plan() asserts size + structural markers before
#   the FSM is allowed to transition; raises typed exception on failure so the
#   caller can emit a fail-closed gate artifact (R13 compliant; no degraded warning).
"""Output-contract validators for AI Escape MRC pipeline phases.

Each validator raises a typed exception (from ai_escape_mrc.errors) on failure.
No degraded-success warnings are emitted (R13 compliance); callers receive
a typed exception and must route to a fail-closed state.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ai_escape_mrc.errors import OutputIdentityContractError, Phase9OutputContractError


#: Minimum acceptable plan.md size in bytes.
PLAN_MIN_BYTES: int = 500

#: Structural markers that must appear in a valid plan.md.
PLAN_REQUIRED_MARKERS: tuple[str, ...] = ("## Task",)

#: This skill's deprecated self-identity tokens. Unambiguous internals — no
#: other skill uses them — so they are auto-sanitized (NOT raised on). The
#: live-sibling-colliding `skill-8d-mrc` is intentionally ABSENT: it names a
#: real workspace skill and is never auto-acted (warn only via the sanitizer).
FORBIDDEN_LEGACY_IDENTITY_TERMS: tuple[str, ...] = (
    "run_8d",
    "trigger_8d",
    "eightd",
    "8d-reports",
    "pending-8d",
    "CLAUDE_EIGHTD",
)

#: Canonical rename map. Ordered: prefixed/longer tokens before bare ones so a
#: partial rewrite can never happen (e.g. `eightd-` consumed before bare
#: `eightd`). Targets contain none of the sources → sanitize is idempotent.
LEGACY_IDENTITY_RENAME_MAP: tuple[tuple[str, str], ...] = (
    ("run_8d", "run_ai_escape_mrc"),
    ("trigger_8d", "trigger_ai_escape_mrc"),
    ("8d-reports", "ai-escape-mrc-reports"),
    ("pending-8d", "pending-ai-escape-mrc"),
    ("CLAUDE_EIGHTD", "CLAUDE_AI_ESCAPE_MRC"),
    ("eightd-", "aem-"),  # CLI prefix form, before bare 'eightd'
    ("eightd", "aem"),    # bare
)

#: Ambiguous token: names a LIVE sibling skill. Never auto-rewritten; warn only.
AMBIGUOUS_IDENTITY_TERM = "skill-8d-mrc"


def sanitize_legacy_identity(text: str) -> str:
    """Idempotently rewrite this skill's deprecated self-identity tokens to the
    active identity, on word boundaries (no substring corruption).

    The ambiguous ``skill-8d-mrc`` (a live sibling skill) is never rewritten —
    only a non-blocking ``stderr`` warn is emitted if present. This is the
    sanitize-then-proceed replacement for the former run-killing raise path:
    callers always receive clean text and never an exception.
    """
    if not text:
        return text
    if AMBIGUOUS_IDENTITY_TERM in text:
        sys.stderr.write(
            f"[WARN] sanitize_legacy_identity: {AMBIGUOUS_IDENTITY_TERM!r} present; "
            "left unchanged (live sibling skill; not auto-rewritten)\n"
        )
    out = text
    for old, new in LEGACY_IDENTITY_RENAME_MAP:
        if old.endswith("-"):
            # Prefix token: boundary before, the literal hyphen is part of 'old'.
            out = re.sub(r"\b" + re.escape(old), new, out)
        else:
            out = re.sub(r"\b" + re.escape(old) + r"\b", new, out)
    return out


def legacy_identity_instruction(*, include_legacy_terms: bool = False) -> str:
    """Return generation guidance for the active skill identity.

    Generated artifacts must not include deprecated token literals anywhere,
    even inside a "check this denylist" command. The default generation prompt
    therefore avoids enumerating the forbidden terms; the deterministic
    validator below owns the exact denylist.
    """
    text = (
        "Active skill identity: AI Escape MRC. Use `skills/skill-ai-escape-mrc`, "
        "`ai_escape_mrc`, `run_ai_escape_mrc.py`, and `trigger_ai_escape_mrc.py`. "
        "Do not quote, enumerate, grep for, or otherwise emit deprecated identity "
        "token literals in generated reports, plans, self-review checklists, or "
        "commands. Refer to the runtime legacy-identity validator if a check is "
        "needed."
    )
    if include_legacy_terms:
        terms = ", ".join(f"`{term}`" for term in FORBIDDEN_LEGACY_IDENTITY_TERMS)
        text += f" Runtime validator denylist: {terms}."
    return text


def validate_no_legacy_identity_terms(text: str, *, artifact_name: str) -> None:
    """Fail generated artifacts that regress to the old skill identity."""
    for term in FORBIDDEN_LEGACY_IDENTITY_TERMS:
        if term in text:
            raise OutputIdentityContractError(
                f"{artifact_name} contains legacy identity term: {term!r}",
                predicate=f"legacy_identity:{term}",
            )


def validate_action_payload(payload, *, artifact_name: str) -> None:
    """Validate any phase output payload (dict/list/str) for legacy identity terms.

    JSON-serializes dict/list inputs so nested keys, list entries, embedded
    command strings, and rationales are all surfaced to the underlying
    `validate_no_legacy_identity_terms` denylist check. Strings pass through.
    Used by phase_4 / phase_5 LLM-call wrappers as a producer-side gate;
    raising here forces a one-shot retry with a named critique, and a second
    failure propagates as `OutputIdentityContractError` (fail-closed).
    """
    import json
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, ensure_ascii=False)
    else:
        text = str(payload)
    validate_no_legacy_identity_terms(text, artifact_name=artifact_name)


def validate_phase9_plan(
    plan_path: Path,
    *,
    min_bytes: int = PLAN_MIN_BYTES,
    required_markers: tuple[str, ...] = PLAN_REQUIRED_MARKERS,
) -> None:
    """Assert plan.md meets the Phase 9 output contract.

    Checks (in order):
    1. File exists at ``plan_path``.
    2. File size > ``min_bytes``.
    3. Content contains every marker in ``required_markers``.

    Raises:
        Phase9OutputContractError: on the first failing predicate.
            The ``predicate`` attribute names the check that failed.

    Args:
        plan_path: Path to the plan.md file produced by Phase 9.
        min_bytes: Minimum acceptable file size in bytes (default 500).
        required_markers: Tuple of strings that must appear in the content.
    """
    plan_path = Path(plan_path)

    # Predicate 1: file exists
    if not plan_path.exists():
        raise Phase9OutputContractError(
            f"plan.md not found at {plan_path}",
            predicate="file_exists",
        )

    # Predicate 2: size check
    size = plan_path.stat().st_size
    if size < min_bytes:
        raise Phase9OutputContractError(
            f"plan.md too small: {size} bytes < {min_bytes} bytes threshold",
            predicate="min_size",
        )

    # Predicate 3: structural markers
    content = plan_path.read_text(encoding="utf-8")
    validate_no_legacy_identity_terms(content, artifact_name=str(plan_path))
    for marker in required_markers:
        if marker not in content:
            raise Phase9OutputContractError(
                f"plan.md missing required marker: {marker!r}",
                predicate=f"marker:{marker}",
            )
