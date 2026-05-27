"""Regression tests for run_ai_escape_mrc final-delivery CLI behavior."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_fake_saver(mock_saver):
    ctx = MagicMock()
    mock_saver.return_value.__enter__ = lambda s: ctx
    mock_saver.return_value.__exit__ = MagicMock(return_value=False)
    return ctx


def test_final_delivery_success_exits_0_and_prints_summary(tmp_path, capsys):
    import run_ai_escape_mrc

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "run_id": "run-ok",
        "phase_10_complete": True,
        "email_delivery_result": "sent",
        "recipient_to": "user@example.com",
        "recipient_cc": ["operator@example.com"],
        "recipient_source": "user_payload",
        "report_path": str(tmp_path / "report.md"),
        "plan_path": str(tmp_path / "plan.md"),
        "stage_summaries_path": str(tmp_path / "stage-summaries.md"),
        "delivery_status_path": str(tmp_path / "delivery-status.json"),
        "screen_summary": "### Phase 10 Final Delivery\n- Delivery outcome: email sent.",
    }

    with patch("run_ai_escape_mrc.build_graph", return_value=fake_graph), \
         patch("run_ai_escape_mrc.SqliteSaver.from_conn_string") as mock_saver, \
         patch("run_ai_escape_mrc.RUNS_DIR", tmp_path), \
         patch("ai_escape_mrc.progress.init", return_value=None), \
         patch("ai_escape_mrc.heartbeat.start", return_value=None), \
         patch("sys.argv", ["run_ai_escape_mrc", "some test problem"]):
        _make_fake_saver(mock_saver)
        rc = run_ai_escape_mrc.main()

    assert rc == 0
    captured = capsys.readouterr()
    assert "[AI Escape MRC] Final Delivery" in captured.err
    assert "Email: sent" in captured.err
    assert "Report:" in captured.err


def test_final_delivery_email_failure_exits_3_and_prints_fallback(tmp_path, capsys):
    import run_ai_escape_mrc

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "run_id": "run-fail",
        "phase_10_complete": True,
        "email_delivery_result": "failed",
        "email_delivery_error": "Outlook profile missing",
        "recipient_to": "user@example.com",
        "recipient_cc": [],
        "recipient_source": "user_payload",
        "report_path": str(tmp_path / "report.md"),
        "plan_path": str(tmp_path / "plan.md"),
        "stage_summaries_path": str(tmp_path / "stage-summaries.md"),
        "delivery_status_path": str(tmp_path / "delivery-status.json"),
    }

    with patch("run_ai_escape_mrc.build_graph", return_value=fake_graph), \
         patch("run_ai_escape_mrc.SqliteSaver.from_conn_string") as mock_saver, \
         patch("run_ai_escape_mrc.RUNS_DIR", tmp_path), \
         patch("ai_escape_mrc.progress.init", return_value=None), \
         patch("ai_escape_mrc.heartbeat.start", return_value=None), \
         patch("sys.argv", ["run_ai_escape_mrc", "some test problem"]):
        _make_fake_saver(mock_saver)
        rc = run_ai_escape_mrc.main()

    assert rc == 3
    captured = capsys.readouterr()
    assert "Email: failed" in captured.err
    assert "Outlook profile missing" in captured.err
    assert "Manual fallback" in captured.err


def test_approval_resume_flags_are_removed(tmp_path, capsys):
    import run_ai_escape_mrc

    with patch("run_ai_escape_mrc.RUNS_DIR", tmp_path), \
         patch("sys.argv", ["run_ai_escape_mrc", "--resume", "run-old", "--approve"]):
        rc = run_ai_escape_mrc.main()

    assert rc == 2
    captured = capsys.readouterr()
    assert "Phase 11 approval execution has been removed" in captured.err
