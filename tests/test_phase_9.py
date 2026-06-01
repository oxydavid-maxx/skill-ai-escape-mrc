"""Tests for phase_9_write_plan - direct call_claude (no subprocess, no template).

Per escape #8 fix refined to option (e): Phase 9 uses direct LLM call matching
Phase 7's pattern. Tests mock call_claude and assert call shape; LLM output
content is non-deterministic so we don't pin specific strings.

DETECTION: test_no_subprocess_import_in_phase9 - structural guard against
regression to subprocess-based dispatch.
"""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from ai_escape_mrc.phases.phase_9_write_plan import phase_9_write_plan
from ai_escape_mrc.validators import FORBIDDEN_LEGACY_IDENTITY_TERMS


def _make_action(title, priority="medium", quadrant="corrective:TRC-NC"):
    return {"title": title, "description": f"Fix {title} across the ecosystem",
            "files_touched": ["ai_escape_mrc/graph.py"], "owner": "kuangyu",
            "priority": priority, "source_quadrant": quadrant}


def test_invokes_call_claude_and_writes_plan(tmp_path):
    actions = [_make_action("Fix corrective issue A", quadrant="corrective:TRC-NC")]
    (tmp_path / "actions.json").write_text(json.dumps(actions), encoding="utf-8")
    state = {"run_id": "run-test-1", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}

    captured = {}

    # WIKI-EXEMPT: test fixture update ??validator now requires >500 bytes + ## Task marker
    # Return a stub that satisfies validate_phase9_plan() contract (>500 bytes, has ## Task).
    _STUB_SUFFIX = ("- [ ] **Step N: Do something concrete.**\n" * 20)

    def fake_call_claude(**kwargs):
        captured.update(kwargs)
        return (
            "# Plan stub from mocked LLM\n\n"
            "## Task 1: Fix corrective issue A\n\n"
            "**Files:** ai_escape_mrc/graph.py\n\n"
            + _STUB_SUFFIX
        )

    with patch("ai_escape_mrc.phases.phase_9_write_plan.call_claude", side_effect=fake_call_claude):
        result = phase_9_write_plan(state)

    assert captured["purpose"] == "phase_9_write_plan"
    assert "implementation-plan author" in captured["system"]
    assert "run-test-1" in captured["user"]
    assert "Fix corrective issue A" in captured["user"]
    assert captured["max_tokens"] == 16000
    assert captured["temperature"] == 0.3

    plan_path = Path(result["plan_path"])
    assert plan_path.exists()
    assert plan_path.read_text(encoding="utf-8").startswith("# Plan stub")
    assert result["phase_9_complete"] is True


def test_empty_actions_still_invokes_llm(tmp_path):
    """Even with zero actions, Phase 9 still calls the LLM (which can decide what to emit)."""
    (tmp_path / "actions.json").write_text("[]", encoding="utf-8")
    state = {"run_id": "run-empty", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}

    # WIKI-EXEMPT: test fixture update ??validator now requires >500 bytes + ## Task marker
    _EMPTY_STUB = (
        "# Empty Implementation Plan\n\n"
        "## Task 1: No actions ??review problem statement\n\n"
        "**Files:** N/A\n\n"
        + ("- [ ] **Step N: Review and re-run analysis.**\n" * 20)
    )
    with patch("ai_escape_mrc.phases.phase_9_write_plan.call_claude", return_value=_EMPTY_STUB) as mock_call:
        result = phase_9_write_plan(state)

    assert mock_call.called
    assert "0 items" in mock_call.call_args.kwargs["user"]
    assert result["phase_9_complete"] is True


def test_no_subprocess_import_in_phase9():
    phase9_src = Path(__file__).parent.parent / "ai_escape_mrc" / "phases" / "phase_9_write_plan.py"
    content = phase9_src.read_text(encoding="utf-8")
    code_lines = [l for l in content.splitlines()
                  if not l.strip().startswith('"""')
                  and not l.strip().startswith('#')
                  and not l.strip().startswith("'")]
    code_only = chr(10).join(code_lines)
    assert "import subprocess" not in code_only, "subprocess regression"
    assert "subprocess.Popen(" not in code_only, "Popen regression"


def test_no_plan_template_import_in_phase9():
    """Per FRC: deterministic template (option b) was replaced by direct LLM (option e).
    Verify the template module is no longer imported."""
    phase9_src = Path(__file__).parent.parent / "ai_escape_mrc" / "phases" / "phase_9_write_plan.py"
    content = phase9_src.read_text(encoding="utf-8")
    code_lines = [l for l in content.splitlines()
                  if not l.strip().startswith('"""')
                  and not l.strip().startswith('#')
                  and not l.strip().startswith("'")]
    code_only = chr(10).join(code_lines)
    assert "_plan_template" not in code_only, "deterministic template regression"
    assert "from ai_escape_mrc.phases._plan_template" not in code_only


def test_phase9_generation_prompt_includes_denylist_and_rename_rule():
    """Updated contract (post run-1780273836 fix): SYSTEM_PROMPT MUST embed the
    forbidden-literal denylist so the LLM can recognize legacy identity terms
    leaking from upstream actions.json and rename them. The plan.md OUTPUT
    contract (no forbidden literals) is enforced by validate_phase9_plan, not
    by hiding the denylist from the prompt."""
    from ai_escape_mrc.phases.phase_9_write_plan import SYSTEM_PROMPT

    # Denylist must be visible to the LLM.
    for term in FORBIDDEN_LEGACY_IDENTITY_TERMS:
        assert term in SYSTEM_PROMPT, f"denylist term {term!r} missing from SYSTEM_PROMPT"

    # Rename rule must be present so the LLM knows how to rewrite.
    assert "IDENTITY RENAME RULE" in SYSTEM_PROMPT
    assert "skill-ai-escape-mrc" in SYSTEM_PROMPT
    assert "aem-" in SYSTEM_PROMPT
