"""Phase 11 — dispatch SDK child to execute the approved plan via
superpowers:executing-plans. Skipped if rejected.

Per spec 2026-04-25-sdk-auto-dispatch-design.md.

WIKI-CONSULTED: claude-agent-sdk-patterns#issue-573
WIKI-FINDING: subprocess inherits CLAUDECODE=1; must strip from env dict passed
              to Popen as defense-in-depth (child_runner.py also strips, dual protection).
WIKI-ACTION: strip CLAUDECODE and CLAUDE_CODE_ENTRYPOINT from Popen env.

WIKI-CONSULTED: silent-staleness#content-based-freshness
WIKI-FINDING: phase_11 must NOT trust gate file mtime or created_at; must trust
              approved:true content directly (passed via LangGraph state).
WIKI-ACTION: approval payload read from state["approval"] dict (LangGraph state),
             not re-read from gate file filesystem.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path


def phase_11_execute(state: dict) -> dict:
    approval = state.get("approval") or {}
    if not approval.get("approved"):
        return {
            "phase_11_complete": True,
            "phase_11_skipped": True,
            "phase_11_skip_reason": approval.get("rejected_reason") or "not approved",
        }

    run_id = state["run_id"]
    plan_path = state["plan_path"]
    child_env = {k: v for k, v in os.environ.items()
                 if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}

    cmd = [
        sys.executable, "-m", "eightd.child_runner",
        "--mode", "execute",
        "--run-id", run_id,
        "--plan-path", plan_path,
    ]
    proc = subprocess.Popen(cmd, env=child_env, stderr=subprocess.PIPE)
    proc.wait()

    return {
        "phase_11_complete": True,
        "phase_11_skipped": False,
        "phase_11_returncode": proc.returncode,
    }
