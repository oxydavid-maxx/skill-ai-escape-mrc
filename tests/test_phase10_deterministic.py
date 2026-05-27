"""Tests: Phase 10 final delivery is deterministic and LLM-independent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from ai_escape_mrc.phases.phase_10_emit_and_wait import phase_10_emit_and_wait
from ai_escape_mrc.render import render_plan_header


def test_render_plan_header_produces_markdown():
    actions = [
        {"title": "Fix pipeline gap", "description": "Close the escape.",
         "files_touched": ["ai_escape_mrc/graph.py"]},
        {"title": "Add validator", "description": "Validate output contract.",
         "files_touched": ["ai_escape_mrc/validators.py"]},
    ]
    result = render_plan_header(actions, topic="Ecosystem Hardening")
    assert result.startswith("# Ecosystem Hardening Plan")
    assert "## Task 1: Fix pipeline gap" in result
    assert "## Task 2: Add validator" in result
    assert "ai_escape_mrc/graph.py" in result


def test_render_plan_header_empty_actions():
    result = render_plan_header([], topic="Empty")
    assert "# Empty Plan" in result
    assert "_No actions provided._" in result


def test_render_plan_header_no_topic():
    result = render_plan_header([{"title": "Do thing"}])
    assert "# Implementation Plan" in result
    assert "## Task 1: Do thing" in result


def test_phase10_delivery_survives_llm_down(tmp_path):
    run_id = "run-test-phase10-determinism-001"
    run_dir = tmp_path / run_id
    run_dir.mkdir()

    plan_path = run_dir / "plan.md"
    plan_path.write_text("# Plan\n\n## Task 1: Check schema\n", encoding="utf-8")
    report_path = run_dir / "report.md"
    report_path.write_text("# AI Escape MRC Report\n\nPlaceholder.", encoding="utf-8")

    state = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "actions_count": 1,
    }

    from ai_escape_mrc.phases import phase_9_write_plan as _p9_mod

    with patch.object(_p9_mod, "call_claude",
                      side_effect=RuntimeError("LLM down -- should not be called")), \
         patch("ai_escape_mrc.delivery.email.send_consolidated_email", return_value={
             "ok": True,
             "channel": "test",
             "to": "operator@example.com",
             "cc": [],
             "source": "operator_fallback",
             "message": "sent",
             "error": None,
         }):
        result = phase_10_emit_and_wait(state)

    delivery_status = Path(result["delivery_status_path"])
    assert delivery_status.exists()
    doc = json.loads(delivery_status.read_text(encoding="utf-8"))
    assert doc["run_id"] == run_id
    assert doc["email_delivery_result"] == "sent"
    assert doc["plan_path"] == str(plan_path)
    assert result["phase_10_complete"] is True


def test_phase10_delivery_status_schema_has_required_fields(tmp_path):
    run_id = "run-test-schema-check-001"
    run_dir = tmp_path / run_id
    run_dir.mkdir()

    plan_path = run_dir / "plan.md"
    plan_path.write_text("# Schema Test Plan\n\n## Task 1: Check schema\n", encoding="utf-8")
    report_path = run_dir / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")

    state = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "actions_count": 1,
    }

    required_fields = {
        "run_id", "created_at", "report_path", "plan_path",
        "stage_summaries_path", "recipient_to", "recipient_cc",
        "recipient_source", "email_delivery_result", "email_delivery_error",
        "email_delivery",
    }

    with patch("ai_escape_mrc.delivery.email.send_consolidated_email", return_value={
        "ok": False,
        "channel": "test",
        "to": "",
        "cc": [],
        "source": "missing",
        "message": "",
        "error": "mailbox unavailable",
    }):
        result = phase_10_emit_and_wait(state)

    doc = json.loads(Path(result["delivery_status_path"]).read_text(encoding="utf-8"))
    missing = required_fields - set(doc.keys())
    assert not missing, f"Delivery status missing required fields: {missing}"
    assert doc["email_delivery_result"] == "failed"
    assert doc["email_delivery_error"] == "mailbox unavailable"
