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


def main():
    ap = argparse.ArgumentParser(prog="run_8d")
    ap.add_argument("problem", nargs="?", help="Problem description")
    ap.add_argument("--resume", dest="resume_id")
    ap.add_argument("--gc", action="store_true", help="Clean runs older than 30d")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.gc:
        gc_runs()
        return 0

    if not args.problem and not args.resume_id:
        ap.error("problem is required (or use --resume <run_id>)")

    run_id = args.resume_id or f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    db_path = run_dir / "checkpoint.db"

    if args.dry_run:
        print(f"Would invoke graph with run_id={run_id}")
        return 0

    with SqliteSaver.from_conn_string(f"sqlite:///{db_path}") as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": run_id}}

        if args.resume_id:
            initial = None
        else:
            initial = {
                "problem": args.problem,
                "run_id": run_id,
                "run_dir": str(run_dir),
            }

        final_state = graph.invoke(initial, config=config)

    if final_state.get("phase_7_complete"):
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
