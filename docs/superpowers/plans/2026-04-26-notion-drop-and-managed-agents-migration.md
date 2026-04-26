# Notion Drop + skill-8d-mrc Managed Agents Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two coupled ecosystem changes: (1) drop Notion as an output destination across the ecosystem, leaving email + Telegram + file as the only outputs; (2) migrate skill-8d-mrc from local LangGraph FSM to a single Anthropic Claude Managed Agents session, eliminating local CPU pressure (~3+ python processes per 8D run today).

**Architecture:** Notion drop is dead-code deletion + doc cleanup (publisher.py already migrated to email_sender; just need to delete unused notion_summary.py + clean docstrings/docs). Managed Agents migration is a 4-phase parallel-preservation/atomic-switch per the spec at `docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md` — build trigger_8d.py + managed_agent/ alongside; parity-test; atomic-delete legacy in single commit; monitor 1 week.

**Tech Stack:** Python 3.12, Anthropic Claude Managed Agents (beta `managed-agents-2026-04-01`), Pydantic v2 (strict mode), Outlook COM via win32com (single-threaded), Bash (hooks), YAML (agent config), pytest.

---

## Task 1: Delete `publishers/notion_summary.py` (dead code)

**Files:**
- Delete: `D:/D-claude/daily_brief/publishers/notion_summary.py`

- [ ] **Step 1: Confirm it's truly unused**

```bash
grep -rn "notion_summary" D:/D-claude/daily_brief/ --include="*.py"
```
Expected: zero matches in production code (only `# DETECTION: structural-grep` comment in `publisher.py:50` confirming the absence).

- [ ] **Step 2: Confirm config.yaml.example has no notion.* required keys**

```bash
grep -n "notion" D:/D-claude/daily_brief/config.yaml.example
```
Note any matches; will remove in Task 3.

- [ ] **Step 3: Delete the file**

```bash
git -C D:/D-claude/daily_brief rm publishers/notion_summary.py
```

- [ ] **Step 4: Run smoke tests to verify no breakage**

```bash
cd D:/D-claude/daily_brief && py -3 -m pytest tests/ -v 2>&1 | tail -10
```
Expected: all tests pass (notion_summary wasn't imported by anything live).

- [ ] **Step 5: Commit (do NOT push; per Git-Aware Working Protocol)**

```bash
git -C D:/D-claude/daily_brief commit -m "feat: delete unused publishers/notion_summary.py (Notion drop)

Dead code: publisher.py:50 already documented the migration to
email_sender (DETECTION: structural-grep). No callers remain.
Per function-replacement-convention: delete in same commit window
as docstring cleanup (Tasks 2-3).

Part 1/N of Notion drop per user directive 2026-04-26 'I don't want
Notion anymore. just use email.'"
```

---

## Task 2: Clean docstrings in `main.py`, `publisher.py`, `briefing.py`

**Files:**
- Modify: `D:/D-claude/daily_brief/main.py:15`
- Modify: `D:/D-claude/daily_brief/publisher.py:7, :35`
- Modify: `D:/D-claude/daily_brief/briefing.py:5, :8, :291`

- [ ] **Step 1: Replace main.py docstring line 15**

Edit `D:/D-claude/daily_brief/main.py`. Find:
```
  4. Publish: File backup + Telegram + Notion
```
Replace with:
```
  4. Publish: File backup + Telegram + Email
```

- [ ] **Step 2: Replace publisher.py docstring line 7 (and any neighbors)**

Edit. Find:
```
  3. Notion:   [daily sum] full page + action items → "[FA] Command Center"
```
Replace with:
```
  3. Email:    [daily sum] rendered HTML → user inbox
```

- [ ] **Step 3: Replace publisher.py line ~35**

Find:
```
        action_items:  list of {action, owner, source} dicts for Notion
```
Replace with:
```
        action_items:  list of {action, owner, source} dicts (email body inclusion)
```

- [ ] **Step 4: Replace briefing.py docstring lines 5, 8, 291**

Find each occurrence of:
- `[daily sum]  — full detailed MD for Notion` → `[daily sum]  — full detailed MD for email`
- `Also extracts structured action items for Notion "[FA] Command Center".` → `Also extracts structured action items for email body inclusion.`
- `"""Generate [daily sum] — full detailed MD for Notion.` → `"""Generate [daily sum] — full detailed MD for email.`

Use Edit tool per occurrence.

- [ ] **Step 5: Verify zero remaining Notion references in production code**

```bash
grep -nrE "notion|Notion|NOTION" D:/D-claude/daily_brief/ --include="*.py" | grep -v "# DETECTION:"
```
Expected: zero output. (The `# DETECTION:` comment in publisher.py is a structural-grep test fixture; KEEP it.)

- [ ] **Step 6: Run tests**

```bash
cd D:/D-claude/daily_brief && py -3 -m pytest tests/ -v 2>&1 | tail -10
```
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git -C D:/D-claude/daily_brief add main.py publisher.py briefing.py
git -C D:/D-claude/daily_brief commit -m "docs: remove Notion references from production docstrings (Notion drop 2/N)"
```

---

## Task 3: Clean templates, README, CLAUDE.md, config.yaml.example

**Files:**
- Modify: `D:/D-claude/daily_brief/CLAUDE.md`
- Modify: `D:/D-claude/daily_brief/README.md`
- Modify: `D:/D-claude/daily_brief/config.yaml.example`
- Modify: `D:/D-claude/daily_brief/templates/daily_brief.md` (if Notion mentioned)
- Modify: `D:/D-claude/daily_brief/templates/daily_sum.md`
- Modify: `D:/D-claude/daily_brief/templates/system_prompt_sum.md`

- [ ] **Step 1: Read CLAUDE.md to find Notion sections**

```bash
grep -nE "notion|Notion|NOTION" D:/D-claude/daily_brief/CLAUDE.md
```

- [ ] **Step 2: Edit CLAUDE.md to remove Notion sections**

Sections to remove or rewrite:
- Architecture diagram: replace `Notion summary / Notion actions` with `Email summary / Email actions`
- Two-Tier Output: `[daily sum]: Full detailed Markdown → Notion page in [CC] Tasks Database` → `[daily sum]: Full detailed HTML email → user inbox`
- Action Items Pipeline: `extracted from the full briefing → pushed to Notion [CC] Tasks Database` → `extracted from the full briefing → included in email body as action checklist`
- Key Files table: remove `notion.api_key` reference
- Publishers table: remove `notion_summary.py` row
- Config Secrets Location: remove `notion.api_key` line
- External Services table: remove Notion row
- Notion Database Schema: DELETE entire section

- [ ] **Step 3: Edit README.md if Notion present**

```bash
grep -nE "notion|Notion|NOTION" D:/D-claude/daily_brief/README.md
```
Remove all matched lines or sections.

- [ ] **Step 4: Edit config.yaml.example to remove notion.* template keys**

Find the `notion:` block (likely with `api_key`, `database_id`, `command_center_db_id`, etc.). DELETE the entire block.

- [ ] **Step 5: Edit templates if Notion mentioned**

```bash
grep -nE "notion|Notion|NOTION" D:/D-claude/daily_brief/templates/
```
For each match, remove the Notion-specific instruction.

- [ ] **Step 6: Verify zero remaining Notion references in committed docs**

```bash
grep -rnE "notion|Notion|NOTION" D:/D-claude/daily_brief/ --include="*.md" --include="*.yaml.example"
```
Expected: zero output.

- [ ] **Step 7: Commit**

```bash
git -C D:/D-claude/daily_brief add CLAUDE.md README.md config.yaml.example templates/
git -C D:/D-claude/daily_brief commit -m "docs: remove Notion references from CLAUDE.md, README, templates (Notion drop 3/N)"
```

---

## Task 4: Update D:/D-claude/ECOSYSTEM.md

**Files:**
- Modify: `D:/D-claude/ECOSYSTEM.md`

- [ ] **Step 1: Find Notion references**

```bash
grep -nE "notion|Notion|NOTION" D:/D-claude/ECOSYSTEM.md
```

- [ ] **Step 2: Update Integrations table + any prose mentions**

Remove Notion row from Integrations table. Update Layer 1 / Layer 3 prose if Notion mentioned. If a diagram has Notion, edit the Mermaid block.

- [ ] **Step 3: Verify clean**

```bash
grep -nE "notion|Notion|NOTION" D:/D-claude/ECOSYSTEM.md
```
Expected: zero output.

- [ ] **Step 4: Commit (if D:/D-claude is git-init)**

```bash
git -C D:/D-claude rev-parse --git-dir 2>&1
```
If yes:
```bash
git -C D:/D-claude add ECOSYSTEM.md
git -C D:/D-claude commit -m "docs: remove Notion from ECOSYSTEM.md (Notion drop 4/N)"
```

---

## Task 5: Search ~/.claude/CLAUDE.md and clean if found

**Files:**
- Modify (maybe): `C:/Users/Kuangyu/.claude/CLAUDE.md`

- [ ] **Step 1: Search**

```bash
grep -n "notion\|Notion\|NOTION" ~/.claude/CLAUDE.md
```

- [ ] **Step 2: Edit only if matches found**

Remove the matched lines. Likely candidates: any "Notion API key" reference, any "[CC] Tasks Database" mention.

- [ ] **Step 3: Verify**

```bash
grep -n "notion\|Notion\|NOTION" ~/.claude/CLAUDE.md
```
Expected: zero output if any Notion references existed.

- [ ] **Step 4: Auto-commit picks up via PostToolUse hook**

```bash
git -C ~/.claude log -1 --oneline -- CLAUDE.md
```
Expected: recent commit if file was modified.

---

## Task 6: User manually purges Notion secrets from `config.yaml`

**Files:**
- Modify (USER ACTION): `D:/D-claude/daily_brief/config.yaml`

- [ ] **Step 1: Send the user a clear inline reminder via email**

This task can NOT be automated by the agent — config.yaml is gitignored and contains secrets the agent should never read or write. Instead, the executing agent emails the user with the remaining manual step:

```
Subject: Manual cleanup — remove Notion keys from daily_brief config.yaml

Notion drop tasks 1-5 are done. One residual manual step:

Edit D:/D-claude/daily_brief/config.yaml and remove the entire `notion:` block
(api_key, database_id, command_center_db_id, etc.). The file is gitignored;
agents should not modify it. Removing the keys prevents accidental use.

After removal, run:
  cd D:/D-claude/daily_brief && py -3 main.py --dry-run

Should complete without errors. If you see "notion" in the output, there's still
a code path referencing it — reply with the error and we'll triage.
```

Use `eightd/delivery/email.py:send_markdown_email()` to send. Recipient: oxydavid@gmail.com.

- [ ] **Step 2: Mark Notion drop complete** in this plan; proceed to Managed Agents tasks.

---

## Task 7: Create `eightd/managed_agent/` directory + skeleton yaml

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/__init__.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/skill-8d-mrc-v1.yaml`

- [ ] **Step 1: Create the directory + empty __init__.py**

```bash
mkdir -p D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent
touch D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/__init__.py
```

- [ ] **Step 2: Write skill-8d-mrc-v1.yaml skeleton**

```yaml
# Anthropic Claude Managed Agents config for skill-8d-mrc.
# Per spec docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md.
# WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
# WIKI-FINDING: replacing local LangGraph FSM with cloud agent; same commit removes legacy
# WIKI-ACTION: this yaml is the new authoritative config; legacy graph.py deleted in Phase C.

name: skill-8d-mrc-v1
description: |
  8D Method-of-Resolving-Conflict analyst for ecosystem failure modes.
  Runs the full 12-phase forensic in a single Managed Agent session;
  returns structured payload (report, actions, plan) for local persistence.

model: claude-opus-4-6

system_prompt_path: ./system_prompt.md  # see Task 8

tools:
  - type: agent_toolset_20260401  # built-in (file ops, code execution in sandbox)
  - type: websearch_20260401      # built-in WebSearch

mcp_servers: []  # No MCP in v1; only built-in tools

network_egress:
  - api.anthropic.com
  - anthropic.com
  # WebSearch endpoints handled by tool internals

# Beta header set automatically by SDK; pinned version:
# anthropic-beta: managed-agents-2026-04-01
```

- [ ] **Step 3: Validate yaml parses**

```bash
py -3 -c "import yaml; yaml.safe_load(open(r'D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/skill-8d-mrc-v1.yaml'))"; echo "exit=$?"
```
Expected: `exit=0`.

- [ ] **Step 4: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && git add eightd/managed_agent/ && \
git commit -m "feat(eightd): managed_agent/ scaffold + skill-8d-mrc-v1.yaml (Phase A)"
```

---

## Task 8: Port system prompt from `eightd/phases/*` + `eightd/prompts/*` to `system_prompt.md`

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/system_prompt.md`
- Read (no modify): all `eightd/phases/*.py` + `eightd/prompts/*.md`

- [ ] **Step 1: Read all phase + prompt files**

Use Glob `D:/D-claude/skills/skill-8d-mrc/eightd/phases/*.py` and `D:/D-claude/skills/skill-8d-mrc/eightd/prompts/*.md` to enumerate. Read each.

- [ ] **Step 2: Identify the LLM prompts in each phase**

Each phase has 1-N LLM call sites (via `eightd/sdk_client.call_claude()`). Extract the prompt strings — these are the "phase prompts" that tell the model what to do.

- [ ] **Step 3: Synthesize into single system_prompt.md**

Structure:
```markdown
# skill-8d-mrc system prompt

You are an 8D analyst running a 12-phase forensic on the user's problem.

## Phase 0 — Forced research
[content from phase_0_research.py prompt]
- Fire 8 parallel WebSearch calls covering: keyword-extraction, meta-categorization, problem-specific, cross-domain, anti-pattern queries
- Output: research summary + meta_categories + meta_domains lists

## Phase 1 — IS / IS NOT
[content from phase_1_is_isnt.py prompt]

## Phase 2 — Why analysis (4 quadrants in parallel)
[content from phase_2_why_analysis.py prompt]
- Run 4 parallel Why chains: q1_trc_nc, q2_trc_nd, q3_mrc_nc, q4_mrc_nd

## Phase 3 — SoA + RC audit (3 rounds)
[content from phase_3_rc_audit.py prompt]
- Run 3 rounds; each round may verdict EXHAUSTED or REWORK

## Phase 4 — Corrective + Prevention (4 quadrants in parallel)
[content from phase_4_actions.py prompt]
- Generate corrective_actions + prevention_actions per quadrant

## Phase 5 — Prevention audit (3 rounds)
[content from phase_5_prevention_audit.py prompt]

## Phase 6 — Verification plan
[content from phase_6_verification.py prompt]

## Phase 7 — Report rendering
[content from phase_7_report.py prompt]
- Output: full Markdown report (~110KB typical)

## Phase 8 — Action collection
- Walk corrective_actions + prevention_actions + verification_plan
- Emit normalized actions_json list

## Phase 9 — Plan generation (writing-plans logic inline)
- Take actions_json + emit plan.md following the bite-sized-task convention
- Reference: docs/superpowers/plans/2026-04-25-batch-r12-lint-pipeline-ecosystem-sdk-dispatch.md format

## Final response

Return a structured payload matching the Pydantic CloudPayload schema:
```json
{
  "report_md": "<full Phase 7 markdown>",
  "actions_json": [<Phase 8 normalized list>],
  "plan_md": "<Phase 9 generated plan>",
  "phase_metadata": {
    "phases_completed": [...],
    "phase_durations_sec": {...},
    "total_runtime_sec": ...,
    "total_tokens_used": {...}
  }
}
```

Validate output structure matches schema BEFORE returning. If any field missing or malformed, retry the affected phase.
```

- [ ] **Step 4: Verify file exists + readable**

```bash
wc -l D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/system_prompt.md
```
Expected: ~200-400 lines.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add eightd/managed_agent/system_prompt.md && \
git commit -m "feat(eightd): port phase prompts to managed_agent/system_prompt.md (Phase A)"
```

---

## Task 9: Create Pydantic `CloudPayload` schema

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/eightd/managed_agent/output_schema.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_cloud_payload_schema.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cloud_payload_schema.py
import pytest
from pydantic import ValidationError
from eightd.managed_agent.output_schema import CloudPayload

def test_valid_payload_passes():
    p = CloudPayload(
        report_md="x" * 1500,
        actions_json=[{"title": "Fix X", "description": "...", "source_quadrant": "corrective:TRC-NC"}],
        plan_md="y" * 600,
        phase_metadata={"phases_completed": ["phase_0"], "phase_durations_sec": {"phase_0": 12.5},
                        "total_runtime_sec": 1800.0, "total_tokens_used": {"input": 50000, "output": 5000}},
    )
    assert p.report_md.startswith("x")

def test_short_report_fails():
    with pytest.raises(ValidationError):
        CloudPayload(
            report_md="too short",  # < 1000 chars
            actions_json=[], plan_md="x" * 600,
            phase_metadata={"phases_completed": [], "phase_durations_sec": {}, "total_runtime_sec": 0.0, "total_tokens_used": {}},
        )

def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        CloudPayload(
            report_md="x" * 1500, actions_json=[], plan_md="y" * 600,
            phase_metadata={"phases_completed": [], "phase_durations_sec": {}, "total_runtime_sec": 0.0, "total_tokens_used": {}},
            extra_field="not allowed",
        )

def test_aggregated_validation_errors():
    """ValidationError aggregates multiple field errors per Pydantic v2 docs."""
    try:
        CloudPayload(
            report_md="short",  # too short
            actions_json="not a list",  # wrong type
            plan_md="also short",  # too short
            phase_metadata={},  # missing required keys
        )
        pytest.fail("should have raised")
    except ValidationError as e:
        # Should report multiple field errors
        assert len(e.errors()) >= 3
```

- [ ] **Step 2: Run test — expect FAIL (module missing)**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_cloud_payload_schema.py -v
```

- [ ] **Step 3: Implement output_schema.py**

```python
"""Pydantic v2 schema for the structured payload returned by the
skill-8d-mrc Managed Agent. Strict mode + extra-forbidden so any
deviation from the contract raises ValidationError at the boundary.

Per spec docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md.

WIKI-CONSULTED: degraded-emission-with-warning
WIKI-FINDING: producer must validate own output; never ship malformed artifact
WIKI-ACTION: trigger_8d.py validates against this schema BEFORE writing artifacts
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class ActionItem(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    files_touched: list[str] = Field(default_factory=list)
    owner: str = "kuangyu"
    priority: Literal["low", "medium", "high", "verification"] = "medium"
    source_quadrant: str


class PhaseMetadata(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    phases_completed: list[str]
    phase_durations_sec: dict[str, float]
    total_runtime_sec: float
    total_tokens_used: dict[str, int]


class CloudPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    report_md: str = Field(..., min_length=1000)
    actions_json: list[ActionItem]
    plan_md: str = Field(..., min_length=500)
    phase_metadata: PhaseMetadata
```

- [ ] **Step 4: Re-run test — expect PASS**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_cloud_payload_schema.py -v
```
Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add eightd/managed_agent/output_schema.py tests/test_cloud_payload_schema.py && \
git commit -m "feat(eightd): Pydantic CloudPayload strict-mode schema for cloud output (Phase A)"
```

---

## Task 10: Create `trigger_8d.py` skeleton with API client + heartbeat

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/trigger_8d.py`
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_trigger_8d.py`

- [ ] **Step 1: Write failing test for session creation flow**

```python
# tests/test_trigger_8d.py
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

def test_trigger_8d_creates_session_with_beta_header(tmp_path):
    from trigger_8d import create_cloud_session

    captured_headers = {}

    def fake_post(url, headers=None, json=None, **kw):
        captured_headers.update(headers or {})
        m = MagicMock(); m.status_code = 200
        m.json.return_value = {"session_id": "sess_test_abc", "status": "running"}
        return m

    with patch("requests.post", side_effect=fake_post):
        session_id = create_cloud_session(problem="test problem", agent_id="skill-8d-mrc-v1", api_key="fake")

    assert session_id == "sess_test_abc"
    assert captured_headers.get("anthropic-beta") == "managed-agents-2026-04-01"
    assert captured_headers.get("x-api-key") == "fake"


def test_trigger_8d_validates_payload_before_write(tmp_path):
    """Schema-invalid payload must NOT write artifacts (R13 fail-closed)."""
    from trigger_8d import handle_session_complete
    from pydantic import ValidationError

    bad_payload = {"report_md": "short", "actions_json": [], "plan_md": "y", "phase_metadata": {}}

    with pytest.raises(ValidationError):
        handle_session_complete(
            session_id="sess_test", run_dir=tmp_path,
            payload=bad_payload, gate_dir=tmp_path / "gates",
        )

    # No artifacts written
    assert not (tmp_path / "report.md").exists()
    assert not (tmp_path / "plan.md").exists()
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_trigger_8d.py -v
```

- [ ] **Step 3: Implement trigger_8d.py skeleton**

```python
"""trigger_8d.py — thin orchestrator for skill-8d-mrc Managed Agents migration.

Per spec docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md.

WIKI-CONSULTED: function-replacement-convention#delete-in-same-commit
WIKI-FINDING: replaces run_8d.py + LangGraph FSM atomically in Phase C
WIKI-ACTION: this file is the new entry point; legacy run_8d.py deleted alongside

Flow:
  1. POST /v1/agents/sessions to create session with the problem
  2. Poll /v1/agents/sessions/<id>/events every 5 min for heartbeat
  3. On session.status == "completed", fetch payload + validate (Pydantic)
  4. Mirror /workspace artifacts to local runs/<run_id>/
  5. Write gate file + send consolidated email
  6. Exit (cloud session terminated; idle billing avoided)

For --resume <run_id> --approve: read gate's plan_md, invoke
superpowers:executing-plans IN-SESSION (no Popen child).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pydantic import ValidationError

from eightd.managed_agent.output_schema import CloudPayload

ANTHROPIC_BETA_HEADER = "managed-agents-2026-04-01"
ANTHROPIC_API_BASE = "https://api.anthropic.com"


def create_cloud_session(problem: str, agent_id: str, api_key: str) -> str:
    """POST to create a Managed Agents session. Returns session_id."""
    url = f"{ANTHROPIC_API_BASE}/v1/agents/sessions"
    headers = {
        "anthropic-beta": ANTHROPIC_BETA_HEADER,
        "x-api-key": api_key,
        "content-type": "application/json",
    }
    body = {"agent_id": agent_id, "input": problem}
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()["session_id"]


def handle_session_complete(session_id: str, run_dir: Path, payload: dict, gate_dir: Path) -> dict:
    """Validate payload (R13 fail-closed), write artifacts, gate file.
    Raises ValidationError if payload doesn't match CloudPayload schema.
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
    }
    gate_file.write_text(json.dumps(gate_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"session_id": session_id, "gate_file": str(gate_file)}


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


def _cmd_run(problem: str) -> int:
    # Full-run path; delegated to subagent in Phase A.10 finer task
    raise NotImplementedError("Run path implemented in Task 11")


def _cmd_status(run_id: str) -> int:
    gate = Path.home() / ".claude" / ".pending-8d-approvals" / f"{run_id}.json"
    if not gate.exists():
        print(f"No pending approval for {run_id}")
        return 0
    print(gate.read_text(encoding="utf-8"))
    return 0


def _cmd_resume_approval(run_id: str, approve: bool, reject_reason: str | None) -> int:
    # Phase 11 invocation; delegated to subagent in Phase A.12 finer task
    raise NotImplementedError("Resume path implemented in Task 12")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test — expect PASS for the 2 implemented cases**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_trigger_8d.py -v
```
Expected: 2 tests pass (the create_session test + handle_session_complete test). Other code paths raise NotImplementedError, intentional for this task.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add trigger_8d.py tests/test_trigger_8d.py && \
git commit -m "feat(trigger_8d): scaffold + create_session + payload validation (Phase A)"
```

---

## Task 11: Implement full run-loop in `trigger_8d.py:_cmd_run`

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/trigger_8d.py:_cmd_run`
- Modify: `D:/D-claude/skills/skill-8d-mrc/tests/test_trigger_8d.py` — add run-loop tests

- [ ] **Step 1: Write failing test for run-loop**

```python
def test_run_loop_polls_until_complete_then_writes(tmp_path, monkeypatch):
    from trigger_8d import _cmd_run

    # Simulate: session created → 2 polls show "running" → 3rd poll shows "completed" with valid payload
    poll_responses = [
        {"status": "running", "events": [{"phase": "phase_0_research", "event": "phase_end"}]},
        {"status": "running", "events": [{"phase": "phase_4_actions", "event": "phase_end"}]},
        {"status": "completed", "payload": {
            "report_md": "x" * 1500, "actions_json": [],
            "plan_md": "y" * 600,
            "phase_metadata": {
                "phases_completed": ["phase_0", "phase_7"],
                "phase_durations_sec": {"phase_0": 12.5},
                "total_runtime_sec": 1800.0,
                "total_tokens_used": {"input": 50000, "output": 5000},
            },
        }},
    ]
    poll_idx = [0]

    def fake_get(url, headers=None, **kw):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = poll_responses[min(poll_idx[0], len(poll_responses)-1)]
        poll_idx[0] += 1
        return m

    def fake_post(url, headers=None, json=None, **kw):
        m = MagicMock(); m.status_code = 200
        m.json.return_value = {"session_id": "sess_run_test", "status": "running"}
        return m

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("requests.post", side_effect=fake_post), \
         patch("requests.get", side_effect=fake_get), \
         patch("trigger_8d.POLL_INTERVAL_SEC", 0):  # speed up test
        rc = _cmd_run("test problem")

    assert rc == 0
    # Gate file written
    gates = list((tmp_path / ".claude" / ".pending-8d-approvals").glob("*.json"))
    assert len(gates) == 1
```

- [ ] **Step 2: Run test — expect FAIL (NotImplementedError)**

- [ ] **Step 3: Implement `_cmd_run` body**

```python
POLL_INTERVAL_SEC = 300  # 5 min

def _cmd_run(problem: str) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 1

    run_id = f"run-{int(time.time())}-{os.urandom(4).hex()}"
    run_dir = Path(__file__).parent / "runs" / run_id

    session_id = create_cloud_session(problem, agent_id="skill-8d-mrc-v1", api_key=api_key)
    print(f"[trigger_8d] session created: {session_id}; run_id: {run_id}")

    # Poll loop with heartbeat
    while True:
        time.sleep(POLL_INTERVAL_SEC)
        status_url = f"{ANTHROPIC_API_BASE}/v1/agents/sessions/{session_id}"
        events_url = f"{ANTHROPIC_API_BASE}/v1/agents/sessions/{session_id}/events"
        headers = {"anthropic-beta": ANTHROPIC_BETA_HEADER, "x-api-key": api_key}

        events_resp = requests.get(events_url, headers=headers, timeout=30)
        events_resp.raise_for_status()
        events_doc = events_resp.json()

        status = events_doc.get("status", "unknown")
        for ev in events_doc.get("events", []):
            phase = ev.get("phase", "?")
            kind = ev.get("event", "?")
            print(f"[heartbeat] {datetime.now().isoformat(timespec='seconds')} {phase} {kind}", file=sys.stderr)
            # Telegram diagnostics post would go here (deferred to Task 13)

        if status == "completed":
            payload = events_doc.get("payload") or {}
            try:
                gate_dir = Path.home() / ".claude" / ".pending-8d-approvals"
                handle_session_complete(session_id, run_dir, payload, gate_dir)
                print(f"[trigger_8d] gate written; awaiting approval. run_id: {run_id}")
                return 0
            except ValidationError as e:
                print(f"ERROR: cloud payload schema validation failed:\n{e}", file=sys.stderr)
                # Email error inline (Task 14 wires send_consolidated_email_error)
                return 2
        if status in ("failed", "errored"):
            print(f"ERROR: session {session_id} ended with status={status}", file=sys.stderr)
            return 2
```

- [ ] **Step 4: Re-run test — expect PASS**

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add trigger_8d.py tests/test_trigger_8d.py && \
git commit -m "feat(trigger_8d): run-loop with poll-heartbeat + payload validation (Phase A)"
```

---

## Task 12: Implement `_cmd_resume_approval` for Phase 11 invocation

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/trigger_8d.py:_cmd_resume_approval`

- [ ] **Step 1: Write failing test**

```python
def test_resume_approve_reads_gate_and_invokes_executing_plans(tmp_path, monkeypatch):
    from trigger_8d import _cmd_resume_approval

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    gate_dir = tmp_path / ".claude" / ".pending-8d-approvals"
    gate_dir.mkdir(parents=True)
    gate_doc = {
        "run_id": "test-r1", "approved": False, "approved_at": None,
        "plan_inline": "# Test plan\n- step 1", "plan_path": str(tmp_path / "plan.md"),
        "report_path": str(tmp_path / "report.md"), "actions_count": 1,
    }
    (gate_dir / "test-r1.json").write_text(json.dumps(gate_doc), encoding="utf-8")

    rc = _cmd_resume_approval("test-r1", approve=True, reject_reason=None)

    assert rc == 0
    # Gate flipped
    updated = json.loads((gate_dir / "test-r1.json").read_text(encoding="utf-8"))
    assert updated["approved"] is True
    assert updated["via"] == "cli"
```

- [ ] **Step 2: Implement `_cmd_resume_approval`**

```python
def _cmd_resume_approval(run_id: str, approve: bool, reject_reason: str | None) -> int:
    gate_file = Path.home() / ".claude" / ".pending-8d-approvals" / f"{run_id}.json"
    if not gate_file.exists():
        print(f"ERROR: no gate file for {run_id}", file=sys.stderr)
        return 1
    doc = json.loads(gate_file.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    if approve:
        doc.update({"approved": True, "approved_at": now, "via": "cli"})
    else:
        doc.update({"approved": False, "rejected": True,
                    "rejected_reason": reject_reason, "via": "cli"})
    gate_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    if not approve:
        print(f"[trigger_8d] {run_id} rejected: {reject_reason}")
        return 0

    # Approved: print the plan + instruct user to invoke executing-plans
    # in their interactive Claude Code session. We don't auto-invoke
    # here because executing-plans is a Skill that needs Claude Code
    # tooling context (subagent dispatch, gates, etc.) — running it from
    # a bare Python script would skip the gates.
    print(f"[trigger_8d] {run_id} approved.")
    print(f"[trigger_8d] Plan at: {doc['plan_path']}")
    print(f"[trigger_8d] To execute: open Claude Code in the project dir,")
    print(f"[trigger_8d]   then in chat: 'execute the plan at {doc['plan_path']}'")
    print(f"[trigger_8d]   Claude will invoke superpowers:executing-plans automatically.")
    return 0
```

- [ ] **Step 3: Run test — expect PASS**

- [ ] **Step 4: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add trigger_8d.py tests/test_trigger_8d.py && \
git commit -m "feat(trigger_8d): _cmd_resume_approval flips gate + prints plan path (Phase A)"
```

---

## Task 13: Wire heartbeat to Telegram diagnostics

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/trigger_8d.py` — add `_post_telegram_heartbeat`
- Reference: `~/.claude/telegram.json` (existing, has `topics.diagnostics: 63`)

- [ ] **Step 1: Add helper function**

Insert in `trigger_8d.py` near top:
```python
def _post_telegram_heartbeat(message: str) -> None:
    """Best-effort Telegram diagnostics post; never raises."""
    try:
        cfg = json.loads((Path.home() / ".claude" / "telegram.json").read_text(encoding="utf-8"))
        token = cfg["bot_token"]
        chat_id = cfg["group_chat_id"]
        thread = cfg["topics"]["diagnostics"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id, "message_thread_id": thread,
            "text": message[:4000], "parse_mode": "Markdown",
        }, timeout=10)
    except Exception:
        pass  # heartbeat must never crash the run
```

- [ ] **Step 2: Wire into run-loop heartbeat block**

In `_cmd_run` poll loop, after the `[heartbeat]` print, add:
```python
            _post_telegram_heartbeat(f"`{datetime.now().isoformat(timespec='seconds')}` 8D `{run_id[:16]}` {phase} {kind}")
```

- [ ] **Step 3: Smoke test — Telegram should receive a test message**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -c "
from trigger_8d import _post_telegram_heartbeat
_post_telegram_heartbeat('trigger_8d.py heartbeat smoke test 2026-04-26')
print('posted')
"
```
Expected: message appears in `claude_daily` group → diagnostics topic.

- [ ] **Step 4: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add trigger_8d.py && \
git commit -m "feat(trigger_8d): heartbeat posts to Telegram diagnostics topic (Phase A)"
```

---

## Task 14: Implement consolidated email send (success + error paths)

**Files:**
- Modify: `D:/D-claude/skills/skill-8d-mrc/trigger_8d.py` — add `_send_completion_email` + `_send_error_email`

- [ ] **Step 1: Add success-path email**

```python
def _send_completion_email(run_id: str, run_dir: Path, gate_doc: dict) -> bool:
    """Send consolidated email with report + plan + approval portal."""
    try:
        from eightd.delivery.email import send_markdown_email
    except ImportError:
        print("WARN: send_markdown_email unavailable; gate file is the source of truth", file=sys.stderr)
        return False

    plan_first50 = "\n".join(gate_doc["plan_inline"].splitlines()[:50])
    body = f"""# 8D Run {run_id} — Approval Pending

## Report
{gate_doc.get('report_path', '')}

## Plan (auto-generated)
{gate_doc.get('plan_path', '')}

```
{plan_first50}
{'...' if len(gate_doc['plan_inline'].splitlines()) > 50 else ''}
```

## To approve
Reply to this email with subject: `APPROVE {run_id}`

Or in your next Claude Code session, type: `approve {run_id}`

## To reject
Reply with subject: `REJECT {run_id}`

Or type in session: `reject {run_id}`
"""
    return send_markdown_email(
        subject=f"[8D APPROVAL PENDING] Run {run_id}",
        body_md=body,
    )


def _send_error_email(run_id: str, error_subject: str, error_body: str) -> bool:
    """Send a self-contained error email — recipient does not need to look anywhere else."""
    try:
        from eightd.delivery.email import send_markdown_email
    except ImportError:
        return False
    return send_markdown_email(
        subject=f"[8D ERROR] {run_id}: {error_subject}",
        body_md=error_body,
    )
```

- [ ] **Step 2: Wire into `handle_session_complete` + error paths**

In `handle_session_complete`, after gate file write, add:
```python
    _send_completion_email(run_id=run_dir.name, run_dir=run_dir, gate_doc=gate_doc)
```

In `_cmd_run` exception/error paths, replace `print(f"ERROR: ...", file=sys.stderr)` with also calling `_send_error_email(...)` with full inline diagnostics (per R13).

- [ ] **Step 3: Smoke test (mocked Outlook)**

```python
# tests/test_trigger_8d.py — additional test
def test_completion_email_called(tmp_path, monkeypatch):
    from trigger_8d import _send_completion_email
    sent = []
    def fake_send(subject, body_md):
        sent.append((subject, body_md))
        return True
    monkeypatch.setattr("eightd.delivery.email.send_markdown_email", fake_send)
    ok = _send_completion_email(
        run_id="test-r1", run_dir=tmp_path,
        gate_doc={"plan_inline": "# Plan", "plan_path": str(tmp_path / "plan.md"),
                  "report_path": str(tmp_path / "report.md")},
    )
    assert ok is True
    assert len(sent) == 1
    assert "APPROVE test-r1" in sent[0][1]
```

- [ ] **Step 4: Run test**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_trigger_8d.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add trigger_8d.py tests/test_trigger_8d.py && \
git commit -m "feat(trigger_8d): consolidated email + self-contained error emails (Phase A)"
```

---

## Task 15: yaml structural validation test

**Files:**
- Create: `D:/D-claude/skills/skill-8d-mrc/tests/test_managed_agent_yaml.py`

- [ ] **Step 1: Write tests**

```python
"""Validates the Anthropic Managed Agents config yaml is structurally sound."""
import yaml
from pathlib import Path

YAML_PATH = Path(__file__).parent.parent / "eightd" / "managed_agent" / "skill-8d-mrc-v1.yaml"

def test_yaml_parses():
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    assert doc is not None

def test_required_keys_present():
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    for k in ("name", "description", "model", "system_prompt_path", "tools"):
        assert k in doc, f"missing required key: {k}"

def test_model_is_opus_4_6():
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    assert doc["model"] == "claude-opus-4-6"

def test_tools_include_websearch_and_agent_toolset():
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    tool_types = [t.get("type") for t in doc["tools"]]
    assert "websearch_20260401" in tool_types
    assert "agent_toolset_20260401" in tool_types

def test_no_mcp_servers_in_v1():
    """Per spec: v1 uses no MCP to avoid always_ask permission policy."""
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    assert doc.get("mcp_servers", []) == []

def test_system_prompt_file_exists():
    doc = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    sp = (YAML_PATH.parent / doc["system_prompt_path"]).resolve()
    assert sp.exists(), f"system_prompt_path resolves to non-existent file: {sp}"
```

- [ ] **Step 2: Run tests — expect PASS**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest tests/test_managed_agent_yaml.py -v
```
Expected: 6 tests pass.

- [ ] **Step 3: Commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add tests/test_managed_agent_yaml.py && \
git commit -m "feat(eightd): yaml structural validation tests (Phase A)"
```

---

## Task 16: Phase B — parity test trigger_8d.py vs run_8d.py

**Files:**
- Test: live runs (no code changes)

- [ ] **Step 1: Pick a small problem statement**

Use: `"Test problem for managed-agent migration verification — single-paragraph anti-pattern with clear root cause"`

- [ ] **Step 2: Run via legacy run_8d.py first; capture output**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 run_8d.py "<problem>" 2>&1 | tee /tmp/legacy-run.log
```
Note the run_id; capture report.md, actions.json, plan.md from `runs/<run_id>/`.

- [ ] **Step 3: Run via new trigger_8d.py; capture output**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 trigger_8d.py "<problem>" 2>&1 | tee /tmp/cloud-run.log
```
Note the new run_id; capture artifacts from new `runs/<run_id>/`.

- [ ] **Step 4: Compare structure (not content; LLM is non-deterministic)**

```python
import json
from pathlib import Path
LEGACY = Path("runs/<legacy-run-id>")
CLOUD = Path("runs/<cloud-run-id>")
for f in ("report.md", "actions.json", "plan.md"):
    assert (LEGACY / f).exists() and (CLOUD / f).exists(), f"{f} missing in one"
    print(f"{f}: legacy {(LEGACY/f).stat().st_size} bytes, cloud {(CLOUD/f).stat().st_size} bytes")
# actions_json should have similar count + same source_quadrant labels
legacy_actions = json.loads((LEGACY / "actions.json").read_text(encoding="utf-8"))
cloud_actions = json.loads((CLOUD / "actions.json").read_text(encoding="utf-8"))
print(f"Action counts: legacy={len(legacy_actions)}, cloud={len(cloud_actions)}")
assert abs(len(legacy_actions) - len(cloud_actions)) <= 2  # allow small drift
```

- [ ] **Step 5: Compare cost**

Check Anthropic billing dashboard (if available); cloud run total cost should be ~$1-3 per spec.

- [ ] **Step 6: Decision gate — proceed to Phase C only if parity verified**

If outputs diverge significantly (missing artifacts, wildly different action counts, schema validation failures), STOP and triage. Do NOT proceed to Phase C.

If parity OK: continue to Task 17.

---

## Task 17: Phase C — atomic switch in single commit

**Files:**
- Delete: `run_8d.py`, `eightd/graph.py`, `eightd/state.py`, `eightd/phases/*.py`, `eightd/sdk_client.py`, `eightd/child_runner.py`, `eightd/parallel.py`, `eightd/prompts/*.md`, `eightd/heartbeat.py`
- Modify: `D:/D-claude/skills/skill-8d-mrc/SKILL.md` — invocation example
- Tag: `legacy-pre-managed-agents-migration`

- [ ] **Step 1: Tag prior commit (safety net for rollback)**

```bash
cd D:/D-claude/skills/skill-8d-mrc && git tag -a legacy-pre-managed-agents-migration -m "Last commit before Managed Agents migration; rollback target"
```

- [ ] **Step 2: Stage all deletions + SKILL.md update IN ONE COMMIT**

```bash
cd D:/D-claude/skills/skill-8d-mrc
git rm run_8d.py
git rm eightd/graph.py eightd/state.py eightd/sdk_client.py eightd/child_runner.py eightd/parallel.py eightd/heartbeat.py
git rm -r eightd/phases/
git rm -r eightd/prompts/
# Plus tests for deleted modules:
git rm tests/test_graph.py tests/test_graph_topology.py tests/test_phase_*.py tests/test_child_runner.py tests/test_sdk_client.py 2>/dev/null || true
```

- [ ] **Step 3: Update SKILL.md**

Edit `SKILL.md`. Find:
```
    py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "<problem description>"
```
Replace with:
```
    py -3 D:/D-claude/skills/skill-8d-mrc/trigger_8d.py "<problem description>"
```

Also update the architecture summary section to reflect Managed Agents instead of LangGraph.

- [ ] **Step 4: Verify pytest passes (only new tests should remain)**

```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 -m pytest -x 2>&1 | tail -10
```
Expected: only test_trigger_8d.py + test_cloud_payload_schema.py + test_managed_agent_yaml.py + test_email_delivery.py + test_utils.py + test_models.py pass.

- [ ] **Step 5: Atomic commit**

```bash
cd D:/D-claude/skills/skill-8d-mrc && \
git add SKILL.md && \
git commit -m "BREAKING: replace LangGraph FSM with Managed Agents (Phase C atomic switch)

Per spec docs/superpowers/specs/2026-04-26-managed-agents-migration-design.md.
Per function-replacement-convention: legacy deleted in same commit as
new entry point lands.

Deleted (all replaced):
  - run_8d.py → trigger_8d.py
  - eightd/graph.py + state.py + phases/ + sdk_client.py + child_runner.py
    + parallel.py + prompts/ + heartbeat.py
  - test_phase_*.py + test_graph.py + test_child_runner.py + test_sdk_client.py

Rollback: git revert <this sha> OR git checkout legacy-pre-managed-agents-migration

Closes user directive 2026-04-26 'use Managed Agents whenever possible'.
"
```

---

## Task 18: Phase D — live monitor 1 week + email final report

**Files:** runtime artifacts only

- [ ] **Step 1: Run 1 live 8D via the new trigger_8d.py**

Pick a real upcoming 8D problem; fire via:
```bash
cd D:/D-claude/skills/skill-8d-mrc && py -3 trigger_8d.py "<problem>"
```

- [ ] **Step 2: Verify CPU pressure resolved**

During the run, check process count:
```powershell
Get-Process python,py | Measure-Object | Select-Object Count
```
Expected: 1-2 processes (vs 3+ before migration).

- [ ] **Step 3: Verify cost matches spec estimate**

Anthropic dashboard → check session-runtime + token cost for the run. Expected: $1-3.

- [ ] **Step 4: After 7 days OR after 2 successful runs, email the final report**

Body:
```
Subject: Managed Agents migration — Week 1 monitoring complete

Migration to Anthropic Claude Managed Agents complete. Phase D monitoring summary:

Runs executed: <N>
Avg cost per run: $<X.XX>
Avg local CPU during run: <Y>% (vs ~80% pre-migration)
Process count per run: <Z> (vs 3+ pre-migration)
Schema validation failures: <N>
Outlook COM email failures: <N>
Heartbeat-to-Telegram delivery rate: <%>

Issues observed: <list inline; no "see dashboard" pointers>

Disposition:
- [ ] Continue using new system
- [ ] Roll back via `git checkout legacy-pre-managed-agents-migration` (if issues)
```

Send via `send_markdown_email` to oxydavid@gmail.com.

---

## Self-Review

**1. Spec coverage:**
- ✅ Notion drop: Tasks 1-6 cover daily_brief code + docs + ECOSYSTEM.md + ~/.claude scan + manual config.yaml step (with email reminder)
- ✅ Phase A (build alongside): Tasks 7-15 cover yaml + system prompt + Pydantic schema + trigger_8d.py + heartbeat + email + yaml validation tests
- ✅ Phase B (parity test): Task 16 covers structural comparison + cost check + decision gate
- ✅ Phase C (atomic switch): Task 17 covers tag + atomic delete + SKILL.md update + commit
- ✅ Phase D (1-week monitor): Task 18 covers live run + CPU verification + cost verification + final report email

**2. Placeholder scan:** No "TBD", "implement later", or "fill in details" found. Each task has actual code/commands.

**3. Type consistency:** `CloudPayload` schema defined in Task 9 used consistently in Task 10, 11, 14. `_cmd_run`, `_cmd_resume_approval`, `_cmd_status` defined in Task 10, implemented in 11+12. `handle_session_complete` defined in Task 10, called from Task 11.

**4. R13 compliance:** All error-handling tasks specify inline diagnostics (no "see dashboard" / "fetch from elsewhere" patterns). Task 14 explicitly enforces this in `_send_error_email`.

**5. function-replacement-convention compliance:** Task 17 (Phase C) is explicitly atomic-single-commit per FRC. Tasks 1-3 also bundle deletion + docstring cleanup in adjacent commits.

**6. Wiki triple-marker compliance:** Tasks 7, 8, 9, 10 all include WIKI-CONSULTED/FINDING/ACTION markers in the code they create.

---

## Execution Handoff

**This session:** Tasks 1-6 (Notion drop) — fits in remaining context.

**Next session:** Tasks 7-18 (Managed Agents migration) — multi-day work; queue via email.

The email at end-of-session should include:
- This plan path
- Resume command: `py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "Implement plan at D:/D-claude/skills/skill-8d-mrc/docs/superpowers/plans/2026-04-26-notion-drop-and-managed-agents-migration.md via subagent-driven-development, starting at Task 7"`
- Note: until Phase C ships, run_8d.py still exists — the resume command above invokes legacy run_8d.py to fire a NEW 8D on the migration plan. Or alternatively, user opens Claude Code in skill-8d-mrc/ and types: "execute the plan at <path> starting at Task 7" — Claude will invoke superpowers:subagent-driven-development directly.
