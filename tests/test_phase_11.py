"""Tests for phase_11_execute — skip-on-not-approved + CLAUDECODE env strip."""
from unittest.mock import patch, MagicMock
from pathlib import Path
from eightd.phases.phase_11_execute import phase_11_execute


def test_phase_11_skips_when_not_approved(tmp_path):
    state = {"run_id": "x", "run_dir": str(tmp_path),
             "plan_path": str(tmp_path / "plan.md"),
             "approval": {"approved": False, "rejected": True, "rejected_reason": "no"}}
    result = phase_11_execute(state)
    assert result["phase_11_complete"] is True
    assert result.get("phase_11_skipped") is True


def test_phase_11_dispatches_when_approved(tmp_path):
    (tmp_path / "plan.md").write_text("# plan", encoding="utf-8")
    state = {"run_id": "x", "run_dir": str(tmp_path),
             "plan_path": str(tmp_path / "plan.md"),
             "approval": {"approved": True, "via": "cli"}}
    captured_env = {}

    def fake_popen(cmd, env=None, **kw):
        captured_env.update(env or {})
        m = MagicMock()
        m.wait.return_value = 0
        m.returncode = 0
        return m

    with patch("subprocess.Popen", side_effect=fake_popen), \
         patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=False):
        result = phase_11_execute(state)

    assert "CLAUDECODE" not in captured_env
    assert result["phase_11_complete"] is True
