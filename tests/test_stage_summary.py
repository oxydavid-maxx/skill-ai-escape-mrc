from pathlib import Path

import pytest

from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.stage_summary import (
    VisibilityReporter,
    emit_phase_start_summary,
    emit_phase_error,
    emit_stage_progress,
    emit_stage_summary,
    fallback_summary_lines,
    summarize_phase,
)


def test_summarize_phase_3_audit_status():
    weakness = {
        "quadrant": "q1_trc_nc",
        "classification": "ADDRESSABLE",
        "issue": "root cause stops at report rendering but misses final-output visibility",
        "suggested_fix": "add transcript-visible completion acceptance",
    }
    state = {
        "phase_3_status": "passed",
        "phase_3_verdict": "EXHAUSTED",
        "phase_3_rounds": [{"round": 1}, {"round": 2, "weaknesses": [weakness]}],
        "phase_3_residual_risks": [],
    }

    lines = summarize_phase("phase_3_rc_audit", state)
    joined = "\n".join(lines)

    assert "Status: passed" in joined
    assert "final-output visibility" in joined
    assert "transcript-visible completion acceptance" in joined


def test_phase_2_summary_includes_four_quadrant_root_causes():
    state = {
        "why_chains": {
            "q1_trc_nc": {"root": "the finalization check never validates visible output"},
            "q2_trc_nd": {"root": "runtime progress events are treated as proof"},
            "q3_mrc_nc": {"root": "completion claims lack an enforced screen evidence gate"},
            "q4_mrc_nd": {"root": "skill identity surfaces are not covered by release checks"},
        }
    }

    lines = summarize_phase("phase_2_why_analysis", state)
    joined = "\n".join(lines)

    assert "TRC-NC root cause: the finalization check never validates visible output" in joined
    assert "TRC-ND root cause: runtime progress events are treated as proof" in joined
    assert "MRC-NC root cause: completion claims lack an enforced screen evidence gate" in joined
    assert "MRC-ND root cause: skill identity surfaces are not covered by release checks" in joined
    assert len([line for line in lines if "root cause:" in line]) == 4


def test_phase_4_summary_includes_action_content_not_counts_only():
    state = {
        "corrective_actions": {
            "q1_trc_nc": {
                "action": "Add final-state verifier before reporting success",
                "rationale": "prevents a run from claiming completion without screen evidence",
            },
            "q2_trc_nd": {
                "action": "Persist visibility receipts beside each LangGraph checkpoint",
                "rationale": "keeps progress inspectable after agent restarts",
            },
        },
        "prevention_actions": {
            "q3_mrc_nc": {
                "action": "Require completion claims to cite transcript-visible proof",
                "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
            },
            "q4_mrc_nd": {
                "action": "Add release check for renamed skill identity surfaces",
                "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
            },
        },
    }

    lines = summarize_phase("phase_4_actions", state)
    joined = "\n".join(lines)

    assert "TRC-NC corrective: Add final-state verifier" in joined
    assert "TRC-ND corrective: Persist visibility receipts" in joined
    assert "MRC-NC prevention: Require completion claims" in joined
    assert "MRC-ND prevention: Add release check" in joined
    assert "Corrective actions: 2" not in joined
    assert "Prevention actions: 2" not in joined


def test_emit_phase_4_summary_prints_all_quadrant_content(tmp_path, capsys):
    state = {
        "run_dir": str(tmp_path),
        "corrective_actions": {
            "q1_trc_nc": {"action": "Add transcript acceptance", "rationale": "visible proof"},
            "q2_trc_nd": {"action": "Record progress receipts", "rationale": "restart proof"},
        },
        "prevention_actions": {
            "q3_mrc_nc": {
                "action": "Block final claims without screen evidence",
                "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
            },
            "q4_mrc_nd": {
                "action": "Check renamed entrypoints before emission",
                "gate_test": {"scope": "PASS", "persistence": "PASS", "measurability": "PASS"},
            },
        },
    }

    emit_stage_summary("phase_4_actions", state)

    captured = capsys.readouterr()
    assert "TRC-NC corrective: Add transcript acceptance" in captured.err
    assert "TRC-ND corrective: Record progress receipts" in captured.err
    assert "MRC-NC prevention: Block final claims" in captured.err
    assert "MRC-ND prevention: Check renamed entrypoints" in captured.err


def test_phase_5_summary_includes_audit_issue_or_residual_risk():
    residual = {
        "quadrant": "q4_mrc_nd",
        "classification": "RESIDUAL",
        "issue": "operator-specific reminder does not protect other users",
        "suggested_fix": "move the guard into Python visibility enforcement",
    }
    state = {
        "phase_5_status": "passed",
        "phase_5_verdict": "EXHAUSTED",
        "phase_5_rounds": [{"round": 1, "weaknesses": [residual]}],
        "phase_5_residual_risks": [residual],
    }

    lines = summarize_phase("phase_5_prevention_audit", state)
    joined = "\n".join(lines)

    assert "operator-specific reminder does not protect other users" in joined
    assert "move the guard into Python visibility enforcement" in joined


def test_phase_6_summary_includes_metric_target_and_data_source():
    state = {
        "verification_plan": {
            "quadrants": [
                {
                    "quadrant": "q1_trc_nc",
                    "metric": "screen-summary coverage",
                    "target": "12 of 12 phases emit content summaries",
                    "data_source": "stage-summaries.jsonl",
                },
                {
                    "quadrant": "q2_trc_nd",
                    "metric": "progress receipt freshness",
                    "target": "heartbeat every 60 seconds",
                    "data_source": "stage-progress.jsonl",
                },
                {
                    "quadrant": "q3_mrc_nc",
                    "metric": "completion-claim evidence",
                    "target": "final response cites visible receipt",
                    "data_source": "terminal transcript",
                },
                {
                    "quadrant": "q4_mrc_nd",
                    "metric": "identity-regression hits",
                    "target": "zero old skill names",
                    "data_source": "identity validator log",
                },
            ],
            "overall_timeframe": "one release cycle",
        }
    }

    lines = summarize_phase("phase_6_verification", state)
    joined = "\n".join(lines)

    assert "TRC-NC verification: metric screen-summary coverage" in joined
    assert "target 12 of 12 phases emit content summaries" in joined
    assert "data source stage-summaries.jsonl" in joined
    assert "MRC-NC verification: metric completion-claim evidence" in joined


def test_emit_stage_summary_prints_and_writes(tmp_path, capsys):
    state = {
        "run_dir": str(tmp_path),
        "report_path": str(tmp_path / "report.md"),
        "closure_audit": {"ok": True},
    }
    Path(state["report_path"]).write_text("# Report\n", encoding="utf-8")

    patch = emit_stage_summary("phase_7_report", state)

    captured = capsys.readouterr()
    assert "[AI Escape MRC] Phase 7 Report" in captured.err
    assert "- Report:" in captured.err
    assert patch["screen_summary"].startswith("### Phase 7 Report")
    assert Path(patch["stage_summaries_path"]).exists()
    assert (tmp_path / "stage-summaries.jsonl").exists()


def test_emit_phase_start_summary_prints_immediately(tmp_path, capsys):
    emit_phase_start_summary("phase_3_rc_audit", {"run_dir": str(tmp_path)})

    captured = capsys.readouterr()
    assert "[AI Escape MRC] Phase 3 Root-Cause Audit" in captured.err
    assert "- Status: running" in captured.err
    assert "stage-summaries.md" in captured.err
    assert (tmp_path / "stage-progress.jsonl").exists()


def test_emit_stage_progress_prints_and_writes_jsonl(tmp_path, capsys):
    emit_stage_progress("phase_0_research", {"run_dir": str(tmp_path)}, "Running web research.", "Queries: 9.")

    captured = capsys.readouterr()
    assert "[AI Escape MRC] Phase 0 Research" in captured.err
    assert "- Progress: Running web research." in captured.err
    assert (tmp_path / "stage-progress.jsonl").exists()


def test_emit_phase_error_prints_and_writes_run_error(tmp_path, capsys):
    emit_phase_error("phase_5_prevention_audit", {"run_dir": str(tmp_path)}, RuntimeError("bad handle"))

    captured = capsys.readouterr()
    assert "[AI Escape MRC] FAILED at Phase 5 Prevention Audit" in captured.err
    assert "bad handle" in captured.err
    assert (tmp_path / "run-error.json").exists()


def test_reporter_screen_sink_failure_fails_closed(tmp_path):
    class BrokenStream:
        def write(self, _):
            raise OSError("screen closed")

        def flush(self):
            pass

    reporter = VisibilityReporter({"run_dir": str(tmp_path)}, stream=BrokenStream())

    with pytest.raises(VisibilityContractError, match="screen"):
        reporter.phase_start("phase_0_research")


def test_fallback_summary_is_deterministic_for_unknown_phase():
    lines = fallback_summary_lines("phase_99_custom", {"phase_99_complete": True, "alpha": 1})

    assert any("Status: complete" in line for line in lines)
    assert any("State keys observed" in line for line in lines)
