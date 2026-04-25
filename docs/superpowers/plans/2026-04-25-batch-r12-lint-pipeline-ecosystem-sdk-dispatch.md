# Batch Implementation Plan — R12 fix + lint parity + pipeline-gap triage + SDK auto-dispatch + ECOSYSTEM.md

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land 5 batched items in dependency order: (A) R12 stop-hook JSON shape fix to eliminate red validation banners; (B) claude-hooks lint matcher↔extractor parity check (closes escape #7 generative class); (C) pipeline-gap 8D report triage; (D) SDK auto-dispatch in skill-8d-mrc LangGraph FSM (closes escape #3 backend→frontend gap); (E) ECOSYSTEM.md refresh + email delivery.

**Architecture:** A and B are surgical edits to existing files. C is a read+triage with output appended to this plan. D is the largest item — 4 new LangGraph phases + 1 new module + 4 new ~/.claude artifacts per spec at `D:/D-claude/skills/skill-8d-mrc/docs/superpowers/specs/2026-04-25-sdk-auto-dispatch-design.md`. E is doc-work referencing the post-D ecosystem state.

**Tech stack:** Python 3.12 (eightd FSM, hooks, claude-hooks CLI), Bash (Stop hooks, pre/post-commit hooks), YAML/JSON (schemas, gates), LangGraph 0.6+ (interrupt() native pattern), claude_agent_sdk (Max-OAuth-whitelisted), Outlook COM via daily_brief existing pattern, Windows Task Scheduler (schtasks).

---

## Task A: R12 stop-hook JSON shape fix

**Files:**
- Modify: `C:/Users/Kuangyu/.claude/hooks/stop-hook-no-handoff-gate.sh:126-134, 200-208`
- Modify: `C:/Users/Kuangyu/.claude/hooks/stop-hook-self-healing-gate.sh:48-52, 62, 121-129`

- [ ] **Step 1: Confirm current JSON shape**

```bash
grep -n 'hookSpecificOutput' ~/.claude/hooks/stop-hook-no-handoff-gate.sh ~/.claude/hooks/stop-hook-self-healing-gate.sh
```
Expected: 3 matches with misnested `decision`/`reason` inside `hookSpecificOutput`.

- [ ] **Step 2: Reshape stop-hook-no-handoff-gate.sh first block (handoff-phrase branch)**

Replace the JSON heredoc that contains `R12 (never-handoff)` (lines ~126-134). Old shape (incorrect):
```json
{"hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": "..."}}
```
New shape (correct):
```json
{"decision": "block", "reason": "...", "hookSpecificOutput": {"hookEventName": "Stop"}}
```
Use the Edit tool — preserve the exact `R12 (never-handoff): ...` reason text verbatim, only restructure the JSON keys.

- [ ] **Step 3: Reshape stop-hook-no-handoff-gate.sh second block (verification-evidence branch)**

Same pattern at lines ~200-208 — the JSON heredoc containing `R12 (verification-evidence)`. Reshape decision/reason out of hookSpecificOutput to top level.

- [ ] **Step 4: Reshape stop-hook-self-healing-gate.sh JSON block**

Lines ~121-129. Same pattern. Reason text mentions "Self-healing checklist not completed".

- [ ] **Step 5: Redirect stop-hook-self-healing-gate.sh CHECKLIST echoes to stderr**

Lines ~48-52 — append ` >&2` to each `echo` (CHECKLIST + missing items).

- [ ] **Step 6: Redirect FINDINGS echo to stderr**

Line ~62 — append ` >&2` to the FINDINGS echo.

- [ ] **Step 7: Bash syntax check**

```bash
bash -n ~/.claude/hooks/stop-hook-no-handoff-gate.sh && \
bash -n ~/.claude/hooks/stop-hook-self-healing-gate.sh && \
echo OK
```
Expected: `OK`.

- [ ] **Step 8: Verify no remaining misnested shape**

```bash
grep -n 'hookSpecificOutput' ~/.claude/hooks/stop-hook-no-handoff-gate.sh ~/.claude/hooks/stop-hook-self-healing-gate.sh
```
Expected: 3 matches, all `{"hookEventName": "Stop"}` only — no decision/reason inside.

- [ ] **Step 9: Commit (auto-commit hook will pick this up)**

```bash
git -C ~/.claude log -1 --oneline -- hooks/stop-hook-no-handoff-gate.sh hooks/stop-hook-self-healing-gate.sh
```
Expected: commit visible.

- [ ] **Step 10: Live verification — trigger R12 with handoff + completion**

Construct an assistant message containing both "done" and "you can run". Submit. Observe UI: R12 deny reason shown WITHOUT red `Hook JSON output validation failed` banner. Tail `~/.claude/hooks/stop-hook.log` — entry should be a clean R12 block, not a parse error.

If banner still red → diff against expected JSON shape, repeat fix.

---

## Task B: claude-hooks lint matcher↔extractor parity check

**Files:**
- Modify: `C:/Users/Kuangyu/.claude/bin/claude-hooks` (extend `cmd_lint`)
- Reference: `C:/Users/Kuangyu/.claude/settings.json` (matchers source)
- Reference: `C:/Users/Kuangyu/.claude/hooks/hook-r13-output-boundary.py` (current extractor for parity check)

- [ ] **Step 1: Read current cmd_lint**

```bash
grep -n 'def cmd_lint' ~/.claude/bin/claude-hooks
```

- [ ] **Step 2: Define expected behavior**

The check: parse `settings.json`, find each PreToolUse hook entry; for each `matcher` regex, expand alternation (e.g., `"Write|Edit|Bash|mcp__.*|PowerShell"` → `["Write", "Edit", "Bash", "mcp__.*", "PowerShell"]`); for each tool name (skip regex patterns like `mcp__.*`), check if the hook script's source contains a literal `tool_name == "<name>"` or `tool_name in (...)` branch. Flag any tool name that has no extraction branch.

False positives acceptable (heuristic). False negatives are the failure mode being prevented.

- [ ] **Step 3: Add `_check_matcher_extractor_parity` helper to claude-hooks**

Insert before `def cmd_lint`. Code:
```python
def _check_matcher_extractor_parity() -> list[str]:
    """Return list of warning strings, one per matcher↔extractor mismatch."""
    import json, re
    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        return []
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"settings.json parse error: {e}"]

    warnings = []
    pretooluse = (settings.get("hooks") or {}).get("PreToolUse") or []
    for entry in pretooluse:
        matcher = entry.get("matcher", "")
        if not matcher:
            continue
        # Skip regex-pattern tool names; only check literal tool names
        tool_names = [t for t in matcher.split("|") if t and re.fullmatch(r"\w+", t)]
        for hook in (entry.get("hooks") or []):
            cmd = hook.get("command", "")
            # Heuristic: extract path after `bash ` or `py -3 `
            m = re.search(r"(?:bash|py\s*-3)\s+(\S+)", cmd)
            if not m:
                continue
            script_path = m.group(1).replace("~", str(Path.home()))
            sp = Path(script_path)
            if not sp.exists():
                continue
            try:
                src = sp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for tool in tool_names:
                # Look for `tool_name == "X"` or `tool_name in (...)` containing X
                pat = rf'tool_name\s*(?:==\s*[\'"]){re.escape(tool)}[\'"]|tool_name\s+in\s*\([^)]*[\'"]?{re.escape(tool)}[\'"]?'
                if not re.search(pat, src):
                    warnings.append(
                        f"matcher↔extractor parity: {sp.name} matches {tool!r} "
                        f"in settings.json but has no `tool_name == {tool!r}` branch"
                    )
    return warnings
```

- [ ] **Step 4: Wire into cmd_lint**

In `cmd_lint`, after the existing rule-validation block, add:
```python
parity_warnings = _check_matcher_extractor_parity()
if parity_warnings:
    print("\n[matcher↔extractor parity check]")
    for w in parity_warnings:
        print(f"  WARN: {w}")
    print(f"  ({len(parity_warnings)} warning(s) — heuristic check, may include false positives)")
else:
    print("\n[matcher↔extractor parity check] OK")
```

- [ ] **Step 5: Run lint**

```bash
py -3 ~/.claude/bin/claude-hooks lint
```
Expected: `[validate-rules] OK` followed by parity-check output. If any drift exists, it'll be flagged. Confirm at minimum that hook-r13-output-boundary.py shows clean (PowerShell branch was added today).

- [ ] **Step 6: Commit (auto-picks via PostToolUse hook on Edit)**

```bash
git -C ~/.claude log -1 --oneline -- bin/claude-hooks
```
Expected: recent commit visible.

---

## Task C: Pipeline-gap 8D report triage

**Files:**
- Read: `D:/D-claude/skills/skill-8d-mrc/docs/8d-reports/8d-2026-04-25-gate-pipeline-enforcement-gap-the-policy-engine-has-multiple.md`
- Append: this plan file (same plan you're reading) — add a "Pipeline-gap 8D triage" section at the bottom

- [ ] **Step 1: Read report Section A (root cause)**

Use Read tool with file_path + offset/limit appropriate for Section A only.

- [ ] **Step 2: Read Section B (Corrective Actions 4Q matrix)**

- [ ] **Step 3: Read Section B2 (Prevention Actions 4Q matrix)**

- [ ] **Step 4: Read Section C (Verification plan)**

- [ ] **Step 5: For each action item, classify**

Three classifications:
- `already-fixed` — done in this session (e.g., R2 predicate sharpening, R8 inline-code digest, PowerShell matcher extension, R13 hook UTF-8 fix, R13 PowerShell extraction)
- `not-applicable` — superseded by other work or out-of-scope
- `new-work` — needs implementation

- [ ] **Step 6: Append triage section to this plan**

Use Edit tool. Append at end of plan file (this file):
```markdown
---

## Task C output: Pipeline-gap 8D triage

| Action item | Classification | Disposition |
|---|---|---|
| <action 1> | already-fixed | <session reference> |
| <action 2> | new-work | <added as Task X.Y below OR filed for next session as <path>> |
| ... | ... | ... |
```

- [ ] **Step 7: For new-work items, decide**

Two options per new-work item:
- **Append as Task** (numbered Task 6.1, 6.2, ... below Task 5) if the item fits in this batch
- **File for next session** by writing a one-line note to `~/.claude/.next-session-primer.md` (create the file if missing)

- [ ] **Step 8: Commit triage updates**

If this plan file was modified, the auto-commit hook on D:/D-claude doesn't fire (workspace not auto-committed). Manual:
```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add docs/superpowers/plans/2026-04-25-batch-r12-lint-pipeline-ecosystem-sdk-dispatch.md && \
git commit -m "plan: append pipeline-gap 8D triage section"
```

---

## Task D: SDK auto-dispatch implementation

Per spec at `D:/D-claude/skills/skill-8d-mrc/docs/superpowers/specs/2026-04-25-sdk-auto-dispatch-design.md`.

### Task D.1: `eightd/child_runner.py` — process entry point with CLAUDECODE strip

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/child_runner.py`
- Test: `D:/D-claude/skills/skill-8d-mrc/tests/test_child_runner.py`

- [ ] **Step 1: Write failing test for env-cleanup**

```python
# tests/test_child_runner.py
import os
import subprocess
import sys
from pathlib import Path

def test_child_runner_strips_claudecode(tmp_path):
    env = {**os.environ, "CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli"}
    out_file = tmp_path / "env_dump.txt"
    proc = subprocess.run(
        [sys.executable, "-c",
         "import eightd.child_runner; import os, sys; "
         f"open(r'{out_file}', 'w').write(str({{k: os.environ.get(k) for k in ['CLAUDECODE','CLAUDE_CODE_ENTRYPOINT']}}))"
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert proc.returncode == 0, proc.stderr
    dump = out_file.read_text()
    assert "'CLAUDECODE': None" in dump, f"CLAUDECODE not popped: {dump}"
    assert "'CLAUDE_CODE_ENTRYPOINT': None" in dump, f"CCE not popped: {dump}"
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_child_runner.py -v
```
Expected: FAIL `ModuleNotFoundError: No module named 'eightd.child_runner'`.

- [ ] **Step 3: Write child_runner.py skeleton**

```python
"""Child SDK process entry point for skill-8d-mrc auto-dispatch (Phase 9 + 11).

Pops CLAUDECODE and CLAUDE_CODE_ENTRYPOINT before importing claude_agent_sdk
to dodge nested-session detection (Issue #573, wiki claude-agent-sdk-patterns).
"""
from __future__ import annotations
import argparse
import os
import sys

# WIKI-CONSULTED: claude-agent-sdk-patterns#issue-573
# WIKI-FINDING: subprocess inherits CLAUDECODE=1; spawned CLI rejects nested session.
# WIKI-ACTION: pop env vars BEFORE importing claude_agent_sdk so its session-init
#              probe doesn't see them.
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)


def main() -> int:
    ap = argparse.ArgumentParser(prog="eightd.child_runner")
    ap.add_argument("--mode", choices=["plan", "execute"], required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--actions-path", help="Path to actions.json (mode=plan)")
    ap.add_argument("--plan-path", required=True, help="Path to plan.md (input for execute, output for plan)")
    args = ap.parse_args()

    # Defer SDK import until after env strip (paranoid)
    from claude_agent_sdk import query, ClaudeAgentOptions

    if args.mode == "plan":
        return _run_plan(args)
    return _run_execute(args)


def _run_plan(args) -> int:
    from claude_agent_sdk import query, ClaudeAgentOptions
    import asyncio
    prompt = (
        f"Invoke superpowers:writing-plans on the actions in {args.actions_path}. "
        f"Output the plan to {args.plan_path}. Run ID: {args.run_id}."
    )
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Write", "WebSearch"],
    )
    return asyncio.run(_collect(query(prompt=prompt, options=options)))


def _run_execute(args) -> int:
    from claude_agent_sdk import query, ClaudeAgentOptions
    import asyncio
    exempt = (
        f"EXEMPT R1 R2 R3 R4 R5 R9 child-of-8d: SDK-dispatched child session "
        f"executing approved plan from 8D run {args.run_id}. Parent ran the "
        f"full pipeline; child only implements the approved plan."
    )
    prompt = (
        f"{exempt}\n\nInvoke superpowers:executing-plans on the plan at "
        f"{args.plan_path}. Run ID: {args.run_id}."
    )
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "Bash", "WebSearch"],
    )
    return asyncio.run(_collect(query(prompt=prompt, options=options)))


async def _collect(msg_iter) -> int:
    async for msg in msg_iter:
        # Forward to stderr for parent heartbeat capture
        print(repr(msg)[:500], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Re-run test — expect PASS**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_child_runner.py -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add eightd/child_runner.py tests/test_child_runner.py && \
git commit -m "feat(eightd): child_runner.py with CLAUDECODE strip (Issue #573 mitigation)"
```

### Task D.2: `eightd/phases/phase_8_collect_actions.py`

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_8_collect_actions.py`
- Test: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_8.py`

- [ ] **Step 1: Write fixture + failing test**

```python
# tests/test_phase_8.py
import json
from pathlib import Path
from eightd.phases.phase_8_collect_actions import phase_8_collect_actions

def test_extracts_4_quadrants_from_full_state(tmp_path):
    state = {
        "run_id": "test-run-1",
        "run_dir": str(tmp_path),
        "phase_4_actions": {
            "TRC-NC": [{"title": "Fix X", "description": "...", "files": ["a.py"]}],
            "TRC-ND": [{"title": "Detect Y", "description": "...", "files": ["b.py"]}],
            "MRC-NC": [{"title": "Prevent Z", "description": "...", "files": ["c.py"]}],
            "MRC-ND": [{"title": "Audit W", "description": "...", "files": ["d.py"]}],
        },
        "phase_6_verification_plan": [{"title": "Verify all", "description": "..."}],
    }
    result = phase_8_collect_actions(state)
    actions_path = Path(result["actions_path"])
    assert actions_path.exists()
    data = json.loads(actions_path.read_text(encoding="utf-8"))
    assert len(data) == 5  # 4 corrective + 1 verification
    sources = {a["source_quadrant"] for a in data}
    assert sources == {"TRC-NC", "TRC-ND", "MRC-NC", "MRC-ND", "verification"}

def test_returns_empty_on_no_actions(tmp_path):
    state = {"run_id": "empty", "run_dir": str(tmp_path), "phase_4_actions": {}}
    result = phase_8_collect_actions(state)
    data = json.loads(Path(result["actions_path"]).read_text(encoding="utf-8"))
    assert data == []
```

- [ ] **Step 2: Run test — expect FAIL (module missing)**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_phase_8.py -v
```

- [ ] **Step 3: Implement phase_8_collect_actions.py**

```python
"""Phase 8 — collect Phase 4 corrective/prevention actions + Phase 6 verification
into a normalized JSON list for downstream writing-plans dispatch.

Pure-Python; no SDK call.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def phase_8_collect_actions(state: dict) -> dict:
    run_dir = Path(state["run_dir"])
    actions_path = run_dir / "actions.json"
    out: list[dict[str, Any]] = []

    p4 = state.get("phase_4_actions") or {}
    for quadrant in ("TRC-NC", "TRC-ND", "MRC-NC", "MRC-ND"):
        for item in (p4.get(quadrant) or []):
            out.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "files_touched": item.get("files") or item.get("files_touched") or [],
                "owner": item.get("owner", "kuangyu"),
                "priority": item.get("priority", "medium"),
                "source_quadrant": quadrant,
            })

    for item in (state.get("phase_6_verification_plan") or []):
        out.append({
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "files_touched": item.get("files") or [],
            "owner": item.get("owner", "kuangyu"),
            "priority": "verification",
            "source_quadrant": "verification",
        })

    actions_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"actions_path": str(actions_path), "actions_count": len(out), "phase_8_complete": True}
```

- [ ] **Step 4: Re-run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_8_collect_actions.py tests/test_phase_8.py && \
git commit -m "feat(eightd): phase_8_collect_actions extracts Phase 4+6 to actions.json"
```

### Task D.3: `eightd/phases/phase_9_write_plan.py` — SDK dispatch for writing-plans

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_9_write_plan.py`
- Test: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_9.py`

- [ ] **Step 1: Write test for Popen invocation shape (skip actual SDK call)**

```python
# tests/test_phase_9.py
from unittest.mock import patch, MagicMock
from pathlib import Path
from eightd.phases.phase_9_write_plan import phase_9_write_plan

def test_phase_9_pops_claudecode_from_popen_env(tmp_path):
    state = {
        "run_id": "test-9",
        "run_dir": str(tmp_path),
        "actions_path": str(tmp_path / "actions.json"),
    }
    (tmp_path / "actions.json").write_text("[]", encoding="utf-8")
    captured_env = {}

    def fake_popen(cmd, env=None, **kw):
        captured_env.update(env or {})
        m = MagicMock()
        m.wait.return_value = 0
        m.returncode = 0
        # Simulate child writing plan.md
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("# stub plan", encoding="utf-8")
        return m

    with patch("subprocess.Popen", side_effect=fake_popen), \
         patch.dict("os.environ", {"CLAUDECODE": "1", "OTHER": "ok"}, clear=False):
        result = phase_9_write_plan(state)

    assert "CLAUDECODE" not in captured_env, "CLAUDECODE leaked into child env"
    assert captured_env.get("OTHER") == "ok", "non-CC env vars must pass through"
    assert Path(result["plan_path"]).exists()
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement phase_9_write_plan.py**

```python
"""Phase 9 — dispatch a child SDK session via Popen running child_runner.py
in --mode plan; child invokes superpowers:writing-plans on actions.json.

Per spec 2026-04-25-sdk-auto-dispatch-design.md.
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
```

- [ ] **Step 4: Re-run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_9_write_plan.py tests/test_phase_9.py && \
git commit -m "feat(eightd): phase_9_write_plan dispatches SDK child for writing-plans"
```

### Task D.4: Gate file directory + writer in `phase_10_emit_and_wait.py`

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_10_emit_and_wait.py`
- Test: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_10.py`
- Create runtime: `~/.claude/.pending-8d-approvals/` (created by phase_10 first run)

- [ ] **Step 1: Write test for gate file write + interrupt() call**

```python
# tests/test_phase_10.py
import json
from pathlib import Path
from unittest.mock import patch
import pytest

def test_phase_10_writes_gate_file_with_inline_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan_path = tmp_path / "plan.md"
    plan_path.write_text("# Plan\n\n- step 1\n- step 2\n", encoding="utf-8")

    from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait

    state = {
        "run_id": "test-10",
        "run_dir": str(tmp_path),
        "report_path": str(tmp_path / "report.md"),
        "plan_path": str(plan_path),
        "actions_count": 5,
    }
    (tmp_path / "report.md").write_text("# report stub", encoding="utf-8")

    # Patch interrupt() to a no-op that returns approval payload
    with patch("langgraph.types.interrupt", return_value={"approved": True, "via": "test"}):
        result = phase_10_emit_and_wait(state)

    gate_dir = tmp_path / ".claude" / ".pending-8d-approvals"
    gate_files = list(gate_dir.glob("test-10.json"))
    assert len(gate_files) == 1
    gate = json.loads(gate_files[0].read_text(encoding="utf-8"))
    assert gate["plan_inline"].startswith("# Plan")
    assert gate["actions_count"] == 5
    assert gate["approved"] is False  # initial state
    assert result["approval"] == {"approved": True, "via": "test"}
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement phase_10_emit_and_wait.py**

```python
"""Phase 10 — emit single consolidated email + gate file, then interrupt()
for human approval via either Portal A (email reply) or Portal B (Claude session).

Per spec 2026-04-25-sdk-auto-dispatch-design.md.

WIKI-CONSULTED: silent-staleness#misleading-metadata-trap
WIKI-FINDING: created_at must NOT be used as freshness signal.
WIKI-ACTION: created_at recorded for audit only; phase_11 trusts approved:true content.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from langgraph.types import interrupt


def phase_10_emit_and_wait(state: dict) -> dict:
    run_id = state["run_id"]
    plan_path = Path(state["plan_path"])
    report_path = state.get("report_path", "")
    plan_inline = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""

    gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"
    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gate_dir / f"{run_id}.json"

    gate_doc = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_path": str(report_path),
        "plan_path": str(plan_path),
        "plan_inline": plan_inline,
        "actions_count": state.get("actions_count", 0),
        "approved": False,
        "approved_at": None,
        "via": None,
        "rejected": False,
        "rejected_reason": None,
    }
    gate_path.write_text(json.dumps(gate_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    # Send consolidated email (best-effort; gate file is the source of truth)
    try:
        from eightd.delivery.email import send_consolidated_email
        send_consolidated_email(
            report_path=str(report_path),
            plan_path=str(plan_path),
            run_id=run_id,
            mailto_url=f"mailto:?subject=APPROVE%20{run_id}",
        )
    except Exception:
        pass  # Portal B remains as fallback

    approval = interrupt({
        "approval_pending": True,
        "gate_path": str(gate_path),
        "plan_path": str(plan_path),
        "run_id": run_id,
    })
    return {"approval": approval, "phase_10_complete": True}
```

- [ ] **Step 4: Re-run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_10_emit_and_wait.py tests/test_phase_10.py && \
git commit -m "feat(eightd): phase_10_emit_and_wait writes gate file + interrupts for approval"
```

### Task D.5: `eightd/phases/phase_11_execute.py`

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_11_execute.py`
- Test: `D:/D-claude/skills/skill-8d-mrc/tests/test_phase_11.py`

- [ ] **Step 1: Write test (mirrors phase_9 Popen-env test, --mode execute)**

```python
# tests/test_phase_11.py
from unittest.mock import patch, MagicMock
from pathlib import Path
from eightd.phases.phase_11_execute import phase_11_execute

def test_phase_11_skips_when_not_approved(tmp_path):
    state = {"run_id": "x", "run_dir": str(tmp_path),
             "plan_path": str(tmp_path / "plan.md"),
             "approval": {"approved": False, "rejected": True, "rejected_reason": "no"}}
    result = phase_11_execute(state)
    assert result["phase_11_complete"] is True
    assert result.get("phase_11_skipped") is True

def test_phase_11_dispatches_when_approved(tmp_path):
    (tmp_path / "plan.md").write_text("# plan", encoding="utf-8")
    state = {"run_id": "x", "run_dir": str(tmp_path),
             "plan_path": str(tmp_path / "plan.md"),
             "approval": {"approved": True, "via": "cli"}}
    captured_env = {}
    def fake_popen(cmd, env=None, **kw):
        captured_env.update(env or {})
        m = MagicMock(); m.wait.return_value = 0; m.returncode = 0
        return m
    with patch("subprocess.Popen", side_effect=fake_popen), \
         patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=False):
        result = phase_11_execute(state)
    assert "CLAUDECODE" not in captured_env
    assert result["phase_11_complete"] is True
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement phase_11_execute.py**

```python
"""Phase 11 — dispatch SDK child to execute the approved plan via
superpowers:executing-plans. Skipped if rejected.

Per spec 2026-04-25-sdk-auto-dispatch-design.md.
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
```

- [ ] **Step 4: Re-run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add eightd/phases/phase_11_execute.py tests/test_phase_11.py && \
git commit -m "feat(eightd): phase_11_execute dispatches SDK child for executing-plans"
```

### Task D.6: Wire 4 phases into `eightd/graph.py` + remove phase_7 email-send

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/graph.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_report.py` (remove email-send)
- Test: existing `tests/test_graph.py` (extend)

- [ ] **Step 1: Read phase_7_report.py to find email-send call**

```bash
grep -n "send_report_email\|email\|deliver" D:/D-claude/skills/skill-8d-mrc/eightd/phases/phase_7_report.py
```

- [ ] **Step 2: Remove the email-send call from phase_7_report.py**

Per function-replacement-convention: delete in same commit; don't leave dual emission.
Use Edit. The exact line depends on Step 1's output — replace the `send_report_email(...)` call (or the equivalent) with a comment:
```python
# Email-send migrated to phase_10_emit_and_wait per spec
# 2026-04-25-sdk-auto-dispatch-design.md (single consolidated email
# with report + plan + approval portal).
```

- [ ] **Step 3: Add 4 nodes + edges to graph.py**

Edit graph.py. Add imports:
```python
from eightd.phases.phase_8_collect_actions import phase_8_collect_actions
from eightd.phases.phase_9_write_plan import phase_9_write_plan
from eightd.phases.phase_10_emit_and_wait import phase_10_emit_and_wait
from eightd.phases.phase_11_execute import phase_11_execute
```

Add nodes (in `build_graph`):
```python
g.add_node("phase_8_collect_actions", _wrap_with_progress("phase_8_collect_actions", phase_8_collect_actions))
g.add_node("phase_9_write_plan", _wrap_with_progress("phase_9_write_plan", phase_9_write_plan))
g.add_node("phase_10_emit_and_wait", _wrap_with_progress("phase_10_emit_and_wait", phase_10_emit_and_wait))
g.add_node("phase_11_execute", _wrap_with_progress("phase_11_execute", phase_11_execute))
```

Replace the existing edge `g.add_edge("phase_7_report", END)` with the chain:
```python
g.add_edge("phase_7_report", "phase_8_collect_actions")
g.add_edge("phase_8_collect_actions", "phase_9_write_plan")
g.add_edge("phase_9_write_plan", "phase_10_emit_and_wait")
g.add_edge("phase_10_emit_and_wait", "phase_11_execute")
g.add_edge("phase_11_execute", END)
```

- [ ] **Step 4: Verify graph compiles**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -c "from eightd.graph import build_graph; from langgraph.checkpoint.sqlite import SqliteSaver; import tempfile; \
with SqliteSaver.from_conn_string(':memory:') as cp: build_graph(checkpointer=cp); print('OK')"
```
Expected: `OK`.

- [ ] **Step 5: Run all existing tests to confirm no regression**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest -x
```

- [ ] **Step 6: Commit**

```bash
git add eightd/graph.py eightd/phases/phase_7_report.py && \
git commit -m "feat(eightd): wire phase_8-11 into graph; remove phase_7 email-send (FRC)"
```

### Task D.7: `eightd/delivery/email.py` — `send_consolidated_email`

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/eightd/delivery/email.py`

- [ ] **Step 1: Read current email.py**

```bash
cat D:/D-claude/skills/skill-8d-mrc/eightd/delivery/email.py | head -80
```

- [ ] **Step 2: Add `send_consolidated_email` function**

```python
def send_consolidated_email(
    report_path: str,
    plan_path: str,
    run_id: str,
    mailto_url: str,
) -> bool:
    """Send a single email containing report summary + plan + approval portal.
    Returns True on success, False otherwise. Errors are logged but not raised.
    """
    from pathlib import Path
    try:
        report = Path(report_path).read_text(encoding="utf-8") if Path(report_path).exists() else ""
        plan = Path(plan_path).read_text(encoding="utf-8") if Path(plan_path).exists() else ""
    except Exception as e:
        print(f"[send_consolidated_email] read error: {e}")
        return False

    plan_first_50 = "\n".join(plan.splitlines()[:50])
    body_md = f"""# 8D Run {run_id} — Approval Pending

## Report
{report_path}

{report[:2000]}
{'...' if len(report) > 2000 else ''}

## Plan (auto-generated via superpowers:writing-plans)
{plan_path}

```
{plan_first_50}
{'...' if len(plan.splitlines()) > 50 else ''}
```

## To approve
Reply to this email with subject: `APPROVE {run_id}`

Or in your next Claude Code session, type: `approve {run_id}`

## To reject
Reply with subject: `REJECT {run_id}`

Or type in session: `reject {run_id}`
"""
    # Reuse existing send_markdown_email (or whatever the module exposes)
    try:
        from eightd.delivery.email import send_markdown_email
        return send_markdown_email(
            subject=f"[8D APPROVAL PENDING] Run {run_id}",
            body_md=body_md,
        )
    except ImportError:
        # Fallback to raw COM if send_markdown_email not present
        print(f"[send_consolidated_email] WARN: send_markdown_email not available; gate file is the source of truth")
        return False
```

- [ ] **Step 3: Smoke test**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -c "
from eightd.delivery.email import send_consolidated_email
import tempfile
with tempfile.TemporaryDirectory() as d:
    from pathlib import Path
    rp = Path(d) / 'r.md'; rp.write_text('# Report stub')
    pp = Path(d) / 'p.md'; pp.write_text('# Plan stub')
    print(send_consolidated_email(str(rp), str(pp), 'test-id', 'mailto:?subject=APPROVE%20test-id'))
"
```
Expected: True (or False with logged warn — acceptable since this is best-effort).

- [ ] **Step 4: Commit**

```bash
git add eightd/delivery/email.py && \
git commit -m "feat(eightd): send_consolidated_email for phase_10 approval portal"
```

### Task D.8: `run_8d.py` — `--approve` / `--reject` / `--status` flags

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/run_8d.py`

- [ ] **Step 1: Add CLI flags**

Edit `run_8d.py`. After the existing `ap.add_argument` calls, add:
```python
ap.add_argument("--approve", action="store_true",
                help="Resume an interrupted run with approval payload")
ap.add_argument("--reject", metavar="REASON",
                help="Resume an interrupted run with rejection payload")
ap.add_argument("--status", action="store_true",
                help="Show pending-approval state without resuming")
```

- [ ] **Step 2: Add resume-with-Command logic**

After the existing args parsing, before the `with SqliteSaver` block, add:
```python
if args.resume_id and (args.approve or args.reject or args.status):
    from langgraph.types import Command
    import json as _json
    from pathlib import Path as _Path
    gate = _Path.home() / ".claude" / ".pending-8d-approvals" / f"{args.resume_id}.json"

    if args.status:
        if not gate.exists():
            print(f"No pending approval for {args.resume_id}")
            return 0
        print(gate.read_text(encoding="utf-8"))
        return 0

    # Validate gate file
    if args.approve:
        if not gate.exists():
            print(f"ERROR: gate file missing: {gate}", file=sys.stderr)
            return 1
        doc = _json.loads(gate.read_text(encoding="utf-8"))
        # Defensive: also flip gate to {approved: true, via: cli} for portal symmetry
        doc.update({"approved": True, "approved_at": _isonow(), "via": "cli"})
        gate.write_text(_json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        resume_payload = {"approved": True, "via": "cli"}
    else:  # --reject
        resume_payload = {"approved": False, "rejected": True,
                          "rejected_reason": args.reject, "via": "cli"}

    db_path = (RUNS_DIR / args.resume_id) / "checkpoint.db"
    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": args.resume_id, "recursion_limit": 100}}
        final_state = graph.invoke(Command(resume=resume_payload), config=config)
    if final_state.get("phase_11_complete"):
        # Cleanup
        if gate.exists():
            gate.unlink()
        return 0
    return 2
```

Add helper at top:
```python
def _isonow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 3: Smoke test --status**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 run_8d.py --resume nonexistent --status
```
Expected: `No pending approval for nonexistent`.

- [ ] **Step 4: Commit**

```bash
git add run_8d.py && \
git commit -m "feat(run_8d): --approve/--reject/--status flags for SDK auto-dispatch resume"
```

### Task D.9: SessionStart hook — banner + auto-resume

**Files:**
- Create: `C:/Users/Kuangyu/.claude/hooks/sessionstart-8d-approval-banner.sh`
- Modify: `C:/Users/Kuangyu/.claude/settings.json` (register the hook)

- [ ] **Step 1: Write the hook script**

```bash
#!/bin/bash
# sessionstart-8d-approval-banner.sh
# (a) Inject banner for any pending {approved: false} entries
# (b) Background-resume for any {approved: true} entries
# Per spec 2026-04-25-sdk-auto-dispatch-design.md.

GATE_DIR="$HOME/.claude/.pending-8d-approvals"
[ -d "$GATE_DIR" ] || exit 0

# Auto-resume approved entries
for f in "$GATE_DIR"/*.json; do
    [ -f "$f" ] || continue
    approved=$(py -3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('approved'))" "$f" 2>/dev/null)
    if [ "$approved" = "True" ]; then
        run_id=$(basename "$f" .json)
        # Background-shell the resume; on success the gate file gets cleaned up by run_8d.py
        nohup py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py --resume "$run_id" --approve \
            >> "$HOME/.claude/hooks/8d-auto-resume.log" 2>&1 &
    fi
done

# Inject banner for pending entries
PENDING=()
for f in "$GATE_DIR"/*.json; do
    [ -f "$f" ] || continue
    approved=$(py -3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('approved'))" "$f" 2>/dev/null)
    if [ "$approved" = "False" ]; then
        PENDING+=("$f")
    fi
done

[ ${#PENDING[@]} -eq 0 ] && exit 0

# Build banner via Python (handles JSON cleanly)
py -3 - <<'PYEOF'
import json, sys
from pathlib import Path
gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"
banners = []
for f in sorted(gate_dir.glob("*.json")):
    try: doc = json.loads(f.read_text(encoding="utf-8"))
    except Exception: continue
    if doc.get("approved"): continue
    plan_first = "\n".join((doc.get("plan_inline","") or "").splitlines()[:50])
    banners.append(f"""[8D APPROVAL PENDING — run {doc['run_id']}]

Report: {doc.get('report_path','')}
Plan:   {doc.get('plan_path','')}

—— Plan summary (first 50 lines) ——
{plan_first}

—— To approve —— Reply: approve {doc['run_id']}
—— To reject  —— Reply: reject {doc['run_id']}
—— Or via email — Click APPROVE button in the 8D run email already in your inbox.
""")
if banners:
    out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n\n---\n\n".join(banners)}}
    print(json.dumps(out))
PYEOF
```

- [ ] **Step 2: chmod + smoke**

```bash
chmod +x ~/.claude/hooks/sessionstart-8d-approval-banner.sh
mkdir -p ~/.claude/.pending-8d-approvals
echo '{"run_id":"test-banner","approved":false,"report_path":"/x","plan_path":"/y","plan_inline":"# Test plan"}' > ~/.claude/.pending-8d-approvals/test-banner.json
bash ~/.claude/hooks/sessionstart-8d-approval-banner.sh
echo "---"
rm ~/.claude/.pending-8d-approvals/test-banner.json
```
Expected: JSON output with `additionalContext` containing the banner.

- [ ] **Step 3: Register in settings.json under SessionStart**

Use PowerShell to insert the registration block:
```powershell
$path = "$HOME\.claude\settings.json"
$content = [IO.File]::ReadAllText($path)
$json = $content | ConvertFrom-Json
$ss = $json.hooks.SessionStart
if (-not $ss) { $json.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @() -Force }
$exists = $json.hooks.SessionStart | Where-Object { $_.hooks | Where-Object { $_.command -like "*sessionstart-8d-approval-banner*" } }
if (-not $exists) {
  $entry = [pscustomobject]@{ matcher = ""; hooks = @([pscustomobject]@{ type = "command"; command = "bash ~/.claude/hooks/sessionstart-8d-approval-banner.sh" }) }
  $json.hooks.SessionStart += $entry
  $json | ConvertTo-Json -Depth 10 | Set-Content $path -Encoding utf8
  Write-Host "registered"
} else { Write-Host "already registered" }
```

- [ ] **Step 4: Commit (auto via PostToolUse)**

```bash
git -C ~/.claude log -1 --oneline -- hooks/sessionstart-8d-approval-banner.sh settings.json
```

### Task D.10: UserPromptSubmit approval-detect hook

**Files:**
- Create: `C:/Users/Kuangyu/.claude/hooks/userpromptsubmit-8d-approval-detect.sh`
- Modify: `C:/Users/Kuangyu/.claude/settings.json` (register)

- [ ] **Step 1: Write hook**

```bash
#!/bin/bash
# userpromptsubmit-8d-approval-detect.sh
# Detect "approve <run_id>" or "reject <run_id>" in user prompt
# → flip gate JSON to {approved: true|false, via: "session"}.

set -u

# Read stdin JSON
RAW=$(cat)
PROMPT=$(echo "$RAW" | py -3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('prompt','') or d.get('user_message','') or '')")

# Match approve/reject + run_id pattern (case-insensitive)
ACTION=""; RUN_ID=""
if [[ "$PROMPT" =~ [Aa]pprove[[:space:]]+(run-[0-9]+-[a-f0-9]+) ]]; then
    ACTION="approve"; RUN_ID="${BASH_REMATCH[1]}"
elif [[ "$PROMPT" =~ [Rr]eject[[:space:]]+(run-[0-9]+-[a-f0-9]+) ]]; then
    ACTION="reject"; RUN_ID="${BASH_REMATCH[1]}"
else
    exit 0
fi

GATE="$HOME/.claude/.pending-8d-approvals/${RUN_ID}.json"
[ -f "$GATE" ] || exit 0

py -3 - "$GATE" "$ACTION" <<'PYEOF'
import json, sys
from datetime import datetime, timezone
gate, action = sys.argv[1], sys.argv[2]
doc = json.load(open(gate, encoding="utf-8"))
now = datetime.now(timezone.utc).isoformat()
if action == "approve":
    doc.update({"approved": True, "approved_at": now, "via": "session"})
else:
    doc.update({"approved": False, "rejected": True, "rejected_reason": "session-rejected", "via": "session"})
open(gate, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=2))
print(f"[approval-detect] {action} -> {gate}", file=sys.stderr)
PYEOF
```

- [ ] **Step 2: chmod + smoke**

```bash
chmod +x ~/.claude/hooks/userpromptsubmit-8d-approval-detect.sh
mkdir -p ~/.claude/.pending-8d-approvals
echo '{"run_id":"run-1234567890-aaaaaaaa","approved":false}' > ~/.claude/.pending-8d-approvals/run-1234567890-aaaaaaaa.json
echo '{"prompt":"approve run-1234567890-aaaaaaaa"}' | bash ~/.claude/hooks/userpromptsubmit-8d-approval-detect.sh
cat ~/.claude/.pending-8d-approvals/run-1234567890-aaaaaaaa.json
rm ~/.claude/.pending-8d-approvals/run-1234567890-aaaaaaaa.json
```
Expected: `approved: true`, `via: "session"`.

- [ ] **Step 3: Register in settings.json under UserPromptSubmit**

PowerShell similar to Task D.9 Step 3, targeting `UserPromptSubmit`.

- [ ] **Step 4: Commit (auto)**

### Task D.11: Outlook approval poller

**Files:**
- Create: `C:/Users/Kuangyu/.claude/bin/outlook-approval-poller.py`
- Reference: `D:/D-claude/daily_brief/sources/outlook_mail.py` (existing Outlook COM pattern)

- [ ] **Step 1: Write poller**

```python
"""outlook-approval-poller.py
Poll Outlook inbox for `APPROVE <run_id>` or `REJECT <run_id>` reply subjects;
flip the matching ~/.claude/.pending-8d-approvals/<run_id>.json to
{approved: true|false, via: "email"}.

Per ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) Q4 / SDK auto-dispatch
spec 2026-04-25-sdk-auto-dispatch-design.md.

Run via Windows Task Scheduler `ClaudeApprovalPoller` every 10 min.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

GATE_DIR = Path.home() / ".claude" / ".pending-8d-approvals"
SUBJECT_RE = re.compile(r"^(APPROVE|REJECT)\s+(run-\d+-[a-f0-9]+)\s*$", re.IGNORECASE)


def main() -> int:
    if not GATE_DIR.exists():
        return 0
    pending = {p.stem: p for p in GATE_DIR.glob("*.json")}
    if not pending:
        return 0
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("win32com not available; poller disabled", file=sys.stderr)
        return 0

    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # olFolderInbox
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)
    flipped = 0
    for i, item in enumerate(items):
        if i > 200:
            break
        try:
            subject = item.Subject or ""
        except Exception:
            continue
        m = SUBJECT_RE.match(subject.strip())
        if not m:
            continue
        action, run_id = m.group(1).upper(), m.group(2)
        if run_id not in pending:
            continue
        gate = pending[run_id]
        doc = json.loads(gate.read_text(encoding="utf-8"))
        if doc.get("approved") or doc.get("rejected"):
            continue  # already flipped
        now = datetime.now(timezone.utc).isoformat()
        if action == "APPROVE":
            doc.update({"approved": True, "approved_at": now, "via": "email"})
        else:
            doc.update({"approved": False, "rejected": True,
                        "rejected_reason": f"email-reply: {subject}", "via": "email"})
        gate.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        flipped += 1
        print(f"[poller] {action} -> {gate.name}", file=sys.stderr)
    print(f"[poller] {flipped} flipped, {len(pending)} pending", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke test**

```bash
py -3 ~/.claude/bin/outlook-approval-poller.py
```
Expected: `[poller] 0 flipped, 0 pending` (no false positives).

- [ ] **Step 3: Commit (auto via PostToolUse)**

### Task D.12: ClaudeApprovalPoller schtasks entry

**Files:** Windows Task Scheduler (no repo file)

- [ ] **Step 1: Register schtasks**

```powershell
$bash = "C:\Users\Kuangyu\AppData\Local\Programs\Git\bin\bash.exe"
schtasks /Delete /TN "ClaudeApprovalPoller" /F 2>$null | Out-Null
$tr = "py -3 `"$HOME/.claude/bin/outlook-approval-poller.py`""
schtasks /Create /TN "ClaudeApprovalPoller" /SC MINUTE /MO 10 /ST 09:03 /TR $tr /F
schtasks /Query /TN "ClaudeApprovalPoller" /FO LIST | Select-String "TaskName|Next Run|Status"
```

- [ ] **Step 2: Trigger manually**

```powershell
schtasks /Run /TN "ClaudeApprovalPoller"
Start-Sleep -Seconds 3
schtasks /Query /TN "ClaudeApprovalPoller" /FO LIST | Select-String "Last Run|Last Result"
```
Expected: Last Result = 0.

### Task D.13: E2E — trivial 8D dispatch test

**Files:** none modified; runtime verification only.

- [ ] **Step 1: Run trivial 8D**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 run_8d.py "Test problem for SDK auto-dispatch verification — should produce minimal Phase 4 actions"
```
Expected: pipeline runs through phase_7 → phase_10, then exits with "Run incomplete. Use --resume <run_id>" message OR "awaiting approval" status.

- [ ] **Step 2: Verify gate file appeared**

```bash
ls ~/.claude/.pending-8d-approvals/
```
Expected: one JSON file matching the run_id.

- [ ] **Step 3: Approve via CLI**

```bash
py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py --resume <run_id> --approve
```
Expected: phase_11 dispatches child SDK; child runs executing-plans on the trivial plan; final state phase_11_complete=True.

- [ ] **Step 4: Verify cleanup**

```bash
ls ~/.claude/.pending-8d-approvals/
```
Expected: empty (run_8d.py cleans on phase_11 success).

---

## Task E: ECOSYSTEM.md update + email

**Files:**
- Read: `C:/Users/Kuangyu/.claude/plans/fuzzy-watching-mitten.md` (original plan)
- Create: `D:/D-claude/ECOSYSTEM.md`

- [ ] **Step 1: Read fuzzy-watching-mitten plan inventory section**

Use Read tool. Note all tagged components ([P1]/[P2]/[P3]).

- [ ] **Step 2: Augment inventory with today's additions**

Add to inventory (append, don't replace):
- **R13** (output-boundary category) in gate-rules.yaml
- **`~/.claude/governance/`** directory: owners.yaml, rule-acceptance.md, discovery-charter.yaml, escape_log.yaml (now 7 entries), audit-r13.sh, run-discovery-audit.sh
- **`~/.claude/.pending-8d-approvals/`** convention (NEW from Task D)
- **R13 hook** (hook-r13-output-boundary.py) — wired with Write|Edit|Bash|mcp__.*|PowerShell matcher
- **3 new SDK auto-dispatch hooks**: sessionstart-8d-approval-banner.sh, userpromptsubmit-8d-approval-detect.sh, outlook-approval-poller.py
- **2 new schtasks entries**: ClaudeDiscoveryAudit (quarterly), ClaudeApprovalPoller (10-min)
- **claude-hooks `discover` subcommand** + lint matcher↔extractor parity (NEW from Task B)
- **skill-8d-mrc Phase 8-11 SDK auto-dispatch** (NEW from Task D)
- **2 new wiki concepts**: degraded-emission-with-warning, long-running-progress-heartbeat
- **R2/R8 predicate sharpening** (today's pre-batch fix)

- [ ] **Step 3: Skip Phase 0 (already done as Task A)**

Per "deduplicate" instruction in plan brief.

- [ ] **Step 4: Execute fuzzy-watching-mitten Tasks 4-23**

Follow that plan's existing tasks; no need to re-derive content. Use existing diagrams 1-9. Keep word budget 5500-7000.

- [ ] **Step 5: Run fuzzy-watching-mitten Task 23 self-review**

All 7 sub-steps from that plan (inventory cross-check, placeholder scan, rule-ID scan, file-path scan, Mermaid render, word count, voice pass).

- [ ] **Step 6: Commit ECOSYSTEM.md**

```bash
cd D:/D-claude && git rev-parse --git-dir 2>/dev/null && \
  git add ECOSYSTEM.md && \
  git commit -m "docs: ECOSYSTEM.md snapshot 2026-04-25 (post-batch)"
```
If D:/D-claude is not git-controlled, skip the commit.

- [ ] **Step 7: Send via email**

```bash
py -3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'D:/D-claude/skills/skill-8d-mrc')
from eightd.delivery.email import send_markdown_email
body = Path('D:/D-claude/ECOSYSTEM.md').read_text(encoding='utf-8')
ok = send_markdown_email(subject='ECOSYSTEM.md — 2026-04-25 snapshot', body_md=body)
print('sent' if ok else 'failed')
"
```
Expected: `sent`.

If email render/send fails per R13 (degraded-emission-with-warning), DO NOT ship a degraded version — fix the rendering then resend. R13 catches this class.

---

## Verification (end-to-end, post-batch)

1. `bash ~/.claude/hooks/stop-hook-no-handoff-gate.sh < /dev/null` doesn't crash; R12 block JSON shape correct (Task A).
2. `py -3 ~/.claude/bin/claude-hooks lint` shows `[matcher↔extractor parity check] OK` (Task B).
3. Pipeline-gap 8D triage section appended to this plan (Task C).
4. `pytest -x` in skill-8d-mrc passes all tests including new test_phase_8/9/10/11/test_child_runner (Task D).
5. Trivial 8D dispatch test (Task D.13) reaches phase_11_complete=True after CLI approve.
6. `D:/D-claude/ECOSYSTEM.md` exists, parses clean, all 9 Mermaid blocks render, inventory cross-check passes (Task E).
7. ECOSYSTEM.md email delivered.

## Non-goals

- Telegram inline-button approval portal (Portal C deferred per spec)
- Per-batch approval inside child SDK execution
- Multiple concurrent 8D runs sharing approval state
- Auto-cleanup of stale gate files >30d unanswered
- ECOSYSTEM.md auto-refresh on ecosystem changes (still manual / dated snapshot)

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Issue #573 evolves; new env var added by Anthropic | Mitigation in one file (child_runner.py); pop additional vars when surfaced |
| SessionStart hook runs background-resume but Claude Code session terminates before completion | nohup detaches; heartbeat to log file is the visibility channel |
| Gate file race (email + session simultaneous approval) | Last-writer-wins on JSON; phase_11 idempotent via LangGraph checkpoint |
| ECOSYSTEM.md drifts within hours of writing as more changes ship | Dated snapshot + acknowledge stale-fast in Part 0 |
| outlook-approval-poller.py hangs on Outlook COM | Default 200-item scan + 10-min interval bounds blast radius; failure mode is "Portal A degraded, Portal B still works" |
| phase_7 email-send removal breaks tests that asserted email sends | Update test_phase_7 to assert NO email-send; phase_10's test asserts email IS sent (FRC verified by tests) |

## Execution order (explicit)

1. Task A — R12 JSON fix (~15 min)
2. Task B — lint parity check (~30 min)
3. Task C — pipeline-gap triage (~30 min)
4. Task D.1-D.13 — SDK auto-dispatch (~3-4 hr)
5. Task E — ECOSYSTEM.md + email (~3 hr)

Total: ~7-8 hr.

---

## Task C output: Pipeline-gap 8D triage

Source: `D:/D-claude/skills/skill-8d-mrc/docs/8d-reports/8d-2026-04-25-gate-pipeline-enforcement-gap-the-policy-engine-has-multiple.md`

| # | Section | Item | Classification | Disposition |
|---|---|---|---|---|
| 1 | B (Corrective TRC-NC) | Rewrite R2 predicate to parse structured JSONL for `tool_use.name=="Skill"`; add `hook_trajectory_aggregator.py`; wire R2/R3/R4/R5 to state-side `sizable_task_ts`; add unit-test fixtures | new-work | file for next session — see primer item [1] |
| 2 | B (Corrective TRC-ND) | Freeze 2026-04-25 escaped session as fixture; write `test_r2_brainstorm_predicate.py`; wire pre-commit on gate-rules.yaml; add `r2-predicate-trace.py` diagnostic | new-work | file for next session — see primer item [2]; first-priority in next session (smallest item, unblocks #1) |
| 3 | B (Corrective MRC-NC) | Explicitly collapsed into B2-Q3 prevention matrix by the report | not-applicable | duplicate — covered by item #7 (B2-MRC-NC) |
| 4 | B (Corrective MRC-ND) | Explicitly collapsed into B2-Q4 prevention matrix by the report | not-applicable | duplicate — covered by item #8 (B2-MRC-ND) |
| 5 | B2 (Prevention TRC-NC) | "Corrective doubles as prevention at TRC scope" — same structural fix as B-Q1 | not-applicable | duplicate reference to item #1; resolved when #1 is implemented |
| 6 | B2 (Prevention TRC-ND) | "Corrective doubles as prevention at TRC detection scope" — same fixture+gate as B-Q2 | not-applicable | duplicate reference to item #2; resolved when #2 is implemented |
| 7 | B2 (Prevention MRC-NC) | Three coordinated artifacts: (1) `pipeline-state-gate.py` PreToolUse hook with per-session FSM (phase: none→brainstormed→planned→executing); (2) `governance/gate-design-standard.md` + ADR template (trigger_basis / adversarial_coverage / escalation_rung fields) + pre-commit enforcement; (3) `monthly-gate-audit.py` cross-referencing feedback_*.md vs gate-rules.yaml | new-work | file for next session — see primer item [3]; large (~6+ hr); the Predicate-Generality charter from fix #2 is partial overlap on the ADR concept but does NOT implement the FSM hook or the monthly audit |
| 8 | B2 (Prevention MRC-ND) | Rule-Effectiveness Lifecycle: schema-required fields on gate-rules.yaml (coverage_targets, paired_detector, bypass_classes); mandatory regression fixture corpus per rule; `rule-effectiveness-audit.py` weekly cron; `CHARTER.md` RACI | new-work | file for next session — see primer item [4]; large (~4+ hr); depends on item #7's gate-design-standard landing first |

### Summary

- **Already-fixed:** 0 items
  - Note: fix #7 (R2 predicate sharpening) removed a false-POSITIVE trigger (`^go\s*$`). The report's Q1 addresses a false-NEGATIVE (R2 failing to detect a legitimate `Skill(superpowers:brainstorming)` invocation). These are different bugs. Fix #7 does not satisfy Q1.
  - fix #2 (Predicate-Generality charter) added `rule-acceptance.md` and `owners.yaml` — structurally related to Q3's gate-design-standard requirement, but does NOT deliver the `trigger_basis`/`adversarial_coverage`/`escalation_rung` fields on gate-rules.yaml, the FSM hook, or the monthly audit cron. Not sufficient to mark Q3 as already-fixed.
- **Not-applicable:** 4 items (items #3, #4, #5, #6 — all duplicates explicitly collapsed by the report itself)
- **New-work — slotted into this batch:** 0 items (batch is already at ~7-8 hr; adding any new-work would overload it)
- **New-work — filed for next session:** 4 items (items #1, #2, #7, #8; written to `~/.claude/.next-session-primer.md`)

### New-work — slotted

None. This batch (Tasks A–E) is already at estimated ~7-8 hr. All new-work items are deferred to the next session to keep this batch executable.

### New-work — filed for next session

The following items have been written to `~/.claude/.next-session-primer.md`:

1. **[R2-Q2] Freeze regression fixture + predicate test + pre-commit wire** — `~/.claude/tests/fixtures/transcripts/2026-04-25-r2-brainstorm-miss.jsonl` + `test_r2_brainstorm_predicate.py` + pre-commit on gate-rules.yaml + `r2-predicate-trace.py` diagnostic. Target date from report: 2026-04-26. ~1.5-2 hr. Recommended first priority since it unblocks Q1 validation.

2. **[R2-Q1] Structured JSONL predicate rewrite + trajectory aggregator** — rewrite R2 predicate to match `tool_use.name=="Skill"` in structured transcript; add `hook_trajectory_aggregator.py` with rolling 20-call window writing `sizable_task_ts`; wire R2/R3/R4/R5 to read state-side; two fixture tests. Target from report: 2026-04-28. ~4-6 hr. Depends on Q2 fixtures being landed first.

3. **[B2-Q3] Behavior-coupled pipeline-state-gate + gate-design-standard** — `pipeline-state-gate.py` PreToolUse FSM hook; `governance/gate-design-standard.md` + ADR template; `monthly-gate-audit.py` schtask. ~6+ hr. Largest item; partially overlaps with the Predicate-Generality charter (fix #2) but is substantially additional work.

4. **[B2-Q4] Rule-Effectiveness Lifecycle** — schema-required fields (coverage_targets, paired_detector, bypass_classes) on gate-rules.yaml; `pre-commit-gate-rules-schema.py` validator; `hooks/fixtures/gate-rules/R<id>.yaml` per-rule fixture corpus; `rule-effectiveness-audit.py` weekly cron; `CHARTER.md` RACI. ~4+ hr. Depends on Q3 gate-design-standard landing first.
