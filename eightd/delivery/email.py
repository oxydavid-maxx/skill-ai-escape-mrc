"""Outlook COM email delivery for 8D reports (Windows only)."""
import json
import os
from datetime import datetime
from pathlib import Path


def send_8d_report_email(report_md: str, report_path: Path, problem_summary: str) -> str:
    """Send report via Outlook COM. Returns log string."""
    import win32com.client

    html_body = _md_to_html(report_md)

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = _get_recipient()
    mail.Subject = f"[8D Report] {problem_summary[:100]} - {datetime.now():%Y-%m-%d}"
    mail.HTMLBody = html_body
    if report_path.exists():
        mail.Attachments.Add(str(report_path.resolve()))
    mail.Send()

    return f"OK: sent to {mail.To} at {datetime.now().isoformat()}"


def _get_recipient() -> str:
    cfg_path = Path.home() / ".claude" / "email.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))["recipient"]
        except Exception:
            pass
    return os.environ.get("CLAUDE_EIGHTD_EMAIL", "")


def _md_to_html(md_text: str) -> str:
    try:
        import markdown
        body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        import html as html_mod
        body = (
            "<pre style='white-space:pre-wrap;font-family:monospace'>"
            + html_mod.escape(md_text)
            + "</pre>"
        )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "body{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;"
        "padding:20px;line-height:1.6}"
        "h1{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}"
        "h2{color:#2980b9;margin-top:30px}"
        "table{border-collapse:collapse;margin:15px 0}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
        "th{background:#f4f4f4}"
        "</style></head><body>"
        + body
        + "</body></html>"
    )
