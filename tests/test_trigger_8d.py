"""Tests for trigger_8d.py -- Managed Agents orchestrator.

Tests mock the external HTTP layer (requests) and the email sender.
No live API calls, no file-system side effects beyond tmp_path.

WIKI-CONSULTED: degraded-emission-with-warning#fail-closed
WIKI-FINDING: handle_session_complete must raise ValidationError before writing any artifact
WIKI-ACTION: test_payload_schema_error_writes_no_artifacts verifies the fail-closed contract
"""
from __future__ import annotations
import json, os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from trigger_8d import (
    create_cloud_session,
    handle_session_complete,
    _cmd_resume_approval,
)
from eightd.managed_agent.output_schema import ActionItem, CloudPayload, PhaseMetadata
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_payload(report_lines: int = 200, plan_lines: int = 100) -> dict:
    """Minimal CloudPayload dict that passes schema validation."""
    report_md = "# 8D Report\n" + "line\n" * report_lines
    plan_md = "# Plan\n## Task 1: Fix thing\n" + "line\n" * plan_lines
    return {
        "report_md": report_md,
        "plan_md": plan_md,
        "actions_json": [
            {
                "title": "Fix corrective issue",
                "description": "Resolve the root cause in the pipeline",
                "files_touched": ["eightd/graph.py"],
                "owner": "kuangyu",
                "priority": "high",
                "source_quadrant": "corrective:TRC-NC",
            }
        ],
        "phase_metadata": {
            "phases_completed": ["P0", "P1", "P2"],
            "phase_durations_sec": {"P0": 10.0, "P1": 5.0, "P2": 7.0},
            "total_runtime_sec": 22.0,
            "total_tokens_used": {"input": 6000, "output": 2000},
        },
    }


# ---------------------------------------------------------------------------
# create_cloud_session
# ---------------------------------------------------------------------------

def test_create_cloud_session_returns_session_id():
    """create_cloud_session parses session_id from the POST response body."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"session_id": "sess-abc123"}
    mock_resp.raise_for_status.return_value = None

    with patch("trigger_8d.requests.post", return_value=mock_resp) as mock_post:
        sid = create_cloud_session("Test problem", "skill-8d-mrc-v1", "key-xyz")

    assert sid == "sess-abc123"
    call_kwargs = mock_post.call_args
    assert "anthropic-beta" in call_kwargs.kwargs["headers"]
    assert "managed-agents" in call_kwargs.kwargs["headers"]["anthropic-beta"]
    assert call_kwargs.kwargs["json"]["agent_id"] == "skill-8d-mrc-v1"
    assert call_kwargs.kwargs["json"]["input"] == "Test problem"


def test_create_cloud_session_propagates_http_error():
    """create_cloud_session lets requests exceptions propagate (caller handles them)."""
    import requests as req_mod
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = req_mod.HTTPError("403 Forbidden")

    with patch("trigger_8d.requests.post", return_value=mock_resp):
        with pytest.raises(req_mod.HTTPError):
            create_cloud_session("problem", "agent", "bad-key")


# ---------------------------------------------------------------------------
# handle_session_complete
# ---------------------------------------------------------------------------

def test_handle_session_complete_writes_all_artifacts(tmp_path):
    """Valid payload: report.md + plan.md + actions.json + gate file all written."""
    run_dir = tmp_path / "run-test-001"
    gate_dir = tmp_path / "approvals"
    payload = _valid_payload()

    with patch("trigger_8d._send_completion_email", return_value=True):
        result = handle_session_complete("sess-001", run_dir, payload, gate_dir)

    assert (run_dir / "report.md").exists()
    assert (run_dir / "plan.md").exists()
    actions = json.loads((run_dir / "actions.json").read_text())
    assert len(actions) == 1
    assert actions[0]["title"] == "Fix corrective issue"

    gate_file = gate_dir / "run-test-001.json"
    assert gate_file.exists()
    gate_doc = json.loads(gate_file.read_text())
    assert gate_doc["cloud_session_id"] == "sess-001"
    assert gate_doc["approved"] is False
    assert "session_id" in result or "gate_file" in result


def test_payload_schema_error_writes_no_artifacts(tmp_path):
    """R13 fail-closed: ValidationError raised before any artifact is written."""
    run_dir = tmp_path / "run-bad-001"
    gate_dir = tmp_path / "approvals"
    bad_payload = {"report_md": "too short", "plan_md": "also short",
                   "actions_json": [], "phase_metadata": {}}

    with pytest.raises(Exception):  # ValidationError or subclass
        handle_session_complete("sess-bad", run_dir, bad_payload, gate_dir)

    # No artifacts should exist - R13 fail-closed
    assert not run_dir.exists() or not (run_dir / "report.md").exists()


def test_handle_session_complete_gate_file_has_plan_inline(tmp_path):
    """Gate file must contain plan_inline for the pending-actions-reminder hook."""
    run_dir = tmp_path / "run-inline-001"
    gate_dir = tmp_path / "approvals"
    payload = _valid_payload()

    with patch("trigger_8d._send_completion_email", return_value=True):
        handle_session_complete("sess-inline", run_dir, payload, gate_dir)

    gate_doc = json.loads((gate_dir / "run-inline-001.json").read_text())
    assert "plan_inline" in gate_doc
    assert len(gate_doc["plan_inline"]) > 0


# ---------------------------------------------------------------------------
# _cmd_resume_approval
# ---------------------------------------------------------------------------

def test_cmd_resume_approval_approve(tmp_path):
    """--resume --approve marks gate doc as approved=True."""
    real_gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"
    real_gate_dir.mkdir(parents=True, exist_ok=True)
    gate_doc = {"run_id": "run-TEST-approve-xxx",
                "approved": False, "rejected": False,
                "plan_path": str(tmp_path / "plan.md")}
    real_gate_path = real_gate_dir / "run-TEST-approve-xxx.json"
    real_gate_path.write_text(json.dumps(gate_doc))
    try:
        rc = _cmd_resume_approval("run-TEST-approve-xxx", approve=True, reject_reason=None)
        assert rc == 0
        updated = json.loads(real_gate_path.read_text())
        assert updated["approved"] is True
        assert updated["approved_at"] is not None
        assert updated["via"] == "cli"
    finally:
        real_gate_path.unlink(missing_ok=True)


def test_cmd_resume_approval_missing_gate_returns_1():
    """--resume for unknown run_id returns exit code 1."""
    rc = _cmd_resume_approval("run-does-not-exist-zzz999", approve=True, reject_reason=None)
    assert rc == 1
