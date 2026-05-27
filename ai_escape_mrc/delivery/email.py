"""Outlook COM email delivery for AI Escape MRC reports (Windows only).

Fallback chain for reliability:
  1. Outlook COM with path-normalized attachment (retry 3x on HRESULT -2147352567)
  2. If attachment fails: send via Outlook WITHOUT attachment, full report INLINED in HTML body
  3. If Outlook COM itself fails: Telegram sendDocument fallback
"""
import json
import time
from datetime import datetime
from pathlib import Path

from ai_escape_mrc.delivery.recipients import DeliveryRecipients, resolve_delivery_recipients


def send_ai_escape_mrc_report_email(
    report_md: str,
    report_path: Path,
    problem_summary: str,
    recipients: DeliveryRecipients | None = None,
) -> str:
    """Send report via Outlook with robust fallback chain. Returns log string."""
    html_body = _md_to_html(report_md)
    recipients = recipients or resolve_delivery_recipients()
    subject = f"[AI Escape MRC Report] {problem_summary[:100]} - {datetime.now():%Y-%m-%d}"

    # Normalize path once
    norm_path = _normalize_attachment_path(report_path)

    # Try 1: Outlook COM with attachment (retry 3x)
    try:
        result = _send_outlook(recipients, subject, html_body, norm_path, attach=True)
        _log_delivery("outlook_with_attachment", result, recipients)
        return result
    except Exception as e_attach:
        attach_err = f"{type(e_attach).__name__}: {e_attach}"
        print(f"  [email] Outlook attachment failed: {attach_err}")

    # Try 2: Outlook COM WITHOUT attachment, full report inlined in HTML
    try:
        inline_html = _build_inline_report_html(report_md, report_path, problem_summary)
        result = _send_outlook(recipients, subject + " [inline]", inline_html, None, attach=False)
        _log_delivery("outlook_inline_fallback", result, recipients)
        return f"{result} (INLINE FALLBACK: attachment failed: {attach_err})"
    except Exception as e_inline:
        inline_err = f"{type(e_inline).__name__}: {e_inline}"
        print(f"  [email] Outlook inline fallback failed: {inline_err}")

    # Try 3: Telegram sendDocument as last resort
    try:
        tg_log = _send_telegram_document(report_path, problem_summary)
        _log_delivery("telegram_fallback", tg_log, DeliveryRecipients(to="telegram", source="telegram_fallback"))
        return f"{tg_log} (OUTLOOK FAILED: attach={attach_err}; inline={inline_err})"
    except Exception as e_tg:
        tg_err = f"{type(e_tg).__name__}: {e_tg}"
        msg = f"ALL DELIVERY FAILED: outlook_attach={attach_err}; outlook_inline={inline_err}; telegram={tg_err}"
        _log_delivery("all_failed", msg, recipients)
        raise RuntimeError(msg)


def send_consolidated_email(
    report_path: str,
    plan_path: str,
    run_id: str,
    mailto_url: str | None = None,
    recipients: DeliveryRecipients | None = None,
    stage_summaries_path: str | None = None,
    stage_summaries_inline: str | None = None,
) -> dict:
    """Send a single email containing report summary + plan delivery.

    Returns a structured delivery result. Errors are not raised to callers; they
    are surfaced in the result so Phase 10 can print and persist them visibly.

    # WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
    # WIKI-FINDING: phase_7 email-send removed in same commit as graph rewiring
    #   to avoid dual-emission window (coexistence = latent bug).
    # WIKI-ACTION: this function IS the consolidated replacement: single email
    #   containing report + plan delivery details.
    """
    from pathlib import Path as _Path
    recipients = recipients or resolve_delivery_recipients()
    try:
        report = _Path(report_path).read_text(encoding="utf-8") if _Path(report_path).exists() else ""
        plan = _Path(plan_path).read_text(encoding="utf-8") if _Path(plan_path).exists() else ""
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[send_consolidated_email] read error: {err}")
        return _delivery_result(False, "read_error", recipients, error=err)

    summaries = _read_stage_summaries(stage_summaries_path) or stage_summaries_inline or ""
    body_md = f"""# AI Escape MRC Run {run_id} - Report Ready

## Delivery
Recipient: `{recipients.display()}`

## Report
{report_path}

{report or "(report content missing)"}

## Stage Summaries
{stage_summaries_path or "(not available)"}

{summaries or "(no stage summaries recorded)"}

## Plan
{plan_path}

```
{plan or "(plan content missing)"}
```
"""
    try:
        return send_markdown_email(
            subject=f"[AI ESCAPE MRC REPORT READY] Run {run_id}",
            body_md=body_md,
            recipients=recipients,
        )
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[send_consolidated_email] WARN: send_markdown_email failed: {err}")
        return _delivery_result(False, "send_exception", recipients, error=err)


def send_markdown_email(
    subject: str,
    body_md: str,
    recipients: DeliveryRecipients | None = None,
) -> dict:
    """Send a markdown-body email via Outlook COM.

    Returns a structured result with error details on failure.
    """
    html_body = _md_to_html(body_md)
    recipients = recipients or resolve_delivery_recipients()
    try:
        message = _send_outlook(recipients, subject, html_body, None, attach=False)
        _log_delivery("outlook_markdown", message, recipients)
        return _delivery_result(True, "outlook_markdown", recipients, message=message)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        _log_delivery("outlook_markdown_failed", err, recipients)
        print(f"[send_markdown_email] Outlook failed: {err}")
        return _delivery_result(False, "outlook_markdown_failed", recipients, error=err)


def _normalize_attachment_path(report_path: Path) -> Path:
    """Resolve path, verify existence + non-empty, return canonical Windows form."""
    p = Path(report_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Report not found: {p}")
    sz = p.stat().st_size
    if sz == 0:
        raise ValueError(f"Report is empty: {p}")
    # Outlook COM prefers backslashes on Windows
    return p


def _send_outlook(recipients: DeliveryRecipients, subject: str, html_body: str,
                  attach_path: Path | None, attach: bool) -> str:
    """Send via Outlook COM. Retries attachment add on HRESULT errors."""
    import win32com.client

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = recipients.to
    if recipients.cc:
        mail.CC = ";".join(recipients.cc)
    mail.Subject = subject
    mail.HTMLBody = html_body

    if attach and attach_path is not None:
        # Build Windows-style absolute path explicitly
        attach_str = str(attach_path).replace("/", "\\")
        last_err = None
        for attempt in range(1, 4):
            try:
                mail.Attachments.Add(attach_str)
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"  [email] attachment add attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    time.sleep(2)
        if last_err is not None:
            raise last_err

    mail.Send()
    return f"OK: sent to {recipients.display()} at {datetime.now().isoformat()}"


def _delivery_result(
    ok: bool,
    channel: str,
    recipients: DeliveryRecipients,
    *,
    message: str = "",
    error: str | None = None,
) -> dict:
    return {
        "ok": ok,
        "channel": channel,
        "to": recipients.to,
        "cc": list(recipients.cc),
        "source": recipients.source,
        "message": message,
        "error": error,
    }


def _build_inline_report_html(report_md: str, report_path: Path, problem_summary: str) -> str:
    """Build HTML with full report content inlined (for attachment-fail fallback)."""
    banner = (
        "<div style='background:#fff3cd;border:1px solid #ffeeba;padding:10px;"
        "margin-bottom:20px;border-radius:4px'>"
        "<strong>Note:</strong> Attachment could not be added via Outlook COM. "
        f"Full report content is inlined below. Original file path: "
        f"<code>{report_path}</code>"
        "</div>"
    )
    return _md_to_html(report_md, extra_prefix=banner)


def _send_telegram_document(report_path: Path, problem_summary: str) -> str:
    """Last-resort: ship report as Telegram document attachment."""
    import requests

    cfg_path = Path.home() / ".claude" / "telegram.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Telegram config missing: {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    token = cfg["bot_token"]
    chat_id = cfg["group_chat_id"]
    thread_id = cfg.get("topics", {}).get("daily-brief")

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {"chat_id": chat_id, "caption": f"[AI Escape MRC Report] {problem_summary[:200]}"}
    if thread_id:
        data["message_thread_id"] = thread_id
    with open(report_path, "rb") as f:
        files = {"document": (report_path.name, f, "text/markdown")}
        r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    result = r.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")
    return f"OK: sent via Telegram at {datetime.now().isoformat()}"


def _log_delivery(channel: str, result: str, recipients: DeliveryRecipients):
    """Append delivery outcome to ~/.claude/hooks/email-delivery.log."""
    try:
        log_dir = Path.home() / ".claude" / "hooks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "email-delivery.log"
        line = f"{datetime.now().isoformat()}\t{channel}\t{recipients.display()}\t{result}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"  [email] log write failed: {e}")


def _read_stage_summaries(path: str | None, max_chars: int | None = None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8")
    if max_chars is None:
        return text
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _md_to_html(md_text: str, extra_prefix: str = "") -> str:
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
        "code{background:#f4f4f4;padding:2px 4px;border-radius:3px}"
        "</style></head><body>"
        + extra_prefix
        + body
        + "</body></html>"
    )
