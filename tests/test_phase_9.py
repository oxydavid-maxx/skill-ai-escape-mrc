"""Tests for phase_9_write_plan - deterministic template (no subprocess).

Per escape #8 fix: Phase 9 replaced subprocess.Popen dispatch with
pure-Python _plan_template.generate_plan(). The old Popen mock test
is intentionally removed (Popen gone).

DETECTION: test_no_subprocess_import_in_phase9 - structural guard against
regression to subprocess-based dispatch.
"""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from eightd.phases.phase_9_write_plan import phase_9_write_plan


def _make_action(title, priority="medium", quadrant="corrective:TRC-NC"):
    return {"title": title, "description": f"Fix {title} across the ecosystem",
            "files_touched": ["eightd/graph.py"], "owner": "kuangyu",
            "priority": priority, "source_quadrant": quadrant}


def test_generates_plan_from_actions(tmp_path):
    actions = [_make_action("Fix corrective issue A", quadrant="corrective:TRC-NC"),
               _make_action("Prevent recurrence B", quadrant="prevention:MRC-ND")]
    (tmp_path / "actions.json").write_text(json.dumps(actions), encoding="utf-8")
    state = {"run_id": "run-test-1", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}
    result = phase_9_write_plan(state)
    plan_path = Path(result["plan_path"])
    assert plan_path.exists(), "plan.md must be written"
    content = plan_path.read_text(encoding="utf-8")
    assert "## Task 1:" in content
    assert "## Task 2:" in content
    assert result["phase_9_complete"] is True


def test_high_priority_action_comes_first(tmp_path):
    actions = [_make_action("Medium action", priority="medium"),
               _make_action("High action", priority="high"),
               _make_action("Low action", priority="low")]
    (tmp_path / "actions.json").write_text(json.dumps(actions), encoding="utf-8")
    state = {"run_id": "run-sort-test", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}
    result = phase_9_write_plan(state)
    content = Path(result["plan_path"]).read_text(encoding="utf-8")
    high_pos = content.find("High action")
    medium_pos = content.find("Medium action")
    low_pos = content.find("Low action")
    assert high_pos < medium_pos < low_pos, "High must appear before medium before low"


def test_empty_actions_produces_valid_plan(tmp_path):
    (tmp_path / "actions.json").write_text("[]", encoding="utf-8")
    state = {"run_id": "run-empty", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}
    result = phase_9_write_plan(state)
    plan_path = Path(result["plan_path"])
    assert plan_path.exists()
    content = plan_path.read_text(encoding="utf-8")
    assert "Completion Checklist" in content
    assert result["phase_9_complete"] is True


def test_run_id_appears_in_plan(tmp_path):
    actions = [_make_action("Traceability check")]
    (tmp_path / "actions.json").write_text(json.dumps(actions), encoding="utf-8")
    state = {"run_id": "run-trace-xyz-42", "run_dir": str(tmp_path),
             "actions_path": str(tmp_path / "actions.json")}
    result = phase_9_write_plan(state)
    content = Path(result["plan_path"]).read_text(encoding="utf-8")
    assert "run-trace-xyz-42" in content, "run_id must appear in plan for traceability"


def test_no_subprocess_import_in_phase9():
    phase9_src = Path(__file__).parent.parent / "eightd" / "phases" / "phase_9_write_plan.py"
    content = phase9_src.read_text(encoding="utf-8")
    # Check actual code lines only (not docstring mentions of what was replaced)
    code_lines = [l for l in content.splitlines() if not l.strip().startswith('"""') and not l.strip().startswith('#') and not l.strip().startswith("'")]
    code_only = chr(10).join(code_lines)
    assert "import subprocess" not in code_only, "subprocess must not be imported - regression detected"
    assert "subprocess.Popen(" not in code_only, "subprocess.Popen call must not appear - regression detected"