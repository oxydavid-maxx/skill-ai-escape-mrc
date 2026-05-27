import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_escape_mrc.phases.phase_7_report import (
    PrerequisiteRefusedError,
    _state_summary,
    phase_7_report,
)


def _base_state(tmp_path: Path) -> dict:
    return {
        "problem": "AI harness rename escape",
        "run_id": "run-test-phase7",
        "run_dir": str(tmp_path / "run-test-phase7"),
        "is_isnt_table": {},
        "why_chains": {
            "q1_trc_nc": {},
            "q2_trc_nd": {},
            "q3_mrc_nc": {},
            "q4_mrc_nd": {},
        },
        "corrective_actions": {"q1_trc_nc": {}, "q2_trc_nd": {}},
        "prevention_actions": {"q3_mrc_nc": {}, "q4_mrc_nd": {}},
        "verification_plan": {"checks": []},
        "phase_3_complete": True,
        "phase_5_complete": True,
    }


def test_phase7_refuses_missing_status_when_rounds_show_fallback(tmp_path, monkeypatch):
    state = _base_state(tmp_path)
    state["phase_3_rounds"] = [{"round": 1, "_fallback": True, "weaknesses": []}]
    state["phase_5_rounds"] = [{"round": 1, "weaknesses": []}]
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_REPORTS_DIR", str(tmp_path / "reports"))

    with pytest.raises(PrerequisiteRefusedError, match="phase_3_status=failed"):
        phase_7_report(state)


def test_phase7_reconstructs_missing_status_and_residuals_from_rounds(tmp_path, monkeypatch):
    state = _base_state(tmp_path)
    state["phase_3_rounds"] = [
        {
            "round": 1,
            "weaknesses": [
                {"classification": "RESIDUAL", "issue": "rc residual"},
            ],
        }
    ]
    state["phase_5_rounds"] = [
        {
            "round": 1,
            "weaknesses": [
                {"classification": "RESIDUAL", "issue": "prevention residual"},
            ],
        }
    ]
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_REPORTS_DIR", str(tmp_path / "reports"))

    with patch(
        "ai_escape_mrc.phases.phase_7_report.call_claude",
        return_value="# AI Escape MRC Report\n",
    ):
        result = phase_7_report(state)

    assert result["phase_3_status"] == "passed"
    assert result["phase_5_status"] == "passed"
    assert result["phase_3_residual_risks"] == [{"classification": "RESIDUAL", "issue": "rc residual"}]
    assert result["phase_5_residual_risks"] == [{"classification": "RESIDUAL", "issue": "prevention residual"}]
    assert result["phase_7_complete"] is True
    assert Path(result["report_path"]).exists()
    assert (tmp_path / "run-test-phase7" / "report.md").exists()


def test_phase7_state_summary_clips_large_leaf_text(tmp_path):
    state = _base_state(tmp_path)
    state["why_chains"] = {
        "q1_trc_nc": {
            "whys": [
                {
                    "n": 1,
                    "why": "x" * 10000,
                    "evidence": "y" * 10000,
                }
            ]
        }
    }

    summary = _state_summary(state)

    why = summary["why_chains"]["q1_trc_nc"]["whys"][0]["why"]
    evidence = summary["why_chains"]["q1_trc_nc"]["whys"][0]["evidence"]
    assert len(why) < 1000
    assert len(evidence) < 1000
    assert "clipped" in why
    assert "clipped" in evidence


def test_phase7_state_summary_bounds_broad_payload(tmp_path):
    state = _base_state(tmp_path)
    state["why_chains"] = {
        f"q{i}": {
            "root": "root " + ("r" * 2000),
            "whys": [
                {"n": n, "why": "w" * 2000, "evidence": "e" * 2000}
                for n in range(5)
            ],
        }
        for i in range(4)
    }
    state["phase_3_rounds"] = [
        {"round": i, "weaknesses": [{"classification": "RESIDUAL", "issue": "x" * 2000} for _ in range(10)]}
        for i in range(3)
    ]
    state["phase_5_rounds"] = [
        {"round": i, "weaknesses": [{"classification": "ADDRESSABLE", "issue": "y" * 2000} for _ in range(10)]}
        for i in range(3)
    ]

    payload = json.dumps(_state_summary(state), ensure_ascii=False)

    assert len(payload) < 50000
    assert payload.count("clipped") >= 10
