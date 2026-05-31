"""Tests for phase_8_collect_actions ??Phase 4+6 action extraction."""
import json
from pathlib import Path
from ai_escape_mrc.phases.phase_8_collect_actions import phase_8_collect_actions


def test_extracts_corrective_prevention_only(tmp_path):
    """Collects ONLY corrective + prevention actions (the implementation work).
    verification_plan is NOT task-ified — it is a measurement plan and stays in
    the report's Section C — so the plan (phase_9) can run in parallel with
    verification (phase_6).
    """
    state = {
        "run_id": "test-run-1",
        "run_dir": str(tmp_path),
        "corrective_actions": {
            "q1_trc_nc": {"action": "Fix X", "files": ["a.py"]},
            "q2_trc_nd": {"action": "Detect Y", "files": ["b.py"]},
            "q3_mrc_nc": {"action": "Prevent Z", "files": ["c.py"]},
            "q4_mrc_nd": {"action": "Audit W", "files": ["d.py"]},
        },
        "prevention_actions": {
            "q1_trc_nc": {"action": "Prevent X recur", "files": ["e.py"]},
            "q2_trc_nd": {"action": "Detect Y proactive", "files": ["f.py"]},
            "q3_mrc_nc": {"action": "Charter for Z class", "files": ["g.md"]},
            "q4_mrc_nd": {"action": "Quarterly audit W", "files": ["h.sh"]},
        },
        # verification_plan is present in state but must NOT be collected as a task.
        "verification_plan": {"action": "Verify all corrective+prevention via E2E"},
    }
    result = phase_8_collect_actions(state)
    actions_path = Path(result["actions_path"])
    assert actions_path.exists()
    data = json.loads(actions_path.read_text(encoding="utf-8"))
    assert len(data) == 8  # 4 corrective + 4 prevention, NO verification
    sources = {a["source_quadrant"] for a in data}
    assert sources == {
        "corrective:TRC-NC", "corrective:TRC-ND", "corrective:MRC-NC", "corrective:MRC-ND",
        "prevention:TRC-NC", "prevention:TRC-ND", "prevention:MRC-NC", "prevention:MRC-ND",
    }
    assert not any(a["source_quadrant"] == "verification" for a in data)


def test_returns_empty_on_no_actions(tmp_path):
    state = {"run_id": "empty", "run_dir": str(tmp_path)}
    result = phase_8_collect_actions(state)
    data = json.loads(Path(result["actions_path"]).read_text(encoding="utf-8"))
    assert data == []
    assert result["actions_count"] == 0
    assert result["phase_8_complete"] is True


def test_handles_partial_state(tmp_path):
    """If only some quadrants populated, others skipped silently."""
    state = {
        "run_id": "partial",
        "run_dir": str(tmp_path),
        "corrective_actions": {"q1_trc_nc": {"action": "only one"}},
    }
    result = phase_8_collect_actions(state)
    data = json.loads(Path(result["actions_path"]).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["source_quadrant"] == "corrective:TRC-NC"
