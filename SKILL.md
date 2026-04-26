---
name: skill-8d-mrc
# WIKI-EXEMPT: backfill execution_mode per surface-acceptance charter — no wiki-governed pattern
description: Use when debugging recurring problems, doing post-mortem analysis, or when a fix didn't prevent recurrence. Triggers on root cause analysis, 8D, post-mortem, why did this happen again, non-conformance, escape analysis, prevention action, corrective action, proof of action. LangGraph FSM-driven — Phase 0 (dual-tier research), Phase 3/5/7 SoA audits, three 4-quadrant matrices (Root Cause + Corrective + Proof of Action), email delivery.
execution_mode: both
---

# 8D MRC — LangGraph-driven

This skill runs a FSM-enforced 8D root cause analysis. Phase order and exit
criteria are enforced by Python code, not markdown.

## Invocation

When the user asks for 8D analysis, execute via Bash:

    py -3 D:/D-claude/skills/skill-8d-mrc/run_8d.py "<problem description>"

Optional flags:
    --resume <run_id>     Resume an interrupted run
    --gc                  Clean runs older than 30 days
    --dry-run             Plan only; do not call Anthropic API

## What the user gets

On success, `run_8d.py` prints the path to the final report on stdout.
The report is saved at a canonical project location (default:
`D:/D-claude/skills/skill-8d-mrc/docs/8d-reports/` — reports live in the
skill's own repo since that's the producer of these artifacts;
overridable via `CLAUDE_EIGHTD_REPORTS_DIR` env var). The report is also
emailed to the user via Outlook COM (configured in `~/.claude/email.json`).

Summarize the report for the user. Do not attempt to run phases manually —
the Python FSM is the only correct implementation.

## MANDATORY post-completion handoff (foreground execution)

**The 8D run produces design; it does NOT implement that design.** When
`run_8d.py` exits successfully (Phase 7 complete, report emitted, email
sent), the orchestrator (this Claude Code session) MUST continue with
foreground implementation of the report's Phase 4 corrective + prevention
actions. Do NOT mark the user's task done at email-send.

Required sequence:

1. **Read** the emitted report at the printed path. Focus on Section B
   (Corrective Actions Matrix) and Section B2 (Prevention Actions Matrix).
2. **Invoke `superpowers:executing-plans`** with the report as the plan
   source. The 8D's Phase 4 IS the plan — no separate `writing-plans`
   step is needed (the design exists). Pass the report path and the
   specific quadrants to be implemented.
3. **executing-plans** internally dispatches to `subagent-driven-
   development` for any non-trivial implementation work, ensuring R4
   (process-skip on code Write) fires correctly when subagents touch
   code files.
4. **Verify** via `superpowers:verification-before-completion` before
   reporting the task done. Per `~/.claude/feedback_never_handoff.md`:
   no completion claim without test evidence.

**Why this split:**
- skill-8d-mrc is the BACKEND — LangGraph FSM, structured phases,
  4-quadrant matrices, can run in background (`run_in_background:true`).
- `superpowers:executing-plans` is the FRONTEND — foreground human-
  visible implementation with proper pipeline gates (R4 enforces the
  pipeline; the heartbeat surfaces progress).
- Backend produces design; frontend implements. Skipping the frontend
  hand-off is the meta-recurrence of degraded-emission-with-warning
  (the 8D report ships, but the prevention items never land in code).

**Bypass:** include `EXEMPT post-8d-execution: <reason>` in the prompt
that triggered the 8D, OR explicitly state "the 8D is for design
inspection only, no implementation needed." Without an EXEMPT, marking
the task done after email-send is a R12 verification-evidence violation.

**Persisted as known-failed receipt:** `~/.claude/feedback_skill_progress_reporting.md`
companion entry; future sessions will see this rule via CLAUDE.md @import
and skill-rules.json `execute-prevention-actions` keyword trigger.

## Architecture (summary)

- Python package `eightd/` with LangGraph StateGraph
- Phase 0: Python-forced dual-tier research (problem-specific + meta/cross-domain)
- Phase 1: IS/IS NOT
- Phase 2: Why analysis, ≥10 whys per quadrant (structural enforcement)
- Phase 3: SoA research + RC audit (must cite ≥2 SoA URLs)
- Phase 4: Corrective + Prevention actions, 4 quadrants each
- Phase 5: SoA research + Prevention audit (must cite ≥2 SoA URLs)
- Phase 6: Verification plan + Proof of Action 4-quadrant matrix
- Phase 7: SoA research + Report render + Closure audit + Email delivery

Report contains THREE 4-quadrant matrices: Root Cause, Corrective Actions, Proof of Action.

## Config

`~/.claude/email.json`:
```json
{
  "recipient": "you@example.com",
  "enabled": true
}
```

## Legacy markdown

The original markdown skill (Phase 0-8 instructions for Claude to read and
follow) is at `SKILL.md.backup-20260420` for reference. Do not follow its
instructions manually — use `run_8d.py`.
