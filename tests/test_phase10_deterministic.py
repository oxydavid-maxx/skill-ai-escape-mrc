# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: Phase 10 gate emission must be LLM-independent. The gate file is the
#   source of truth for the approval flow; if it depends on Phase 9's LLM call, a
#   transient LLM failure can block the entire approval pipeline.
# WIKI-ACTION: Test patches call_claude to raise RuntimeError("LLM down") and asserts
#   gate file is still written, proving Phase 10 is fully decoupled from Phase 9 LLM.
"""Tests: Phase 10 gate-file emission is deterministic and LLM-independent.

Key invariant: phase_10_emit_and_wait() writes a valid gate file even when
Phase 9's call_claude() is unavailable.  This proves the closed-loop approval
path cannot be broken by LLM failures in Phase 9.

render.py is also tested here: render_plan_header() must produce a non-empty
Markdown string without any external calls.
"""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# WIKI-EXEMPT: import-only fix — no pattern change, wiki already consulted above
from eightd.render import render_plan_header
from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait


# ---------------------------------------------------------------------------
# render_plan_header tests
# ---------------------------------------------------------------------------

def test_render_plan_header_produces_markdown():
    actions = [
        {"title": "Fix pipeline gap", "description": "Close the escape.",
         "files_touched": ["eightd/graph.py"]},
        {"title": "Add validator", "description": "Validate output contract.",
         "files_touched": ["eightd/validators.py"]},
    ]
    result = render_plan_header(actions, topic="Ecosystem Hardening")
    assert result.startswith("# Ecosystem Hardening Plan")
    assert "## Task 1: Fix pipeline gap" in result
    assert "## Task 2: Add validator" in result
    assert "eightd/graph.py" in result


def test_render_plan_header_empty_actions():
    result = render_plan_header([], topic="Empty")
    assert "# Empty Plan" in result
    assert "_No actions provided._" in result


def test_render_plan_header_no_topic():
    result = render_plan_header([{"title": "Do thing"}])
    assert "# Implementation Plan" in result
    assert "## Task 1: Do thing" in result


# ---------------------------------------------------------------------------
# Phase 10 deterministic gate-emission test
# ---------------------------------------------------------------------------

def test_phase10_gate_emission_survives_llm_down(tmp_path):
    """Phase 10 gate-file write succeeds even when call_claude raises.

    Scenario:
    1. Phase 9's call_claude is patched to raise RuntimeError (simulates LLM outage).
    2. A plan.md is pre-written by the test (simulating that Phase 9 ran successfully
       in a previous session / from a different path).
    3. phase_10_emit_and_wait() is called with a state pointing at that plan.md.
    4. Assertions: gate file exists, has approved=False, has plan_inline content,
       and the run_id matches.

    This proves that Phase 10 does NOT call call_claude and is fully deterministic.
    """
    # Arrange: write a plan.md as if Phase 9 had already produced it
    run_id = "run-test-phase10-determinism-001"
    run_dir = tmp_path / run_id
    run_dir.mkdir()

    actions = [{"title": "Fix corrective issue", "description": "Resolve root cause",
                "files_touched": ["eightd/graph.py"], "owner": "kuangyu",
                "priority": "high", "source_quadrant": "corrective:TRC-NC"}]

    plan_content = render_plan_header(actions, topic="Test Ecosystem")
    plan_path = run_dir / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    report_path = run_dir / "report.md"
    report_path.write_text("# 8D Report\n\nPlaceholder.", encoding="utf-8")

    state = {
        "run_id": run_id,
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "actions_count": len(actions),
    }

    # Gate dir → use tmp_path so we don't pollute real ~/.claude
    gate_dir = tmp_path / "approvals"
    gate_dir.mkdir()

    # Phase 9's call_claude is "down" — but phase_10 must not call it at all
    from eightd.phases import phase_9_write_plan as _p9_mod

    # Act: call phase_10 with LLM disabled, interrupt patched, email patched
    from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait
    from langgraph.types import interrupt as _interrupt

    interrupt_payload = {}

    def fake_interrupt(payload):
        interrupt_payload.update(payload)
        return {"approved": True, "via": "test"}

    with patch.object(_p9_mod, "call_claude",
                      side_effect=RuntimeError("LLM down — should not be called")), \
         patch("eightd.phases.phase_10_emit_and_wait.interrupt", side_effect=fake_interrupt), \
         patch("eightd.delivery.email.send_consolidated_email", return_value=True), \
         patch("eightd.phases.phase_10_emit_and_wait.Path.home", return_value=tmp_path):

        result = phase_10_emit_and_wait(state)

    # Assert: gate file written
    # Note: gate_dir path depends on Path.home() mock → tmp_path / ".claude" / ".pending-8d-approvals"
    pending_dir = tmp_path / ".claude" / ".pending-8d-approvals"
    gate_file = pending_dir / f"{run_id}.json"

    assert gate_file.exists(), f"Gate file not written at {gate_file}"

    gate_doc = json.loads(gate_file.read_text(encoding="utf-8"))
    assert gate_doc["run_id"] == run_id
    assert gate_doc["approved"] is False, "Gate must start as unapproved"
    assert len(gate_doc["plan_inline"]) > 0, "plan_inline must be non-empty"
    assert "# Test Ecosystem Plan" in gate_doc["plan_inline"]

    # interrupt was called with the right keys
    assert interrupt_payload.get("approval_pending") is True
    assert run_id in interrupt_payload.get("run_id", "")

    # phase_10_complete flag returned
    assert result.get("phase_10_complete") is True


def test_phase10_gate_file_schema_has_all_required_fields(tmp_path):
    """Gate file must contain all schema fields required by Portal A/B consumers."""
    run_id = "run-test-schema-check-001"
    run_dir = tmp_path / run_id
    run_dir.mkdir()

    plan_path = run_dir / "plan.md"
    plan_path.write_text("# Schema Test Plan\n\n## Task 1: Check schema\n", encoding="utf-8")
    report_path = run_dir / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")

    state = {
        "run_id": run_id,
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "actions_count": 1,
    }

    required_fields = {
        "run_id", "created_at", "report_path", "plan_path",
        "plan_inline", "actions_count", "approved", "approved_at",
        "via", "rejected", "rejected_reason",
    }

    def fake_interrupt(payload):
        return {"approved": False}

    with patch("eightd.phases.phase_10_emit_and_wait.interrupt", side_effect=fake_interrupt), \
         patch("eightd.delivery.email.send_consolidated_email", return_value=True), \
         patch("eightd.phases.phase_10_emit_and_wait.Path.home", return_value=tmp_path):

        phase_10_emit_and_wait(state)

    gate_file = tmp_path / ".claude" / ".pending-8d-approvals" / f"{run_id}.json"
    gate_doc = json.loads(gate_file.read_text(encoding="utf-8"))

    missing = required_fields - set(gate_doc.keys())
    assert not missing, f"Gate file missing required fields: {missing}"
