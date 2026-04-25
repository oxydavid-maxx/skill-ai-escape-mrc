"""Phase 9 — dispatch a child SDK session via Popen running child_runner.py
in --mode plan; child invokes superpowers:writing-plans on actions.json.

Per spec 2026-04-25-sdk-auto-dispatch-design.md.

WIKI-CONSULTED: claude-agent-sdk-patterns#issue-573
WIKI-FINDING: subprocess inherits CLAUDECODE=1; child_runner.py pops it, but
              Popen env filter is defense-in-depth so env is clean before exec.
WIKI-ACTION: strip CLAUDECODE and CLAUDE_CODE_ENTRYPOINT from env dict passed
             to Popen (does not rely solely on child_runner.py's own strip).
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path


def phase_9_write_plan(state: dict) -> dict:
    run_dir = Path(state["run_dir"])
    plan_path = run_dir / "plan.md"
    actions_path = state["actions_path"]
    run_id = state["run_id"]

    # Strip CLAUDECODE from child env (Issue #573 defense-in-depth)
    child_env = {k: v for k, v in os.environ.items()
                 if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}

    cmd = [
        sys.executable, "-m", "eightd.child_runner",
        "--mode", "plan",
        "--run-id", run_id,
        "--actions-path", actions_path,
        "--plan-path", str(plan_path),
    ]
    proc = subprocess.Popen(cmd, env=child_env, stderr=subprocess.PIPE)
    proc.wait()

    if proc.returncode != 0:
        # Retry once
        proc2 = subprocess.Popen(cmd, env=child_env, stderr=subprocess.PIPE)
        proc2.wait()
        if proc2.returncode != 0:
            return {"plan_path": str(plan_path), "phase_9_complete": False,
                    "phase_9_error": f"child exit {proc2.returncode}"}

    return {"plan_path": str(plan_path), "phase_9_complete": True}
