"""Tests for phase_9_write_plan — Popen env strip (CLAUDECODE defense-in-depth)."""
from unittest.mock import patch, MagicMock
from pathlib import Path
from eightd.phases.phase_9_write_plan import phase_9_write_plan


def test_phase_9_pops_claudecode_from_popen_env(tmp_path):
    state = {
        "run_id": "test-9",
        "run_dir": str(tmp_path),
        "actions_path": str(tmp_path / "actions.json"),
    }
    (tmp_path / "actions.json").write_text("[]", encoding="utf-8")
    captured_env = {}

    def fake_popen(cmd, env=None, **kw):
        captured_env.update(env or {})
        m = MagicMock()
        m.wait.return_value = 0
        m.returncode = 0
        # Simulate child writing plan.md
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# stub plan", encoding="utf-8")
        return m

    with patch("subprocess.Popen", side_effect=fake_popen), \
         patch.dict("os.environ", {"CLAUDECODE": "1", "OTHER": "ok"}, clear=False):
        result = phase_9_write_plan(state)

    assert "CLAUDECODE" not in captured_env, "CLAUDECODE leaked into child env"
    assert captured_env.get("OTHER") == "ok", "non-CC env vars must pass through"
    assert Path(result["plan_path"]).exists()
