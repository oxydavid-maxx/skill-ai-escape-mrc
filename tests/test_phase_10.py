"""Tests for phase_10_emit_and_wait — gate file write + interrupt()."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest


def test_phase_10_writes_gate_file_with_inline_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan_path = tmp_path / "plan.md"
    plan_path.write_text("# Plan\n\n- step 1\n- step 2\n", encoding="utf-8")

    from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait

    state = {
        "run_id": "test-10",
        "run_dir": str(tmp_path),
        "report_path": str(tmp_path / "report.md"),
        "plan_path": str(plan_path),
        "actions_count": 5,
    }
    (tmp_path / "report.md").write_text("# report stub", encoding="utf-8")

    # Patch interrupt() at the module level where it's imported
    with patch("eightd.phases.phase_10_emit_and_wait.interrupt", return_value={"approved": True, "via": "test"}):
        result = phase_10_emit_and_wait(state)

    gate_dir = tmp_path / ".claude" / ".pending-8d-approvals"
    gate_files = list(gate_dir.glob("test-10.json"))
    assert len(gate_files) == 1
    gate = json.loads(gate_files[0].read_text(encoding="utf-8"))
    assert gate["plan_inline"].startswith("# Plan")
    assert gate["actions_count"] == 5
    assert gate["approved"] is False  # initial state
    assert result["approval"] == {"approved": True, "via": "test"}
