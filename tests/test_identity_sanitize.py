"""Unit + integration tests for the sanitize-not-raise identity path.

Replaces the prior raise-based contract (validate_no_legacy_identity_terms /
validate_action_payload). The identity gate no longer kills a finished run:
deprecated self-identity tokens are idempotently, token-boundary-safely
rewritten to the active identity; the ambiguous `skill-8d-mrc` (a live sibling
skill) is never rewritten, only warned.
"""
from pathlib import Path

from ai_escape_mrc.validators import (
    sanitize_legacy_identity,
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    validate_phase9_plan,
)


# --- Task 1: sanitizer unit tests -------------------------------------------

def test_renames_six_tokens():
    assert sanitize_legacy_identity("run_8d and trigger_8d") == "run_ai_escape_mrc and trigger_ai_escape_mrc"
    assert sanitize_legacy_identity("see 8d-reports/x") == "see ai-escape-mrc-reports/x"
    assert sanitize_legacy_identity("pending-8d") == "pending-ai-escape-mrc"
    assert sanitize_legacy_identity("CLAUDE_EIGHTD=1") == "CLAUDE_AI_ESCAPE_MRC=1"


def test_eightd_prefix_and_bare():
    assert sanitize_legacy_identity("run eightd-closed-loop now") == "run aem-closed-loop now"
    assert sanitize_legacy_identity("the eightd tool") == "the aem tool"


def test_token_boundary_no_substring_corruption():
    # contrived word containing the substring must be untouched
    assert sanitize_legacy_identity("weightday") == "weightday"


def test_idempotent():
    once = sanitize_legacy_identity("run_8d eightd-x 8d-reports")
    assert sanitize_legacy_identity(once) == once


def test_skill_8d_mrc_not_rewritten():
    # live sibling skill reference must pass through unchanged (no rewrite)
    s = "the sibling skill skill-8d-mrc does X"
    assert sanitize_legacy_identity(s) == s


def test_skill_8d_mrc_not_in_denylist():
    assert "skill-8d-mrc" not in FORBIDDEN_LEGACY_IDENTITY_TERMS


def test_six_tokens_remain_in_denylist():
    assert set(FORBIDDEN_LEGACY_IDENTITY_TERMS) == {
        "run_8d", "trigger_8d", "eightd", "8d-reports", "pending-8d", "CLAUDE_EIGHTD",
    }


def test_empty_string_passthrough():
    assert sanitize_legacy_identity("") == ""


# --- Task 7: integration — the sota-gate death cannot recur -----------------

def test_phase9_plan_with_legacy_token_sanitizes_and_does_not_raise(tmp_path):
    """A Phase-9-style plan containing run_8d: after sanitize the file is written,
    validate_phase9_plan returns without raising, and content reads the active
    identity (re-creation of the sota-gate death now yields a clean plan)."""
    plan_path = tmp_path / "plan.md"
    raw = (
        "# Plan\n\n"
        "## Task 1: Wire run_8d entrypoint\n\n"
        "**Files:** run_8d.py\n\n"
        + ("- [ ] **Step N: invoke run_8d here.**\n" * 30)
    )
    # Phase-9-style: sanitize before writing.
    cleaned = sanitize_legacy_identity(raw)
    plan_path.write_text(cleaned, encoding="utf-8")

    # No raise — identity is no longer a predicate of validate_phase9_plan.
    validate_phase9_plan(plan_path)

    content = plan_path.read_text(encoding="utf-8")
    assert "run_8d" not in content
    assert "run_ai_escape_mrc" in content


def test_skill_8d_mrc_passes_through_phase9_sanitize_unchanged(tmp_path):
    """A plan referencing the live sibling skill skill-8d-mrc passes through
    unchanged and validate_phase9_plan does not raise."""
    plan_path = tmp_path / "plan.md"
    raw = (
        "# Plan\n\n"
        "## Task 1: Reference sibling\n\n"
        "**Files:** ai_escape_mrc/graph.py\n\n"
        "The sibling skill skill-8d-mrc is referenced legitimately.\n\n"
        + ("- [ ] **Step N: do work.**\n" * 30)
    )
    cleaned = sanitize_legacy_identity(raw)
    plan_path.write_text(cleaned, encoding="utf-8")

    validate_phase9_plan(plan_path)

    content = plan_path.read_text(encoding="utf-8")
    assert "skill-8d-mrc" in content  # not rewritten
