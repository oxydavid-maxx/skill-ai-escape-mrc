"""Phase 9 - direct LLM call with fixed Python prompt for plan generation.

Replaces both the original subprocess-based writing-plan dispatch that hung in
autonomous mode (escape #8, proof AI Escape MRC run-1777179234), AND
the deterministic-template intermediate (option b) that landed earlier today.

User-approved refinement 2026-04-26 (option e): use the SAME pattern as Phase 7
report render -- direct call_claude() with a fixed system prompt + actions.json
content. Keeps LLM intelligence for adaptive plan structure, matches Phase 0-7
codebase pattern, has zero hang risk because no skill is invoked (skills are
interactive; direct LLM calls are not).

WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
WIKI-FINDING: prior deterministic-template approach (option b) was an outlier
            from the codebase pattern; direct LLM call (option e) matches
            Phase 7's pattern + preserves adaptive plan generation.
WIKI-ACTION: deleted both the original Popen dispatch AND the deterministic
            template import; replaced with call_claude() pattern matching
            Phase 7. prior-template-module module also deleted in same commit
            (no caller remains).
            Phase 11 auto-execution has since been removed; Phase 9 only writes
            the plan for delivery.

WIKI-CONSULTED: wiki-to-code-traceability#triple-marker-convention
WIKI-FINDING: triple markers required on any code touching wiki-governed
            patterns (silent-staleness, FRC, dual-emit).
WIKI-ACTION: this file carries the triple markers; prior-template-module deletion
            is referenced explicitly in WIKI-ACTION above.

DETECTION: structural-grep - subprocess must not appear in this file (regression guard).
"""
from __future__ import annotations
import json
from pathlib import Path

# WIKI-CONSULTED: silent-staleness#three-layer-defense
# WIKI-FINDING: Phase 9 can silently emit a too-short/incomplete plan.md that looks
#   like success but breaks Phase 10 gate content ??layer 2 defense is output
#   validation before the FSM transitions.
# WIKI-ACTION: validate_phase9_plan() called after every call_claude() write;
#   raises Phase9OutputContractError on failure for fail-closed routing (R13).
from ai_escape_mrc.sdk_client import call_claude
from ai_escape_mrc.models import model_for_role
from ai_escape_mrc.validators import legacy_identity_instruction, validate_phase9_plan


SYSTEM_PROMPT = """You are an implementation-plan author. Convert the structured \
AI Escape MRC corrective + prevention actions you receive into a bite-sized-task implementation \
plan in Markdown.

Output requirements:
- Header: `# <topic> Implementation Plan` derived from the actions' source quadrants
- One `## Task N: <action title>` per action (use action.title verbatim)
- Per task: `**Files:**` listing action.files_touched, then 3-5 bite-sized steps \
(each 2-5 minutes of work). Use `- [ ]` checkbox syntax.
- Each step starts with `**Step N: <imperative>**` then exact commands or code.
- Final section: `## Self-Review` checklist (placeholder scan, type consistency, \
spec coverage).

Constraints:
- Bite-sized: each step is one action (2-5 min). NO multi-action steps.
- Concrete: exact file paths, exact commands, exact code (no TBD/TODO).
- DRY/YAGNI: no speculative tasks beyond what the actions specify.
- {identity_instruction}
- Do NOT invoke any tools or skills. Just emit the plan markdown directly.
""".format(identity_instruction=legacy_identity_instruction())


def phase_9_write_plan(state: dict) -> dict:
    """Generate plan.md via direct LLM call (no SDK dispatch, no skill invocation).

    Same pattern as phase_7_report._render_report -- call_claude with fixed system
    prompt + actions JSON as user content. Matches codebase convention.
    """
    run_dir = Path(state["run_dir"])
    plan_path = run_dir / "plan.md"
    actions_path = state["actions_path"]
    run_id = state["run_id"]

    actions = json.loads(Path(actions_path).read_text(encoding="utf-8"))
    user_msg = (
        f"Run ID: {run_id}\n"
        f"Source actions ({len(actions)} items):\n\n"
        f"```json\n{json.dumps(actions, ensure_ascii=False, indent=2)}\n```\n\n"
        f"Emit the implementation plan markdown now."
    )

    plan_md = call_claude(
        model=model_for_role("report_generation"),
        system=SYSTEM_PROMPT,
        user=user_msg,
        parse_json=False,
        max_tokens=16000,
        temperature=0.3,
        purpose="phase_9_write_plan",
        timeout_sec=900,
    )

    # WIKI-CONSULTED: silent-staleness#output-validation
    # WIKI-FINDING: write + validate in same step; never transition FSM on unvalidated output.
    # WIKI-ACTION: validate_phase9_plan raises Phase9OutputContractError before return.
    plan_path.write_text(plan_md, encoding="utf-8")
    validate_phase9_plan(plan_path)
    return {"plan_path": str(plan_path), "phase_9_complete": True}
