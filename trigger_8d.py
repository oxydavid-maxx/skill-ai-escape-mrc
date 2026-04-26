from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pydantic import ValidationError

from eightd.managed_agent.output_schema import CloudPayload

# WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
# WIKI-FINDING: replaces run_8d.py + LangGraph FSM atomically in Phase C
# WIKI-ACTION: this file is the new entry point; legacy run_8d.py deleted in same commit (Phase C)
# WIKI-CONSULTED: degraded-emission-with-warning
# WIKI-FINDING: producer must validate output before emission; R13 fail-closed
# WIKI-ACTION: handle_session_complete raises ValidationError before writing any artifact

ANTHROPIC_BETA_HEADER = "managed-agents-2026-04-01"
ANTHROPIC_API_BASE = "https://api.anthropic.com"
POLL_INTERVAL_SEC = 300  # 5 min


def create_cloud_session(problem: str, agent_id: str, api_key: str) -> str:
    """POST to create a Managed Agents session. Returns session_id."""
    url = f"{ANTHROPIC_API_BASE}/v1/agents/sessions"
    headers = {
        "anthropic-beta": ANTHROPIC_BETA_HEADER,
        "x-api-key": api_key,
        "content-type": "application/json",
    }
    resp = requests.post(url, headers=headers, json={"agent_id": agent_id, "input": problem}, timeout=30)
    resp.raise_for_status()
    return resp.json()["session_id"]


def handle_session_complete(
    session_id: str, run_dir: Path, payload: dict, gate_dir: Path
) -> dict:
    """Validate payload (R13 fail-closed), write artifacts, write gate file.

    Raises ValidationError if payload does not match CloudPayload schema.
    Per R13: never write partial artifacts; refuse on malformed payload.
    """
    validated = CloudPayload(**payload)  # raises ValidationError on bad data

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.md").write_text(validated.report_md, encoding="utf-8")
    (run_dir / "plan.md").write_text(validated.plan_md, encoding="utf-8")
    (run_dir / "actions.json").write_text(
        json.dumps([a.model_dump() for a in validated.actions_json], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_file = gate_dir / f"{run_dir.name}.json"
    gate_doc = {
        "run_id": run_dir.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_path": str(run_dir / "report.md"),
        "plan_path": str(run_dir / "plan.md"),
        "plan_inline": validated.plan_md,
        "actions_count": len(validated.actions_json),
        "approved": False, "approved_at": None, "via": None,
        "rejected": False, "rejected_reason": None,
        "cloud_session_id": session_id,
    }
    gate_file.write_text(json.dumps(gate_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    _send_completion_email(run_id=run_dir.name, run_dir=run_dir, gate_doc=gate_doc)
    return {"session_id": session_id, "gate_file": str(gate_file)}


def _post_telegram_heartbeat(message: str) -> None:
    """Best-effort Telegram diagnostics post; never raises."""
    try:
        cfg = json.loads((Path.home() / ".claude" / "telegram.json").read_text(encoding="utf-8"))
        token = cfg["bot_token"]
        chat_id = cfg["group_chat_id"]
        thread = cfg["topics"]["diagnostics"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id, "message_thread_id": thread,
            "text": message[:4000], "parse_mode": "Markdown",
        }, timeout=10)
    except Exception:
        pass  # heartbeat must never crash the run


def _send_completion_email(run_id: str, run_dir: Path, gate_doc: dict) -> bool:
    """Send consolidated email with report path + plan preview + approval instructions.
    Per R13: all inline; no see-file pointers for required actions.
    """
    try:
        from eightd.delivery.email import send_markdown_email
    except ImportError:
        print("WARN: send_markdown_email unavailable; gate file is the source of truth", file=sys.stderr)
        return False
    plan_inline = gate_doc.get("plan_inline", "")
    plan_first50 = "\n".join(plan_inline.splitlines()[:50])
    plan_truncated = "..." if len(plan_inline.splitlines()) > 50 else ""
    body = (
        f"# 8D Run {run_id} -- Approval Pending\n\n"
        f"**Report path:** {gate_doc.get('report_path', '(none)')}\n\n"
        f"## Plan (first 50 lines)\n```\n{plan_first50}\n{plan_truncated}\n```\n\n"
        f"## To approve\nReply with subject: `APPROVE {run_id}`\n"
        f"Or in Claude Code session: `approve {run_id}`\n\n"
        f"## To reject\nReply with subject: `REJECT {run_id}`\n"
        f"Or: `reject {run_id}`\n"
    )
    return send_markdown_email(subject=f"[8D APPROVAL PENDING] Run {run_id}", body_md=body)


def _send_error_email(run_id: str, error_subject: str, error_body: str) -> bool:
    """Send a self-contained error email -- recipient does not need to look anywhere else."""
    try:
        from eightd.delivery.email import send_markdown_email
    except ImportError:
        return False
    return send_markdown_email(subject=f"[8D ERROR] {run_id}: {error_subject}", body_md=error_body)


def _cmd_run(problem: str) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1
    run_id = f"run-{int(time.time())}-{os.urandom(4).hex()}"
    run_dir = Path(__file__).parent / "runs" / run_id
    gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"

    try:
        session_id = create_cloud_session(problem, agent_id="skill-8d-mrc-v1", api_key=api_key)
    except Exception as e:
        err_body = f"# Session Creation Failed\n\nRun ID: {run_id}\nError: {type(e).__name__}: {e}\n"
        _send_error_email(run_id, "session creation failed", err_body)
        print(f"ERROR: session creation failed: {e}", file=sys.stderr)
        return 1

    print(f"[trigger_8d] session created: {session_id}; run_id: {run_id}")
    _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` 8D `{run_id[:20]}` session_created")

    while True:
        time.sleep(POLL_INTERVAL_SEC)
        events_url = f"{ANTHROPIC_API_BASE}/v1/agents/sessions/{session_id}/events"
        headers = {"anthropic-beta": ANTHROPIC_BETA_HEADER, "x-api-key": api_key}

        try:
            resp = requests.get(events_url, headers=headers, timeout=30)
            resp.raise_for_status()
            events_doc = resp.json()
        except Exception as e:
            print(f"[trigger_8d] poll error: {e}; retrying next interval", file=sys.stderr)
            _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` poll_error: {str(e)[:100]}")
            continue

        status = events_doc.get("status", "unknown")
        for ev in events_doc.get("events", []):
            phase = ev.get("phase", "?")
            kind = ev.get("event", "?")
            print(f"[heartbeat] {datetime.now().isoformat(timespec='seconds')} {phase} {kind}", file=sys.stderr)
            _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` 8D `{run_id[:16]}` {phase} {kind}")

        if status == "completed":
            payload = events_doc.get("payload") or {}
            try:
                handle_session_complete(session_id, run_dir, payload, gate_dir)
                print(f"[trigger_8d] gate written; run_id: {run_id}")
                _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` 8D `{run_id[:20]}` completed")
                return 0
            except ValidationError as e:
                err_body = (
                    f"# 8D Payload Schema Validation Failed\n\n"
                    f"Run ID: {run_id}\nSession: {session_id}\n\n"
                    f"## Validation Errors\n```\n{e}\n```\n\n"
                    f"No artifacts written (R13 fail-closed)."
                )
                _send_error_email(run_id, "payload schema invalid", err_body)
                print(f"ERROR: payload schema validation failed:\n{e}", file=sys.stderr)
                return 2

        if status in ("failed", "errored"):
            err_body = f"# 8D Cloud Session Failed\n\nRun ID: {run_id}\nSession: {session_id}\nStatus: {status}\n"
            _send_error_email(run_id, f"session status={status}", err_body)
            print(f"ERROR: session {session_id} ended with status={status}", file=sys.stderr)
            return 2


def _cmd_status(run_id: str) -> int:
    gate = Path.home() / ".claude" / ".pending-8d-approvals" / f"{run_id}.json"
    if not gate.exists():
        print(f"No pending approval for {run_id}")
        return 0
    print(gate.read_text(encoding="utf-8"))
    return 0


def _cmd_resume_approval(run_id: str, approve: bool, reject_reason) -> int:
    gate_file = Path.home() / ".claude" / ".pending-8d-approvals" / f"{run_id}.json"
    if not gate_file.exists():
        print(f"ERROR: no gate file for {run_id}", file=sys.stderr)
        return 1
    doc = json.loads(gate_file.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    if approve:
        doc.update({"approved": True, "approved_at": now, "via": "cli"})
    else:
        doc.update({"approved": False, "rejected": True, "rejected_reason": reject_reason, "via": "cli"})
    gate_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    if not approve:
        print(f"[trigger_8d] {run_id} rejected: {reject_reason}")
        return 0
    plan_path = doc.get('plan_path', '(see gate file)')
    print(f"[trigger_8d] {run_id} approved.")
    print(f"[trigger_8d] Plan at: {plan_path}")
    print(f"[trigger_8d] In Claude Code session: execute the plan at {plan_path}")
    print(f"[trigger_8d] Claude will invoke superpowers:executing-plans automatically.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="trigger_8d")
    ap.add_argument("problem", nargs="?")
    ap.add_argument("--resume", dest="resume_id")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--reject", metavar="REASON")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.resume_id and args.status:
        return _cmd_status(args.resume_id)
    if args.resume_id and (args.approve or args.reject):
        return _cmd_resume_approval(args.resume_id, args.approve, args.reject)
    if args.problem:
        return _cmd_run(args.problem)
    ap.error("must provide problem OR --resume <id>")
    return 2


if __name__ == "__main__":
    sys.exit(main())