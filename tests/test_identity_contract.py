from pathlib import Path

import pytest

from ai_escape_mrc.errors import OutputIdentityContractError
from ai_escape_mrc.validators import (
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    legacy_identity_instruction,
    validate_no_legacy_identity_terms,
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

    assert "skill-8d-mrc" in text


def test_validate_no_legacy_identity_terms_rejects_old_skill_name():
    with pytest.raises(OutputIdentityContractError) as exc_info:
        validate_no_legacy_identity_terms(
            "edit ~/.claude/skills/skill-8d-mrc/run_8d.py",
            artifact_name="plan.md",
        )

    assert exc_info.value.predicate == "legacy_identity:skill-8d-mrc"


def test_phase9_plan_validator_rejects_legacy_identity(tmp_path):
    plan = tmp_path / "plan.md"
    content = (
        "# Plan\n\n"
        "## Task 1: Fix output boundary\n\n"
        "**Files:** ~/.claude/skills/skill-8d-mrc/run_8d.py\n\n"
        + ("- [ ] **Step N: Do something concrete.**\n" * 30)
    )
    plan.write_text(content, encoding="utf-8")

    with pytest.raises(OutputIdentityContractError):
        validate_phase9_plan(plan)
