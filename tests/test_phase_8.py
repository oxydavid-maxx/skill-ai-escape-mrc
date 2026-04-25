"""Tests for phase_8_collect_actions — Phase 4+6 action extraction."""
import json
from pathlib import Path
from eightd.phases.phase_8_collect_actions import phase_8_collect_actions


def test_extracts_4_quadrants_from_full_state(tmp_path):
    state = {
        "run_id": "test-run-1",
        "run_dir": str(tmp_path),
        "phase_4_actions": {
            "TRC-NC": [{"title": "Fix X", "description": "...", "files": ["a.py"]}],
            "TRC-ND": [{"title": "Detect Y", "description": "...", "files": ["b.py"]}],
            "MRC-NC": [{"title": "Prevent Z", "description": "...", "files": ["c.py"]}],
            "MRC-ND": [{"title": "Audit W", "description": "...", "files": ["d.py"]}],
        },
        "phase_6_verification_plan": [{"title": "Verify all", "description": "..."}],
    }
    result = phase_8_collect_actions(state)
    actions_path = Path(result["actions_path"])
    assert actions_path.exists()
    data = json.loads(actions_path.read_text(encoding="utf-8"))
    assert len(data) == 5  # 4 corrective + 1 verification
    sources = {a["source_quadrant"] for a in data}
    assert sources == {"TRC-NC", "TRC-ND", "MRC-NC", "MRC-ND", "verification"}


def test_returns_empty_on_no_actions(tmp_path):
    state = {"run_id": "empty", "run_dir": str(tmp_path), "phase_4_actions": {}}
    result = phase_8_collect_actions(state)
    data = json.loads(Path(result["actions_path"]).read_text(encoding="utf-8"))
    assert data == []
