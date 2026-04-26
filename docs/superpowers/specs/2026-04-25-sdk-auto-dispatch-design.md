# SDK Auto-Dispatch Design — skill-8d-mrc Phase 8-11

**Date:** 2026-04-25
**Status:** brainstorm → spec
**Source:** ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) escape #3 (backend→frontend handoff gap); user directive 2026-04-25 ("collects all action from 8d report, super power write plan, send email, ask for permission for execution. all should be in lang graph").

## Wiki consultation (per R6 + wiki-to-code-traceability convention)

- **WIKI-CONSULTED:** `concepts/function-replacement-convention.md` — when the new SDK-dispatch path supersedes the prior human-as-courier path (escape #3), the prior path's "natural language ask in email" should NOT coexist as a fallback that quietly defeats the closed loop. WIKI-FINDING: "later means never" — coexistence creates dual-function silent failure. WIKI-ACTION: phase_10's email body is REDESIGNED (not added alongside the old report email) — the old "report-only" email is replaced; this spec's email IS the report email + plan + portal, single emission.
- **WIKI-CONSULTED:** `concepts/silent-staleness.md` — gate file mtime-based "staleness" is the misleading-metadata trap. WIKI-FINDING: freshness must derive from content, not from `datetime.now()`. WIKI-ACTION: gate file's `created_at` is recorded but NOT used as a freshness signal; phase_11 validates `approved: true` content directly. The 30-day run_dir gc derives staleness from `final_state.phase_7_complete_ts`, not from filesystem mtime.
- **WIKI-CONSULTED:** `concepts/claude-agent-sdk-patterns.md` — Issue #573 + StructuredOutput contract. WIKI-FINDING: nested-session detection rejects child SDK if `CLAUDECODE` inherited; subprocess.Popen is the right escape hatch. WIKI-ACTION: `eightd/child_runner.py` pops `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` before importing claude_agent_sdk; phase_9/phase_11 also strip these from Popen env (defense-in-depth).
- **WIKI-CONSULTED:** `concepts/anthropic-oauth-policy-2026.md` — only Claude Code / claude CLI / Agent SDK / MCP-from-Claude-Code use Max sub post-2026-04-04. WIKI-FINDING: claude_agent_sdk path IS whitelisted; subprocess→bare-API-key is NOT. WIKI-ACTION: child_runner.py exclusively uses `claude_agent_sdk.query()`; no fallback to `anthropic.Anthropic()` direct API.

## Research informing this design (external)

- **LangGraph native human-in-the-loop pattern (2026 docs):** `interrupt(data)` is a function call INSIDE a node that pauses execution; resume is `graph.invoke(Command(resume=value), config)` which feeds `value` back as the return of `interrupt()`. State is automatically persisted via the configured checkpointer.
- **Claude Agent SDK Issue #573 (Feb 2026):** SDK subprocess inherits `CLAUDECODE=1` from parent process; spawned CLI rejects the session as nested. Mitigation: pop `CLAUDECODE` from env before spawning child.

## Goal

Close the 8D backend→frontend gap (escape #3) by extending the LangGraph FSM with three new phases and one native `interrupt()` call: auto-collect Phase 4 actions, invoke `superpowers:writing-plans` via SDK to produce a plan artifact, emit a single approval gate with two equivalent access portals (email + active Claude session), and on approval invoke `superpowers:executing-plans` via SDK. Both portals surface identical content and write to the same gate file.

## Non-goals

- Per-batch approval inside `executing-plans` execution
- HTTP server / web dashboard for approval
- Telegram inline-button portal (deferred Portal C)
- Plan revision loop pre-approval (user edits `plan.md` directly)
- Replacing the existing `--resume <run_id>` CLI flag (extends with `--approve`)

## Constraints

1. **Hook recursion** — child SDK starts cold; without mitigation hits R1-R13 from clean slate.
2. **Concurrency / nested-session crash** — Issue #573: must clear CLAUDECODE.
3. **Trust / blast-radius** — autonomous code modifications without review violate R12 + never-handoff.
4. **OAuth split** — must use `claude_agent_sdk` (Max-whitelisted post-2026-04-04).
5. **Observability** — child runs detached from user terminal; needs heartbeat surfacing.

## Architecture

### LangGraph node additions

```
phase_7_report                (existing — emails report; will be MODIFIED to defer
                                          email until phase_10 to avoid dual emission
                                          per function-replacement-convention)
  → phase_8_collect_actions   (NEW — pure-Python action extraction)
  → phase_9_write_plan        (NEW — SDK dispatch → superpowers:writing-plans)
  → phase_10_emit_and_wait    (NEW — emits gate + single email containing report+plan,
                                     then calls interrupt())
  → phase_11_execute          (NEW — runs after Command(resume=...) → SDK dispatch
                                       → superpowers:executing-plans)
  → END
```

`phase_10_emit_and_wait` is a single node. The `interrupt()` is a function call WITHIN that node, not a structural edge. After `interrupt()` returns (on resume), the same node finishes and the graph transitions to `phase_11_execute`. Matches LangGraph's documented pattern.

**Critical (function-replacement-convention):** phase_7's email-send is REMOVED in this design — phase_10 sends the SINGLE consolidated email (report + plan + approval portal). Leaving phase_7's email in place would create dual-emission and silently defeat the closed loop. Phase_7 retains report rendering; only the email-send is migrated to phase_10.

### Components

| File | Type | Responsibility |
|---|---|---|
| `eightd/phases/phase_7_report.py` | Modify | REMOVE email-send call; keep report rendering. Email-send migrated to phase_10. |
| `eightd/phases/phase_8_collect_actions.py` | NEW Pure-Python | Walk `final_state` → extract Section B (Corrective 4Q), B2 (Prevention 4Q), Phase 6 verification → normalized JSON `[{title, description, files_touched, owner, priority, source_quadrant}]`. Output: `runs/<run_id>/actions.json`. |
| `eightd/phases/phase_9_write_plan.py` | NEW SDK dispatch | Spawns child via `subprocess.Popen` running `eightd/child_runner.py`. Child invokes `claude_agent_sdk.query()` with system prompt = "Invoke superpowers:writing-plans on actions at <path>". Tool surface: `Read,Glob,Grep,Write(only runs/<run_id>/plan.md),WebSearch`. Output: `runs/<run_id>/plan.md`. |
| `eightd/phases/phase_10_emit_and_wait.py` | NEW I/O + interrupt | Writes plan, gate file `~/.claude/.pending-8d-approvals/<run_id>.json`, sends consolidated email (report + plan + approval portal). Then calls `interrupt({"approval_pending": True, "gate_path": ..., "plan_path": ...})`. On resume, receives approval payload. |
| `eightd/phases/phase_11_execute.py` | NEW SDK dispatch | Spawns child via `subprocess.Popen` running `eightd/child_runner.py --mode execute`. Tool surface: `Read,Glob,Grep,Write,Edit,Bash,WebSearch`. Heartbeat to `runs/<run_id>/child/progress.jsonl`. |
| `eightd/child_runner.py` | NEW module | Process entry-point for SDK child. Pops `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` from env before importing claude_agent_sdk. Modes: `--mode plan` or `--mode execute`. |
| `eightd/graph.py` | Modify | Add 4 nodes; edges phase_7→phase_8→phase_9→phase_10→phase_11→END. |
| `eightd/delivery/email.py` | Modify | Add `send_consolidated_email(report_path, plan_path, run_id, mailto_url)`. |
| `run_8d.py` | Modify | Add `--approve` / `--reject <reason>` / `--status` flags. On `--resume --approve`: `graph.invoke(Command(resume={"approved": True, "via": "cli"}), config)`. |
| `~/.claude/.pending-8d-approvals/` | NEW directory | Single source of truth for pending approval state. |
| `~/.claude/hooks/sessionstart-8d-approval-banner.sh` | NEW hook | (a) Inject banner with plan content for `{approved: false}` entries. (b) Background-shell `py -3 run_8d.py --resume <id> --approve` for `{approved: true}` entries; on success delete entry. |
| `~/.claude/hooks/userpromptsubmit-8d-approval-detect.sh` | NEW hook | Detect `approve <run_id>` / `reject <run_id>` (case-insensitive) → flip gate JSON. |
| `~/.claude/bin/outlook-approval-poller.py` | NEW tool | Reuses daily_brief Outlook COM pattern. Scans inbox for `APPROVE <run_id>` reply subjects → flips matching gate. |
| Windows Task Scheduler `ClaudeApprovalPoller` | NEW schtasks entry | Every 10 min, runs outlook-approval-poller.py. |

### Data flow

```
[parent FSM]                                [user]                     [child process]
phase_7 → renders report (no email)
phase_8 → actions.json
phase_9 → Popen(env without CLAUDECODE) ──→ claude_agent_sdk → writing-plans
                          ←─── plan.md ────────
phase_10 → writes gate file (plan inline)
        → sends CONSOLIDATED email (report + plan + mailto: portal)
        → interrupt({approval_pending: True, ...})
        # graph.invoke returns; run_8d.py exits 0

[Portal A — Email]                                [Portal B — Claude session]
clicks mailto: APPROVE <run_id>                  sees SessionStart banner with plan
sends reply                                      types "approve <run_id>"
ClaudeApprovalPoller (10 min)                    UserPromptSubmit hook detects
detects subject → flips gate JSON                → flips gate JSON
                       \                                /
                         → gate file: {approved: true} ←
                                       │
SessionStart-8d-approval-banner.sh next session boot
detects approved → background-shells:
  py -3 run_8d.py --resume <id> --approve
                                       │
[parent FSM resumes via Command(resume={...})]
phase_10's interrupt() returns approval payload
phase_11 → Popen(env without CLAUDECODE) ──→ claude_agent_sdk → executing-plans
                          ←─── execution complete ────
END → cleanup: delete gate file
```

### Gate file schema

```json
{
  "run_id": "run-1234567890-deadbeef",
  "created_at": "2026-04-25T16:30:00Z",
  "report_path": "...",
  "plan_path": "runs/<run_id>/plan.md",
  "plan_inline": "<full plan markdown>",
  "actions_count": 12,
  "approved": false,
  "approved_at": null,
  "via": null,
  "rejected": false,
  "rejected_reason": null
}
```

On approval: `{approved: true, approved_at: ..., via: "email"|"session"|"cli"}`.
On rejection: `{rejected: true, rejected_reason: ..., via: ...}` — phase_11 skipped, gate file kept for audit.

**Per silent-staleness wiki:** `created_at` is recorded for audit only, NOT as freshness signal. Phase_11 trusts `approved: true` content directly; staleness derivation comes from `final_state.phase_7_complete_ts` (data-derived, not metadata).

### Hook recursion mitigation

Child SDK initial prompt prepends:

```
EXEMPT R1 R2 R3 R4 R5 R9 child-of-8d: SDK-dispatched child session executing
approved plan from 8D run <run_id>. Parent ran the full pipeline; child only
implements the approved plan. Bypassing pipeline-START gates here is correct.
```

R6, R7, R8, R11, R12, R13 remain active in child.

### Concurrency / nested-session mitigation (Issue #573)

`eightd/child_runner.py` first lines:

```python
import os
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)
```

`phase_9_write_plan.py` and `phase_11_execute.py` both call `subprocess.Popen([...], env={k:v for k,v in os.environ.items() if k != "CLAUDECODE"})` for defense-in-depth.

### Observability

- Child writes to `runs/<run_id>/child/<phase_id>/progress.jsonl`.
- Child reuses `eightd/heartbeat.py`.
- Both append to `~/.claude/metrics.jsonl`.

### Email portal mailto template

```
mailto:<user_email>?subject=APPROVE%20<run_id>
```

Email body: report summary + plan summary (first 50 lines) + APPROVE/REJECT mailto buttons + fallback "Or in your next Claude Code session, type `approve <run_id>` or `reject <run_id>`."

### SessionStart banner template

```
[8D APPROVAL PENDING — run <run_id>]

Report: <report_path>
Plan:   <plan_path>

—— Plan summary (first 50 lines) ——
<inline>

—— To approve ——
Reply with: approve <run_id>

—— To reject ——
Reply with: reject <run_id>

—— Or via email ——
Click the APPROVE button in the 8D report email already in your inbox.
```

### Resume + approve flow

```bash
py -3 run_8d.py --resume <run_id>                       # picks up at last interrupted phase
py -3 run_8d.py --resume <run_id> --approve             # passes Command(resume={"approved": True})
py -3 run_8d.py --resume <run_id> --reject "<reason>"   # passes Command(resume={"rejected": True, ...})
py -3 run_8d.py --resume <run_id> --status              # shows pending-approval state without resuming
```

`--approve` validates the gate file shows `{approved: true}` before passing the resume Command.

## Error handling

| Failure | Handling |
|---|---|
| phase_8 finds no actions | Skip phase_9-11; email "no actions in Phase 4 — nothing to dispatch"; END. |
| phase_9 child Popen exits non-zero | Retry 1×; on second failure email "plan generation failed: <reason>"; END. |
| phase_10 email send fails | Gate file still written; Portal B can still surface it. |
| phase_11 child fails mid-execution | Heartbeat surfaces failure. `--resume --approve` is idempotent via checkpoint. |
| Multiple pending approvals | SessionStart banner lists all; user approves one at a time. |
| Approval after run_dir deleted (>30d gc) | Gate file's `plan_inline` is self-contained; phase_11 reads from gate file. |
| Outlook poller misses email | Portal B still works. |
| `CLAUDECODE` mitigation fails | Child Popen exits with detectable error; parent emails fallback. |

## Testing strategy

- **Unit:** `phase_8_collect_actions` against 3 fixture `final_state` dicts.
- **Unit:** gate-file schema validator (jsonschema).
- **Unit:** `child_runner.py` env-cleanup verification.
- **Integration:** `--dry-run` for phase_9 / phase_11.
- **Integration:** synthetic gate-file-write + Portal B simulation.
- **E2E:** trivial 8D run → all 4 new phases complete + gate file appears + email sends + SessionStart banner appears.
- **Hook unit:** `sessionstart-8d-approval-banner.sh` against synthetic gate dir.

## Open issues / residuals

- **Outlook poller Windows-only** — acceptable; macOS would lose Portal A but keep Portal B.
- **Race: dual-portal simultaneous approval** — last-writer-wins; phase_11 idempotent via checkpoint.
- **Plan markdown longer than reasonable email body** — email contains summary + link; full plan in gate file.
- **Child encounters its own approval-needed scenarios** — out of scope for v1.
- **Issue #573 may evolve** — mitigation lives in one file (`child_runner.py`) for easy extension.

## Out-of-scope deferrals

- Telegram inline-button portal (Portal C)
- Per-batch approval inside child execution
- In-portal plan editing UI
- Multiple concurrent 8D runs sharing approval state
- Auto-cleanup of stale gate files (>30d unanswered)

## Owner

skill-8d-mrc maintainer (kuangyu).

## Source

- Ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) escape #3
- Brainstorm session 2026-04-25 (this document)
- Wiki consultations 2026-04-25: function-replacement-convention, silent-staleness, claude-agent-sdk-patterns, anthropic-oauth-policy-2026
- Research 2026-04-25:
  - LangChain docs — Human-in-the-Loop interrupt/resume pattern
  - GitHub anthropics/claude-agent-sdk-python Issue #573 — CLAUDECODE inheritance
- User directives: "everything. go.", "collects all action from 8d report, super power write plan, send email, ask for permission for execution. all should be in lang graph", "either email click ok or session review plan and reply ok... just a different access portal" (dual portal)
