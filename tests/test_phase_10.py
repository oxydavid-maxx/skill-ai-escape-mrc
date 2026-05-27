"""Tests for Phase 10 final delivery."""
import json
from pathlib import Path
from unittest.mock import patch


def _state(tmp_path):
    plan_path = tmp_path / "plan.md"
    report_path = tmp_path / "report.md"
    summaries_path = tmp_path / "stage-summaries.md"
    plan_path.write_text("# Plan\n\n- step 1\n", encoding="utf-8")
    report_path.write_text("# Report\n\nSummary.", encoding="utf-8")
    summaries_path.write_text("### Phase 9 Plan\n- Plan tasks: one.\n", encoding="utf-8")
    return {
        "run_id": "test-10",
        "run_dir": str(tmp_path),
        "report_path": str(report_path),
        "plan_path": str(plan_path),
        "stage_summaries_path": str(summaries_path),
        "actions_count": 5,
        "user_email": "user@example.com",
        "operator_email": "operator@example.com",
    }


def test_phase_10_writes_delivery_status_on_email_success(tmp_path, capsys):
    from ai_escape_mrc.phases.phase_10_emit_and_wait import phase_10_emit_and_wait

    with patch(
        "ai_escape_mrc.delivery.email.send_consolidated_email",
        return_value={
            "ok": True,
            "channel": "test",
            "to": "user@example.com",
            "cc": ["operator@example.com"],
            "source": "user_payload",
            "message": "sent",
            "error": None,
        },
    ):
        result = phase_10_emit_and_wait(_state(tmp_path))

    assert result["phase_10_complete"] is True
    assert result["email_delivery_result"] == "sent"
    status = json.loads(Path(result["delivery_status_path"]).read_text(encoding="utf-8"))
    assert status["report_path"].endswith("report.md")
    assert status["plan_path"].endswith("plan.md")
    assert status["recipient_to"] == "user@example.com"
    assert status["recipient_cc"] == ["operator@example.com"]
    assert status["email_delivery_result"] == "sent"
    captured = capsys.readouterr()
    assert "[AI Escape MRC] Final Delivery" in captured.err
    assert "Email: sent" in captured.err
    assert "Report:" in captured.err


def test_phase_10_records_email_failure_without_losing_artifacts(tmp_path, capsys):
    from ai_escape_mrc.phases.phase_10_emit_and_wait import phase_10_emit_and_wait

    with patch(
        "ai_escape_mrc.delivery.email.send_consolidated_email",
        side_effect=RuntimeError("Outlook profile missing"),
    ):
        result = phase_10_emit_and_wait(_state(tmp_path))

    assert result["phase_10_complete"] is True
    assert result["email_delivery_result"] == "failed"
    assert "Outlook profile missing" in result["email_delivery_error"]
    status = json.loads(Path(result["delivery_status_path"]).read_text(encoding="utf-8"))
    assert Path(status["report_path"]).exists()
    assert Path(status["plan_path"]).exists()
    assert status["email_delivery_result"] == "failed"
    assert "Outlook profile missing" in status["email_delivery_error"]
    captured = capsys.readouterr()
    assert "Email: failed" in captured.err
    assert "Outlook profile missing" in captured.err
    assert "Manual fallback" in captured.err
