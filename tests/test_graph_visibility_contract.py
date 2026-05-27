from pathlib import Path

import pytest

from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.graph import _wrap_with_progress


def test_graph_wrapper_emits_required_start_and_summary_receipts(tmp_path, capsys):
    def phase(state):
        report = Path(state["run_dir"]) / "report.md"
        report.write_text("# Report\n", encoding="utf-8")
        return {
            "phase_7_complete": True,
            "report_path": str(report),
            "closure_audit": {"ok": True},
        }

    wrapped = _wrap_with_progress("phase_7_report", phase)
    result = wrapped({"run_dir": str(tmp_path)})

    captured = capsys.readouterr()
    assert "[AI Escape MRC] Phase 7 Report" in captured.err
    assert (tmp_path / "stage-progress.jsonl").exists()
    assert (tmp_path / "stage-summaries.jsonl").exists()
    assert result["stage_summaries_path"] == str(tmp_path / "stage-summaries.md")


def test_graph_wrapper_fails_closed_when_start_receipt_cannot_emit(monkeypatch, tmp_path):
    def broken_start(*_args, **_kwargs):
        raise VisibilityContractError("start sink failed", phase="phase_0_research", sink="screen")

    monkeypatch.setattr("ai_escape_mrc.stage_summary.emit_phase_start_summary", broken_start)
    wrapped = _wrap_with_progress("phase_0_research", lambda _state: {"phase_0_complete": True})

    with pytest.raises(VisibilityContractError, match="start sink failed"):
        wrapped({"run_dir": str(tmp_path), "problem": "p"})


def test_graph_wrapper_writes_run_error_when_phase_raises(tmp_path, capsys):
    def phase(_state):
        raise RuntimeError("phase exploded")

    wrapped = _wrap_with_progress("phase_5_prevention_audit", phase)

    with pytest.raises(RuntimeError, match="phase exploded"):
        wrapped({"run_dir": str(tmp_path)})

    captured = capsys.readouterr()
    assert "[AI Escape MRC] FAILED at Phase 5 Prevention Audit" in captured.err
    assert (tmp_path / "run-error.json").exists()
