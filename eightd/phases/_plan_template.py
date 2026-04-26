from __future__ import annotations
from datetime import date
from typing import Any

_PRIORITY_ORDER = {"high": 0, "verification": 1, "medium": 2, "low": 3}
_QUADRANT_LABELS = {
    "corrective:TRC-NC": "TRC-NC Corrective",
    "corrective:TRC-ND": "TRC-ND Corrective",
    "prevention:MRC-NC": "MRC-NC Prevention",
    "prevention:MRC-ND": "MRC-ND Prevention",
    "verification": "Verification",
}
_PRIORITY_TAG = {"high": "[HIGH]", "verification": "[VERIFY]", "medium": "[MED]", "low": "[LOW]"}


def generate_plan(actions, run_id):
    today = date.today().isoformat()
    sorted_actions = sorted(actions, key=lambda a: _PRIORITY_ORDER.get(str(a.get("priority", "medium")), 2))
    sections = [_build_header(run_id, today, len(actions))]
    for i, action in enumerate(sorted_actions):
        sections.append(_build_task(i + 1, action, run_id))
    sections.append(_build_footer(run_id))
    return chr(10).join(sections)


def _build_header(run_id, today, action_count):
    return f"# 8D Implementation Plan - Run {run_id}" + chr(10) + chr(10) + f"**Generated:** {today}" + chr(10) + f"**Source run:** {run_id}" + chr(10) + f"**Total tasks:** {action_count}" + chr(10) + "**Priority ordering:** High > Verification > Medium > Low" + chr(10) + chr(10) + "---"


def _build_task(task_num, action, run_id):
    title = str(action.get("title") or "(untitled)")
    description = str(action.get("description") or title)
    files_touched = action.get("files_touched") or []
    owner = str(action.get("owner") or "kuangyu")
    priority = str(action.get("priority") or "medium")
    source_quadrant = str(action.get("source_quadrant") or "unknown")
    quadrant_label = _QUADRANT_LABELS.get(source_quadrant, source_quadrant)
    priority_tag = _PRIORITY_TAG.get(priority, f"[{priority.upper()}]")
    files_section = ""
    if files_touched:
        fl = chr(10).join(f"- {f}" for f in files_touched)
        files_section = chr(10) + "**Files:**" + chr(10) + fl + chr(10)
    commit_title = title[:60]
    n = chr(10)
    return f"## Task {task_num}: {title} {priority_tag}{n}{n}**Source:** {quadrant_label}{n}**Owner:** {owner}{n}**Priority:** {priority}{files_section}{n}{description}{n}{n}- [ ] **Step 1: Implement**{n}{n}  Implement the action described above.{n}{n}- [ ] **Step 2: Verify**{n}{n}  Run relevant tests. Document evidence inline.{n}{n}- [ ] **Step 3: Commit (atomic)**{n}{n}  fix: {commit_title}{n}  8D run {run_id}, {quadrant_label}.{n}  Verified: [describe evidence]"


def _build_footer(run_id):
    return f"---{chr(10)}{chr(10)}## Completion Checklist{chr(10)}{chr(10)}- [ ] All tasks above completed or explicitly deferred{chr(10)}- [ ] Each fix includes a detection artifact{chr(10)}- [ ] No see-file pointers in commit messages (R13){chr(10)}- [ ] Pipeline-touching commits include PIPELINE-VERIFIED marker{chr(10)}{chr(10)}**Run ID:** {run_id}{chr(10)}**Approval command:** In Claude Code session, type: approve {run_id}"