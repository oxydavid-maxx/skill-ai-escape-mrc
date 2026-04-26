"""Phase 9 - deterministic plan generation from structured actions.

Replaces the former subprocess.Popen -> child_runner.py -> superpowers:writing-plans
dispatch that hung in autonomous mode.

Per escape #8 in ~/.claude/governance/escape_log.yaml (proof 8D run-1777179234).
User-approved fix: drop Phase 9 LLM/SDK dispatch entirely; generate plan directly
from the structured actions.json output of phase_8_collect_actions.

WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
WIKI-FINDING: Popen dispatch + new template path coexisting = latent dual-emit bug.
WIKI-ACTION: Popen dispatch deleted in this same commit as _plan_template.py lands.
            child_runner.py kept intact (phase_11_execute.py still uses --mode execute).

DETECTION: structural-grep - subprocess must not appear in this file (regression guard).
"""
from __future__ import annotations
import json
from pathlib import Path

from eightd.phases._plan_template import generate_plan


def phase_9_write_plan(state: dict) -> dict:
    """Generate plan.md deterministically from actions.json (no SDK, no Popen)."""
    run_dir = Path(state["run_dir"])
    plan_path = run_dir / "plan.md"
    actions_path = state["actions_path"]
    run_id = state["run_id"]

    actions = json.loads(Path(actions_path).read_text(encoding="utf-8"))
    plan_md = generate_plan(actions, run_id)
    plan_path.write_text(plan_md, encoding="utf-8")

    return {"plan_path": str(plan_path), "phase_9_complete": True}