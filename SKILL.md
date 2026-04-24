---
name: skill-8d-mrc
description: Use when debugging recurring problems, doing post-mortem analysis, or when a fix didn't prevent recurrence. Triggers on root cause analysis, 8D, post-mortem, why did this happen again, non-conformance, escape analysis, prevention action, corrective action, proof of action. LangGraph FSM-driven — Phase 0 (dual-tier research), Phase 3/5/7 SoA audits, three 4-quadrant matrices (Root Cause + Corrective + Proof of Action), email delivery.
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
