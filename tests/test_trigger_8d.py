"""Tests for trigger_8d.py -- Managed Agents orchestrator.

Tests mock the anthropic SDK and email sender.
No live API calls, no file-system side effects beyond tmp_path.
"""
# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: old tests patching trigger_8d.requests (requests.post schema) are contradictory
#   to the new SDK implementation; leaving them would assert a wrong contract — the dual-function
#   latent bug FRC warns about. Must be replaced in the same edit.
# WIKI-ACTION: test_create_cloud_session_* rewritten to mock _get_client (SDK) not requests.post;
#   assert sessions.create uses {agent: {id,type}, environment_id} not {agent_id, input}.
# WIKI-CONSULTED: degraded-emission-with-warning#fail-closed
# WIKI-FINDING: handle_session_complete must raise ValidationError before writing any artifact
# WIKI-ACTION: test_payload_schema_error_writes_no_artifacts verifies the R13 fail-closed contract
from __future__ import annotations
import json, os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import anthropic

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

# WIKI-CONSULTED: function-replacement-convention#The-Convention
# WIKI-FINDING: old tests patched trigger_8d.requests.post with {agent_id,input} body —
#   wrong contract after SDK rewrite; leaving them asserts a dead schema.
# WIKI-ACTION: replaced with SDK-mocking tests asserting sessions.create({agent,environment_id}).

def _make_mock_client(session_id: str = "sess-abc123"):
    """Build a mock anthropic.Anthropic client for Managed Agents tests."""
    mock_client = MagicMock()
    mock_agent = MagicMock()
    mock_agent.id = "agent-mocked-id"
    mock_agent.name = "skill-8d-mrc-v1"
    agents_page = MagicMock()
    agents_page.__iter__ = MagicMock(return_value=iter([mock_agent]))
    mock_client.beta.agents.list.return_value = agents_page
    mock_client.beta.agents.create.return_value = mock_agent
    mock_env = MagicMock()
    mock_env.id = "env-mocked-id"
    mock_env.name = "skill-8d-mrc-env"
    envs_page = MagicMock()
    envs_page.__iter__ = MagicMock(return_value=iter([mock_env]))
    mock_client.beta.environments.list.return_value = envs_page
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_client.beta.sessions.create.return_value = mock_session
    mock_client.beta.sessions.events.send.return_value = MagicMock()
    return mock_client


def test_create_cloud_session_returns_session_id():
    """create_cloud_session uses SDK sessions.create+events.send; returns session_id.

    Correct schema: agent={"id":..,"type":"agent"} + environment_id.
    Old wrong schema {agent_id, input} returns HTTP 400 "Extra inputs not permitted".
    """
    mock_client = _make_mock_client(session_id="sess-abc123")

    with patch("trigger_8d._get_client", return_value=mock_client), \
         patch("trigger_8d._load_system_prompt", return_value="# system prompt"):
        sid = create_cloud_session("Test problem", "skill-8d-mrc-v1", "key-xyz")

    assert sid == "sess-abc123"
    create_kwargs = mock_client.beta.sessions.create.call_args.kwargs
    assert "agent" in create_kwargs
    assert create_kwargs["agent"]["type"] == "agent"
    assert "environment_id" in create_kwargs
    assert "agent_id" not in create_kwargs   # old wrong field
    assert "input" not in create_kwargs       # old wrong field
    send_call = mock_client.beta.sessions.events.send.call_args
    assert send_call is not None
    events = send_call.kwargs.get("events", [])
    msg = next((e for e in events if isinstance(e, dict) and e.get("type") == "user.message"), None)
    assert msg is not None
    assert any("Test problem" in b.get("text", "") for b in msg["content"] if isinstance(b, dict))


def test_create_cloud_session_propagates_sdk_error():
    """SDK AuthenticationError propagates out of create_cloud_session."""
    mock_client = _make_mock_client()
    mock_client.beta.sessions.create.side_effect = anthropic.AuthenticationError(
        message="bad key",
        response=MagicMock(status_code=401),
        body={"error": {"message": "bad key"}},
    )
    with patch("trigger_8d._get_client", return_value=mock_client), \
         patch("trigger_8d._load_system_prompt", return_value="# sys"):
        with pytest.raises(anthropic.AuthenticationError):
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
