"""CLI entry point for 8D MRC LangGraph pipeline."""
import argparse
import shutil
import sys
import time
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from eightd.graph import build_graph

RUNS_DIR = Path(__file__).parent / "runs"
RUN_RETENTION_DAYS = 30


def _isonow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(prog="run_8d")
    ap.add_argument("problem", nargs="?", help="Problem description")
    ap.add_argument("--resume", dest="resume_id")
    ap.add_argument("--gc", action="store_true", help="Clean runs older than 30d")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approve", action="store_true",
                    help="Resume an interrupted run with approval payload")
    ap.add_argument("--reject", metavar="REASON",
                    help="Resume an interrupted run with rejection payload")
    ap.add_argument("--status", action="store_true",
                    help="Show pending-approval state without resuming")
    args = ap.parse_args()

    if args.gc:
        gc_runs()
        return 0

    if not args.problem and not args.resume_id:
        ap.error("problem is required (or use --resume <run_id>)")

    run_id = args.resume_id or f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id

    # --approve / --reject / --status: approval-gate resume path
    if args.resume_id and (args.approve or args.reject or args.status):
        import json as _json
        from langgraph.types import Command
        gate = Path.home() / ".claude" / ".pending-8d-approvals" / f"{args.resume_id}.json"

        if args.status:
            if not gate.exists():
                print(f"No pending approval for {args.resume_id}")
                return 0
            print(gate.read_text(encoding="utf-8"))
            return 0

        # Validate gate file and build resume payload
        if args.approve:
            if not gate.exists():
                print(f"ERROR: gate file missing: {gate}", file=sys.stderr)
                return 1
            doc = _json.loads(gate.read_text(encoding="utf-8"))
            # Flip gate to {approved: true, via: cli} for portal symmetry
            doc.update({"approved": True, "approved_at": _isonow(), "via": "cli"})
            gate.write_text(_json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            resume_payload = {"approved": True, "via": "cli"}
        else:  # --reject
            resume_payload = {
                "approved": False,
                "rejected": True,
                "rejected_reason": args.reject,
                "via": "cli",
            }

        db_path = (RUNS_DIR / args.resume_id) / "checkpoint.db"
        with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": args.resume_id, "recursion_limit": 100}}
            final_state = graph.invoke(Command(resume=resume_payload), config=config)
        if final_state.get("phase_11_complete"):
            # Cleanup gate file on successful execution
            if gate.exists():
                gate.unlink()
            return 0
        return 2

    run_dir.mkdir(parents=True, exist_ok=True)

    db_path = run_dir / "checkpoint.db"

    if args.dry_run:
        print(f"Would invoke graph with run_id={run_id}")
        return 0

    # Init progress logging (emits per-event records to run_dir/progress.jsonl)
    try:
        from eightd import progress as _progress
        _progress.init(run_dir)
    except Exception:
        pass

    # Start the heartbeat daemon thread. Emits a human-readable progress summary
    # every HEARTBEAT_INTERVAL_SEC (default 300s) to stderr and optionally to the
    # Telegram diagnostics topic. Satisfies the requirement in
    # ~/.claude/feedback_skill_progress_reporting.md that long-running skills
    # (>10 min) surface intermediate progress every 5-10 min.
    # WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
    # WIKI-FINDING: progress.py docstring promised an external monitor never built
    # WIKI-ACTION: replaced with built-in heartbeat thread at process init
    try:
        from eightd import heartbeat as _heartbeat
        _heartbeat.start(run_dir, run_id)
    except Exception as e:
        import sys
        sys.stderr.write(f"[run_8d] WARN: heartbeat failed to start: {e}\n")

    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": run_id, "recursion_limit": 100}}

        if args.resume_id:
            initial = None
        else:
            initial = {
                "problem": args.problem,
                "run_id": run_id,
                "run_dir": str(run_dir),
            }

        try:
            final_state = graph.invoke(initial, config=config)
        except Exception as _exc:
            # GraphInterrupt is raised by interrupt() in phase_10 to pause the
            # graph for human approval. It is NOT an error — the checkpoint is
            # persisted and the user resumes via --approve/--reject.
            from langgraph.errors import GraphInterrupt
            if isinstance(_exc, GraphInterrupt):
                print(
                    f"Awaiting approval for {run_id}. "
                    f"Use --approve {run_id} or --reject {run_id} '<reason>' to continue.",
                    file=sys.stderr,
                )
                # Checkpoint preserved; do NOT rmtree run_dir.
                return 0
            raise

    if final_state.get("phase_11_complete"):
        # Full pipeline complete — cleanup checkpoint and run directory.
        report_path = final_state.get("report_path")
        print(report_path)
        shutil.rmtree(run_dir, ignore_errors=True)
        return 0

    print(
        f"Run incomplete. Use --resume {run_id} to continue.",
        file=sys.stderr,
    )
    return 2


def gc_runs():
    cutoff = time.time() - RUN_RETENTION_DAYS * 86400
    if not RUNS_DIR.exists():
        return
    for rundir in RUNS_DIR.iterdir():
        if rundir.is_dir() and rundir.stat().st_mtime < cutoff:
            shutil.rmtree(rundir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
