"""Identity-contract tests, post sanitize-not-raise migration.

The former raise-based path (validate_no_legacy_identity_terms) was deleted:
identity is now sanitized, never raised. Phase 9's validator no longer checks
identity. The instruction helper still names the active identity and avoids
emitting deprecated literals by default.
"""
from ai_escape_mrc.validators import (
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    legacy_identity_instruction,
    sanitize_legacy_identity,
    validate_phase9_plan,
)


def test_legacy_identity_instruction_names_active_skill():
    text = legacy_identity_instruction()

    assert "AI Escape MRC" in text
    assert "skill-ai-escape-mrc" in text
    assert "run_ai_escape_mrc.py" in text
    for term in FORBIDDEN_LEGACY_IDENTITY_TERMS:
        assert term not in text


def test_legacy_identity_instruction_can_emit_denylist_for_non_generated_debug():
    text = legacy_identity_instruction(include_legacy_terms=True)

    # The denylist (the six auto-sanitized tokens) is visible for debug.
    for term in FORBIDDEN_LEGACY_IDENTITY_TERMS:
        assert term in text


def test_phase9_validator_does_not_raise_on_legacy_identity(tmp_path):
    """Identity is no longer a Phase 9 predicate. A plan that was sanitized
    before writing contains the active identity and passes; even a plan that
    still contained a legacy token would NOT raise here (size + markers only)."""
    plan = tmp_path / "plan.md"
    raw = (
        "# Plan\n\n"
        "## Task 1: Fix output boundary\n\n"
        "**Files:** run_8d.py\n\n"
        + ("- [ ] **Step N: Do something concrete.**\n" * 30)
    )
    plan.write_text(sanitize_legacy_identity(raw), encoding="utf-8")

    # No exception.
    validate_phase9_plan(plan)
    content = plan.read_text(encoding="utf-8")
    assert "run_ai_escape_mrc" in content
    assert "run_8d" not in content
