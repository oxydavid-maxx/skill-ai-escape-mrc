"""Phase 10 — emit single consolidated email + gate file, then interrupt()
for human approval via either Portal A (email reply) or Portal B (Claude session).

Per spec 2026-04-25-sdk-auto-dispatch-design.md.

WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
WIKI-FINDING: created_at must NOT be used as freshness signal.
WIKI-ACTION: created_at recorded for audit only; phase_11 trusts approved:true content.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from langgraph.types import interrupt


def phase_10_emit_and_wait(state: dict) -> dict:
    run_id = state["run_id"]
    plan_path = Path(state["plan_path"])
    report_path = state.get("report_path", "")
    plan_inline = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""

    gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"
    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gate_dir / f"{run_id}.json"

    gate_doc = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_path": str(report_path),
        "plan_path": str(plan_path),
        "plan_inline": plan_inline,
        "actions_count": state.get("actions_count", 0),
        "approved": False,
        "approved_at": None,
        "via": None,
        "rejected": False,
        "rejected_reason": None,
    }
    gate_path.write_text(json.dumps(gate_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    # Send consolidated email (best-effort; gate file is the source of truth)
    try:
        from eightd.delivery.email import send_consolidated_email
        send_consolidated_email(
            report_path=str(report_path),
            plan_path=str(plan_path),
            run_id=run_id,
            mailto_url=f"mailto:?subject=APPROVE%20{run_id}",
        )
    except Exception:
        pass  # Portal B remains as fallback

    approval = interrupt({
        "approval_pending": True,
        "gate_path": str(gate_path),
        "plan_path": str(plan_path),
        "run_id": run_id,
    })
    return {"approval": approval, "phase_10_complete": True}
