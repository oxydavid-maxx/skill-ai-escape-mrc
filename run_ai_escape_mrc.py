"""CLI entry point for AI Escape MRC LangGraph pipeline."""
import argparse
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from ai_escape_mrc.graph import build_graph

RUNS_DIR = Path(__file__).parent / "runs"
RUN_RETENTION_DAYS = 30


def _isonow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(prog="run_ai_escape_mrc")
    ap.add_argument("problem", nargs="?", help="Problem description")
    ap.add_argument("--resume", dest="resume_id")
    ap.add_argument("--run-id", help=argparse.SUPPRESS)
    ap.add_argument("--status-json", metavar="RUN_ID_OR_DIR",
                    help="Print a JSON status snapshot for a run id or run directory")
    ap.add_argument("--gc", action="store_true", help="Clean runs older than 30d")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--user-email", help="Requester email; final report/plan email goes here when set")
    ap.add_argument("--operator-email", help="Operator email to CC or use as fallback")
    ap.add_argument("--approve", action="store_true",
                    help="Removed: Phase 11 approval execution is no longer supported")
    ap.add_argument("--reject", metavar="REASON",
                    help="Removed: Phase 11 approval execution is no longer supported")
    ap.add_argument("--status", action="store_true",
                    help="Removed: use --status-json for run status")
    args = ap.parse_args()

    if args.gc:
        gc_runs()
        return 0

    if args.status_json:
        from ai_escape_mrc.run_status import status_for_run
        status = status_for_run(args.status_json, default_runs_dir=RUNS_DIR)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0 if status.get("exists") else 1

    if not args.problem and not args.resume_id:
        ap.error("problem is required (or use --resume <run_id>)")

    if args.resume_id and args.run_id:
        ap.error("--run-id cannot be combined with --resume")

    run_id = args.resume_id or args.run_id or f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id

    # Legacy approval execution was removed with Phase 11. Keep a clear error
    # instead of silently resuming an old execution path.
    if args.resume_id and (args.approve or args.reject or args.status):
        print(
            "Phase 11 approval execution has been removed. "
            "AI Escape MRC now ends at Phase 10 final delivery; use --status-json <run_id> "
            "or open the delivered report/plan artifacts.",
            file=sys.stderr,
        )
        return 2

    run_dir.mkdir(parents=True, exist_ok=True)

    db_path = run_dir / "checkpoint.db"

    if args.dry_run:
        print(f"Would invoke graph with run_id={run_id}")
        return 0

    print(
        "\n".join(
            [
                f"[AI Escape MRC] Run started: {run_id}",
                f"- Problem: {args.problem}",
                f"- Run directory: {run_dir}",
                "- Stage summaries print here after each phase and persist to stage-summaries.md/jsonl.",
            ]
        ),
        file=sys.stderr,
        flush=True,
    )

    # Init progress logging (emits per-event records to run_dir/progress.jsonl).
    # This is a required visibility sink, not best-effort logging.
    try:
        from ai_escape_mrc import progress as _progress
        _progress.init(run_dir)
    except Exception as e:
        _record_runtime_error(run_dir, "runtime_init", e)
        return 1

    # Start the heartbeat daemon thread. Emits a human-readable progress summary
    # every HEARTBEAT_INTERVAL_SEC (default 300s) to stderr and optionally to the
    # Telegram diagnostics topic. Satisfies the requirement in
    # ~/.claude/feedback_skill_progress_reporting.md that long-running skills
    # (>10 min) surface intermediate progress every 5-10 min.
    # WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
    # WIKI-FINDING: progress.py docstring promised an external monitor never built
    # WIKI-ACTION: replaced with built-in heartbeat thread at process init
    try:
        from ai_escape_mrc import heartbeat as _heartbeat
        _heartbeat.start(run_dir, run_id)
    except Exception as e:
        # WIKI-CONSULTED: function-replacement-convention#The-Convention
        # WIKI-FINDING: Local import inside except block shadows module-level import,
        #   making Python treat 'sys' as local throughout main(); all later sys.stderr
        #   references fail with UnboundLocalError on code paths that skip this block.
        # WIKI-ACTION: Removed local 'import sys'; module-level import (line 4) is used.
        sys.stderr.write(f"[run_ai_escape_mrc] WARN: heartbeat failed to start: {e}\n")

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
                "user_email": args.user_email,
                "operator_email": args.operator_email,
            }

        try:
            final_state = graph.invoke(initial, config=config)
        except Exception as _exc:
            # Phase 10 no longer interrupts; treat any GraphInterrupt as a
            # stale approval-flow regression.
            from langgraph.errors import GraphInterrupt
            if isinstance(_exc, GraphInterrupt):
                print(
                    f"Unexpected approval interrupt for {run_id}; "
                    "Phase 11 approval execution has been removed.",
                    file=sys.stderr,
                )
                return 1
            _record_runtime_error(run_dir, "runtime", _exc)
            return 1

    if final_state.get("phase_10_complete"):
        _print_final_delivery(final_state)
        return 0 if _delivery_ok(final_state) else 3

    print(
        f"Run incomplete before Phase 10 final delivery. Use --status-json {run_id} to inspect.",
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


def _record_runtime_error(run_dir: Path, phase: str, exc: BaseException) -> None:
    try:
        error_path = run_dir / "run-error.json"
        if not error_path.exists():
            from ai_escape_mrc.stage_summary import write_run_error
            write_run_error(run_dir, phase, exc)
        else:
            print(f"[AI Escape MRC] Run failed; details: {error_path}", file=sys.stderr, flush=True)
    except Exception as visibility_exc:
        print(
            f"[AI Escape MRC] Run failed and error artifact could not be written: "
            f"{type(visibility_exc).__name__}: {visibility_exc}",
            file=sys.stderr,
            flush=True,
        )
    print(
        f"[AI Escape MRC] Run failed: {type(exc).__name__}: {str(exc)[:300]}",
        file=sys.stderr,
        flush=True,
    )


def _delivery_ok(state: dict) -> bool:
    return state.get("email_delivery_result") == "sent"


def _print_final_delivery(state: dict) -> None:
    lines = [
        "[AI Escape MRC] Final Delivery",
        f"- Run: {state.get('run_id') or '(missing)'}",
        f"- Email: {state.get('email_delivery_result') or '(missing)'}",
        f"- Recipient: To={state.get('recipient_to') or '(missing)'}; "
        f"Cc={state.get('recipient_cc') or '(none)'}; "
        f"source={state.get('recipient_source') or '(missing)'}",
        f"- Report: {state.get('report_path') or '(missing)'}",
        f"- Plan: {state.get('plan_path') or '(missing)'}",
        f"- Stage summaries: {state.get('stage_summaries_path') or '(missing)'}",
        f"- Delivery status: {state.get('delivery_status_path') or '(missing)'}",
    ]
    if state.get("screen_summary"):
        screen_lines = str(state["screen_summary"]).splitlines()
        lines.append("- Latest summary:")
        lines.extend(f"  {line}" for line in screen_lines[:8])
    if not _delivery_ok(state):
        lines.append(f"- Email error: {state.get('email_delivery_error') or '(missing error detail)'}")
        lines.append("- Manual fallback: open the report and plan paths above and send them to the requester manually.")
    print("\n".join(lines), file=sys.stderr, flush=True)


if __name__ == "__main__":
    sys.exit(main())
