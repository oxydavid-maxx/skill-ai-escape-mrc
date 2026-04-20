import sys
from unittest.mock import patch, MagicMock
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Outlook COM only on Windows"
)


def test_send_email_calls_outlook(tmp_path):
    from eightd.delivery.email import send_8d_report_email

    fake_report = tmp_path / "r.md"
    fake_report.write_text("# test", encoding="utf-8")

    with patch("win32com.client.Dispatch") as mock_dispatch, \
         patch("eightd.delivery.email._get_recipient", return_value="test@example.com"):
        mock_app = MagicMock()
        mock_mail = MagicMock()
        mock_app.CreateItem.return_value = mock_mail
        mock_dispatch.return_value = mock_app

        log = send_8d_report_email("# test md", fake_report, "test problem")

    assert mock_mail.Send.called
    assert "OK" in log
