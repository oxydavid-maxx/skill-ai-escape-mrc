"""Phase 10: final report/plan delivery.

This is the terminal phase of the local AI Escape MRC graph. It delivers the
already-rendered report and implementation plan, records the delivery outcome,
and never dispatches an execution child.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_escape_mrc.delivery.recipients import DeliveryRecipients, resolve_delivery_recipients


def phase_10_emit_and_wait(state: dict) -> dict:
    run_id = state["run_id"]
    run_dir = Path(state.get("run_dir") or Path(state["plan_path"]).parent)
    report_path = str(state.get("report_path") or "")
    plan_path = str(state.get("plan_path") or "")
    recipients = resolve_delivery_recipients(
        user_email=state.get("user_email"),
        operator_email=state.get("operator_email"),
    )

    try:
        from ai_escape_mrc.delivery.email import send_consolidated_email

        delivery = send_consolidated_email(
            report_path=report_path,
            plan_path=plan_path,
            run_id=run_id,
            recipients=recipients,
            stage_summaries_path=state.get("stage_summaries_path"),
            stage_summaries_inline=state.get("screen_summary"),
        )
    except Exception as exc:
        delivery = _delivery_exception(exc, recipients)

    delivery = _normalize_delivery_result(delivery, recipients)
    delivery_status_path = run_dir / "delivery-status.json"
    delivery_doc = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_path": report_path,
        "plan_path": plan_path,
        "stage_summaries_path": state.get("stage_summaries_path"),
        "recipient_to": recipients.to,
        "recipient_cc": list(recipients.cc),
        "recipient_source": recipients.source,
        "delivery_status_path": str(delivery_status_path),
        "email_delivery_result": "sent" if delivery.get("ok") else "failed",
        "email_delivery_error": delivery.get("error"),
        "email_delivery": delivery,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    delivery_status_path.write_text(
        json.dumps(delivery_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _print_final_delivery_block(delivery_doc)

    return {
        "phase_10_complete": True,
        "delivery_status_path": str(delivery_status_path),
        "email_delivery_result": delivery_doc["email_delivery_result"],
        "email_delivery_error": delivery_doc["email_delivery_error"],
        **recipients.as_gate_fields(),
    }


def _print_final_delivery_block(delivery_doc: dict[str, Any]) -> None:
    lines = [
        "[AI Escape MRC] Final Delivery",
        f"- Run: {delivery_doc.get('run_id') or '(missing)'}",
        f"- Email: {delivery_doc.get('email_delivery_result') or '(missing)'}",
        f"- Recipient: To={delivery_doc.get('recipient_to') or '(missing)'}; "
        f"Cc={delivery_doc.get('recipient_cc') or '(none)'}; "
        f"source={delivery_doc.get('recipient_source') or '(missing)'}",
        f"- Report: {delivery_doc.get('report_path') or '(missing)'}",
        f"- Plan: {delivery_doc.get('plan_path') or '(missing)'}",
        f"- Stage summaries: {delivery_doc.get('stage_summaries_path') or '(missing)'}",
        f"- Delivery status: {delivery_doc.get('delivery_status_path') or '(missing)'}",
    ]
    if delivery_doc.get("email_delivery_error"):
        lines.append(f"- Email error: {delivery_doc['email_delivery_error']}")
        lines.append("- Manual fallback: open the report and plan paths above and send them to the requester manually.")
    print("\n".join(lines), file=sys.stderr, flush=True)


def _delivery_exception(exc: BaseException, recipients: DeliveryRecipients) -> dict[str, Any]:
    return {
        "ok": False,
        "channel": "exception",
        "to": recipients.to,
        "cc": list(recipients.cc),
        "source": recipients.source,
        "message": "",
        "error": f"{type(exc).__name__}: {exc}",
    }


def _normalize_delivery_result(value: Any, recipients: DeliveryRecipients) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "ok": bool(value.get("ok")),
            "channel": str(value.get("channel") or "unknown"),
            "to": value.get("to") or recipients.to,
            "cc": list(value.get("cc") or recipients.cc),
            "source": value.get("source") or recipients.source,
            "message": str(value.get("message") or ""),
            "error": value.get("error"),
        }
    if isinstance(value, bool):
        return {
            "ok": value,
            "channel": "legacy_bool",
            "to": recipients.to,
            "cc": list(recipients.cc),
            "source": recipients.source,
            "message": "legacy boolean delivery result",
            "error": None if value else "legacy sender returned False",
        }
    return {
        "ok": False,
        "channel": "invalid_result",
        "to": recipients.to,
        "cc": list(recipients.cc),
        "source": recipients.source,
        "message": "",
        "error": f"Unexpected delivery result type: {type(value).__name__}",
    }
