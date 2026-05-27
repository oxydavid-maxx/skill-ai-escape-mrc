import sys
from unittest.mock import patch, MagicMock
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Outlook COM only on Windows"
)


def test_send_email_calls_outlook(tmp_path):
    from ai_escape_mrc.delivery.email import send_ai_escape_mrc_report_email
    from ai_escape_mrc.delivery.recipients import DeliveryRecipients

    fake_report = tmp_path / "r.md"
    fake_report.write_text("# test", encoding="utf-8")

    with patch("win32com.client.Dispatch") as mock_dispatch, \
         patch("ai_escape_mrc.delivery.email._log_delivery") as mock_log_delivery:
        mock_app = MagicMock()
        mock_mail = MagicMock()
        mock_app.CreateItem.return_value = mock_mail
        mock_dispatch.return_value = mock_app

        log = send_ai_escape_mrc_report_email(
            "# test md",
            fake_report,
            "test problem",
            recipients=DeliveryRecipients(
                to="user@example.com",
                cc=("operator@example.com",),
                source="user_payload",
            ),
        )

    assert mock_mail.Send.called
    assert mock_mail.To == "user@example.com"
    assert mock_mail.CC == "operator@example.com"
    mock_log_delivery.assert_called_once()
    assert "OK" in log


def test_consolidated_email_is_report_ready_not_approval(tmp_path):
    from ai_escape_mrc.delivery.email import send_consolidated_email
    from ai_escape_mrc.delivery.recipients import DeliveryRecipients

    report = tmp_path / "report.md"
    plan = tmp_path / "plan.md"
    summaries = tmp_path / "stage-summaries.md"
    report.write_text("# Report\n\nExecutive summary.\n\nFULL_REPORT_TAIL", encoding="utf-8")
    plan.write_text("# Plan\n\n## Task 1: Do thing\n\nFULL_PLAN_TAIL\n", encoding="utf-8")
    summaries.write_text("### Phase 1\n- Detailed discussion.\n\nFULL_SUMMARY_TAIL\n", encoding="utf-8")

    with patch("ai_escape_mrc.delivery.email.send_markdown_email") as mock_send:
        mock_send.return_value = {
            "ok": True,
            "channel": "test",
            "to": "user@example.com",
            "cc": [],
            "source": "user_payload",
            "message": "sent",
            "error": None,
        }
        result = send_consolidated_email(
            report_path=str(report),
            plan_path=str(plan),
            run_id="run-test",
            recipients=DeliveryRecipients(to="user@example.com", source="user_payload"),
            stage_summaries_path=str(summaries),
        )

    assert result["ok"] is True
    kwargs = mock_send.call_args.kwargs
    assert "REPORT READY" in kwargs["subject"]
    assert "Approval Pending" not in kwargs["body_md"]
    assert "To approve" not in kwargs["body_md"]
    assert str(report) in kwargs["body_md"]
    assert str(plan) in kwargs["body_md"]
    assert "FULL_REPORT_TAIL" in kwargs["body_md"]
    assert "FULL_PLAN_TAIL" in kwargs["body_md"]
    assert "FULL_SUMMARY_TAIL" in kwargs["body_md"]


def test_consolidated_email_does_not_truncate_detailed_content(tmp_path):
    from ai_escape_mrc.delivery.email import send_consolidated_email
    from ai_escape_mrc.delivery.recipients import DeliveryRecipients

    report = tmp_path / "report.md"
    plan = tmp_path / "plan.md"
    summaries = tmp_path / "stage-summaries.md"
    report.write_text("# Report\n" + "\n".join(f"report line {i}" for i in range(400)), encoding="utf-8")
    plan.write_text("# Plan\n" + "\n".join(f"plan line {i}" for i in range(120)), encoding="utf-8")
    summaries.write_text("\n".join(f"summary line {i}" for i in range(160)), encoding="utf-8")

    with patch("ai_escape_mrc.delivery.email.send_markdown_email") as mock_send:
        mock_send.return_value = {
            "ok": True,
            "channel": "test",
            "to": "user@example.com",
            "cc": [],
            "source": "user_payload",
            "message": "sent",
            "error": None,
        }
        send_consolidated_email(
            report_path=str(report),
            plan_path=str(plan),
            run_id="run-test",
            recipients=DeliveryRecipients(to="user@example.com", source="user_payload"),
            stage_summaries_path=str(summaries),
        )

    body = mock_send.call_args.kwargs["body_md"]
    assert "report line 399" in body
    assert "plan line 119" in body
    assert "summary line 159" in body
