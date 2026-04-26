from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from pydantic import ValidationError

from eightd.managed_agent.output_schema import CloudPayload

# WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
# WIKI-FINDING: replaces run_8d.py + LangGraph FSM atomically in Phase C
# WIKI-ACTION: this file is the new entry point; legacy run_8d.py deleted in same commit (Phase C)
# WIKI-CONSULTED: degraded-emission-with-warning
# WIKI-FINDING: producer must validate output before emission; R13 fail-closed
# WIKI-ACTION: handle_session_complete raises ValidationError before writing any artifact
# WIKI-CONSULTED: claude-agent-sdk-patterns
# WIKI-FINDING: use anthropic SDK (client.beta.sessions) instead of raw requests to /v1/agents/sessions
# WIKI-ACTION: all API calls go through anthropic.Anthropic(). agent_id + input not a valid session-create schema.

ANTHROPIC_BETA = "managed-agents-2026-04-01"
POLL_INTERVAL_SEC = 300  # 5 min


def _get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def ensure_agent(client: anthropic.Anthropic, system_prompt: str) -> str:
    """Create (or reuse by name) the skill-8d-mrc-v1 agent. Returns agent_id.

    Anthropic Managed Agents uses an agent registry: agents are persistent objects
    you create once (with model + system prompt + tools), then reference by ID in
    session.create(). We list agents to avoid duplicate creation.
    """
    agent_name = "skill-8d-mrc-v1"
    betas: list[anthropic.types.AnthropicBeta] = [ANTHROPIC_BETA]

    # Check if agent already exists
    agents_page = client.beta.agents.list(betas=betas)
    for ag in agents_page:
        if ag.name == agent_name:
            return ag.id

    # Create agent from yaml config
    agent = client.beta.agents.create(
        model="claude-opus-4-6",
        name=agent_name,
        system=system_prompt,
        tools=[
            {"type": "agent_toolset_20260401"},
        ],
        description=(
            "8D Method-of-Resolving-Conflict analyst for ecosystem failure modes. "
            "Runs the full 12-phase forensic in a single Managed Agent session; "
            "returns structured payload (report, actions, plan) for local persistence."
        ),
        betas=betas,
    )
    return agent.id


def ensure_environment(client: anthropic.Anthropic) -> str:
    """Create (or reuse) an execution environment. Returns environment_id."""
    betas: list[anthropic.types.AnthropicBeta] = [ANTHROPIC_BETA]
    env_name = "skill-8d-mrc-env"

    envs_page = client.beta.environments.list(betas=betas)
    for env in envs_page:
        if env.name == env_name:
            return env.id

    env = client.beta.environments.create(
        name=env_name,
        betas=betas,
    )
    return env.id


def create_cloud_session(problem: str, agent_id: str, api_key: str) -> str:
    """Create a Managed Agents session and send the problem as the first user message.

    Returns session_id.

    Flow (per SDK schema discovered 2026-04-26):
    1. sessions.create(agent={"id": agent_id, "type": "agent"}, environment_id=...)
    2. sessions.events.send(session_id, events=[{"type": "user.message", ...}])
    """
    client = _get_client(api_key)
    betas: list[anthropic.types.AnthropicBeta] = [ANTHROPIC_BETA]

    system_prompt = _load_system_prompt()
    agent_id_resolved = ensure_agent(client, system_prompt)
    env_id = ensure_environment(client)

    session = client.beta.sessions.create(
        agent={"id": agent_id_resolved, "type": "agent"},
        environment_id=env_id,
        title=f"8D run — {problem[:60]}",
        betas=betas,
    )
    session_id = session.id

    # Send the problem as the first user message to kick off the agent
    client.beta.sessions.events.send(
        session_id,
        events=[
            {
                "type": "user.message",
                "content": [{"type": "text", "text": problem}],
            }
        ],
        betas=betas,
    )

    return session_id


def _load_system_prompt() -> str:
    """Load system_prompt.md relative to this file."""
    sp_path = Path(__file__).parent / "eightd" / "managed_agent" / "system_prompt.md"
    return sp_path.read_text(encoding="utf-8")


def _extract_agent_output(session_id: str, client: anthropic.Anthropic) -> dict | None:
    """Poll events to find the agent's final text output and parse JSON payload.

    Returns the parsed CloudPayload dict if found, else None.
    """
    import re, json as _json
    betas: list[anthropic.types.AnthropicBeta] = [ANTHROPIC_BETA]

    events_page = client.beta.sessions.events.list(session_id, betas=betas)
    for event in events_page:
        # Agent message events carry the final structured output
        event_type = getattr(event, "type", "") or ""
        if "agent.message" in event_type or event_type == "agent_message":
            content = getattr(event, "content", []) or []
            for block in content:
                text = getattr(block, "text", "") or ""
                # Try to extract JSON payload from the agent's text response
                # Agent is instructed to return CloudPayload JSON as final response
                json_match = re.search(r"\{[\s\S]*\}", text)
                if json_match:
                    try:
                        return _json.loads(json_match.group(0))
                    except Exception:
                        continue
    return None


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
        import requests as _req
        cfg = json.loads((Path.home() / ".claude" / "telegram.json").read_text(encoding="utf-8"))
        token = cfg["bot_token"]
        chat_id = cfg["group_chat_id"]
        thread = cfg["topics"]["diagnostics"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        _req.post(url, json={
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
    client = _get_client(api_key)
    betas: list[anthropic.types.AnthropicBeta] = [ANTHROPIC_BETA]

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
        try:
            session = client.beta.sessions.retrieve(session_id, betas=betas)
            status = getattr(session, "status", "unknown")
        except Exception as e:
            print(f"[trigger_8d] poll error: {e}; retrying next interval", file=sys.stderr)
            _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` poll_error: {str(e)[:100]}")
            continue

        # Log heartbeat per event
        try:
            events_page = client.beta.sessions.events.list(session_id, betas=betas)
            for ev in events_page:
                ev_type = getattr(ev, "type", "?")
                print(f"[heartbeat] {datetime.now().isoformat(timespec='seconds')} {ev_type}", file=sys.stderr)
                _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` 8D `{run_id[:16]}` {ev_type}")
        except Exception:
            pass

        if status in ("idle", "terminated"):
            # Session completed — extract payload from agent message events
            payload = _extract_agent_output(session_id, client) or {}
            if not payload:
                err_body = (
                    f"# 8D Cloud Session Produced No Parseable Payload\n\n"
                    f"Run ID: {run_id}\nSession: {session_id}\nStatus: {status}\n\n"
                    f"The session ended but no JSON payload was found in agent message events."
                )
                _send_error_email(run_id, "no payload found", err_body)
                print(f"ERROR: no parseable payload from session {session_id}", file=sys.stderr)
                return 2

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

        print(f"[trigger_8d] session {session_id} status={status}; waiting...", file=sys.stderr)


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
