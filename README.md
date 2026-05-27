# skill-8d-mrc

<!-- WIKI-CONSULTED: wiki-to-code-traceability, silent-staleness, function-replacement-convention -->
<!-- WIKI-FINDING: README is documentation surface, not behavioral code; triple-marker convention applies to code in wiki-governed domains, not narrative README sections. Silent-staleness concern: README must describe the *current* state of the skill so that staleness is visible to readers. -->
<!-- WIKI-ACTION: README content authored from current SKILL.md + repo layout snapshot 2026-05-27; phase count, file list, and dependency list cross-checked against eightd/phases/, requirements.txt, and Makefile to avoid silent-staleness. -->

**LangGraph FSM-driven 8D Root Cause Analysis skill for Claude Code.**

Run a disciplined, structurally-enforced 8D (Eight Disciplines) post-mortem on
any recurring problem and get back a 3-matrix report (Root Cause / Corrective
Actions / Proof of Action) — delivered as Markdown + email, with foreground
implementation of the prevention actions wired into the Superpowers pipeline.

> 8D ("Eight Disciplines of Problem Solving") is an automotive-industry
> standard for permanently eliminating recurring defects. This skill mechanizes
> the discipline: phase order, exit criteria, audits, and proof-of-action are
> enforced by Python code, not by an LLM following a checklist.

---

## Why this skill exists

A normal LLM "post-mortem" tends to produce a plausible-looking write-up that
**doesn't actually prevent recurrence**:

- Root cause is asserted, not audited against state-of-the-art literature.
- "Corrective action" lists are aspirational — there's no proof that the
  action was implemented, only a sentence saying it should be.
- Prevention vs. correction vs. containment all get muddled into one bucket.
- The same bug class returns 2 weeks later because no structural barrier was
  built.

This skill addresses each failure mode with a hard structural gate:

| Failure mode in ad-hoc post-mortems     | Structural defense in skill-8d-mrc                               |
|-----------------------------------------|------------------------------------------------------------------|
| Skip "why" depth, jump to action        | Phase 2 requires **≥10 whys per quadrant** (Pydantic-enforced)    |
| Root cause = first plausible guess      | Phase 3 audit requires **≥2 state-of-the-art URLs** cited         |
| Prevention = "we'll be more careful"    | Phase 4 forces a 4-quadrant matrix (process / training / system / tooling) |
| Action ships but isn't verified         | Phase 6 Proof-of-Action 4-quadrant matrix (detection / metric / owner / cadence) |
| Report writes, report forgotten         | Phase 11 hands off to `superpowers:executing-plans` for foreground implementation |
| 8D runs in background, status invisible | Built-in heartbeat with per-phase ETA + next-phase + stall detection |

---

## What you get

A single `py -3 run_8d.py "<problem>"` invocation produces:

1. **A 12-phase forensic walk** through the problem, executed by a LangGraph
   `StateGraph` with SQLite checkpointing (resumable on crash).
2. **A Markdown report** containing three 4-quadrant matrices:
   - **Root Cause Matrix** — why-chains × people / process / technology / environment
   - **Corrective Actions Matrix** — containment / corrective / preventive / systemic
   - **Proof-of-Action Matrix** — detection mechanism / metric / owner / cadence
3. **An email delivery** of the report via Outlook COM (Win32).
4. **A handoff** into `superpowers:executing-plans` so the prevention actions
   actually land in code, not just on paper.

---

## Architecture (the 12 phases)

```
Phase 0  ─ Dual-tier research (problem-specific + meta/cross-domain WebSearch)
Phase 1  ─ IS / IS-NOT scoping
Phase 2  ─ Why analysis  (≥10 whys × 4 quadrants, structural enforcement)
Phase 3  ─ SoA research + Root-cause audit (≥2 SoA URLs cited)
Phase 4  ─ Corrective + Prevention actions (4-quadrant matrix)
Phase 5  ─ SoA research + Prevention audit (≥2 SoA URLs cited)
Phase 6  ─ Verification plan + Proof-of-Action 4-quadrant matrix
Phase 7  ─ SoA research + Report render + Closure audit + Email delivery
Phase 8  ─ Collect concrete follow-up actions from the report
Phase 9  ─ Write implementation plan (writing-plans-equivalent)
Phase 10 ─ Emit + wait (gate JSON, banner, approve-hook)
Phase 11 ─ Hand off to superpowers:executing-plans for foreground implementation
```

Each phase is a node in a LangGraph `StateGraph`. Edges are conditional —
phase N cannot start until phase N-1's exit criteria are met (e.g., Phase 3
will refuse to advance if fewer than 2 SoA URLs are present in state).

State is persisted to `runs/<run_id>/checkpoint.db` (SQLite) so a crash mid-run
is recoverable with `--resume <run_id>` — no need to re-run from Phase 0 and
burn the LLM compute again.

---

## Installation

```bash
git clone https://github.com/oxydavid-maxx/skill-8d-mrc.git
cd skill-8d-mrc
pip install -r requirements.txt
```

Symlink (or copy) into your Claude Code skills directory so Claude Code
auto-discovers it:

```powershell
# Windows (PowerShell, admin)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\skill-8d-mrc" -Target "<repo path>"
```

```bash
# macOS / Linux
ln -s "<repo path>" ~/.claude/skills/skill-8d-mrc
```

Configure email delivery at `~/.claude/email.json`:

```json
{
  "recipient": "you@example.com",
  "enabled": true
}
```

Set `ANTHROPIC_API_KEY` (or rely on the Claude Code subscription token if
running under Claude Code itself).

---

## Usage

### From Claude Code (recommended)

Just ask:

> *"Run an 8D on the recurring CI flake where pytest hangs after deps install."*

The skill auto-triggers on phrases like *root cause analysis, 8D, post-mortem,
why did this happen again, non-conformance, escape analysis, prevention
action, corrective action, proof of action.*

### Direct CLI

```bash
py -3 run_8d.py "<problem description>"
```

Optional flags:

| Flag                  | What it does                                                                |
|-----------------------|-----------------------------------------------------------------------------|
| `--resume <run_id>`   | Resume an interrupted run from its last successful phase                    |
| `--gc`                | Garbage-collect runs older than 30 days                                     |
| `--dry-run`           | Plan the FSM transitions without calling the Anthropic API                  |

### Output

On success, `run_8d.py` prints the path to the Markdown report on stdout. By
default reports live in:

```
docs/8d-reports/<run_id>-report.md
```

Override with `CLAUDE_EIGHTD_REPORTS_DIR`. The report is also emailed to the
recipient in `~/.claude/email.json` via Outlook COM (`pywin32`).

---

## Configuration

| File / env var                       | Purpose                                                              |
|--------------------------------------|----------------------------------------------------------------------|
| `~/.claude/email.json`               | Email recipient + enabled flag (Outlook COM delivery)                |
| `CLAUDE_EIGHTD_REPORTS_DIR`          | Override default report output directory                             |
| `ANTHROPIC_API_KEY`                  | API key for direct CLI runs (skip if using Claude Code subscription) |
| `runs/<run_id>/checkpoint.db`        | LangGraph SQLite checkpoint — used by `--resume`                     |
| `governance/audits/*.json`           | E2E closed-loop test traces (for the `audit-closed-loop` make target)|

---

## Repository layout

```
skill-8d-mrc/
├── SKILL.md                  # Skill manifest (Claude Code reads this)
├── run_8d.py                 # Main entrypoint — LangGraph FSM orchestrator
├── trigger_8d.py             # Cloud-session trigger (uses anthropic SDK)
├── generate_partial_report.py# Render a report from a partially-completed run
├── Makefile                  # `make test`, `make audit-closed-loop`
├── requirements.txt          # Python dependencies (langgraph, anthropic, ...)
│
├── eightd/                   # Python package — the FSM and phase logic
│   ├── graph.py              # LangGraph StateGraph wiring
│   ├── state.py              # Pydantic state schema (per-phase fields)
│   ├── models.py             # 4-quadrant matrix Pydantic models
│   ├── schemas.py            # JSON Schemas for gate contracts
│   ├── heartbeat.py          # Daemon thread, per-phase ETA + stall detection
│   ├── progress.py           # Heartbeat event log
│   ├── render.py             # Markdown report renderer
│   ├── validators.py         # Phase exit-criteria validators
│   ├── parallel.py           # asyncio.gather helpers for SoA research
│   ├── sdk_client.py         # Anthropic SDK wrapper (retry + timeout)
│   ├── child_runner.py       # Subprocess runner for managed agents
│   ├── errors.py             # Typed exception hierarchy
│   ├── utils.py
│   ├── phases/               # One file per FSM node (phase_0 … phase_11)
│   ├── prompts/              # Per-phase prompt templates
│   ├── delivery/             # Outlook COM email + banner emission
│   ├── managed_agent/        # YAML-driven managed-agent definitions
│   └── ...
│
├── tests/                    # pytest suite
│   ├── test_phase_*.py       # Per-phase unit tests
│   ├── test_heartbeat.py     # Heartbeat formatting + stall thresholds
│   ├── test_trigger_8d.py    # SDK client mocks
│   ├── e2e/
│   │   └── test_closed_loop_pipeline.py  # 8-test seam-contract harness
│   └── fixtures/
│
├── docs/
│   └── 8d-reports/           # Generated reports (gitignored)
│
├── runs/                     # Per-run checkpoint DBs (gitignored)
├── governance/audits/        # E2E test JSON traces
├── templates/                # Report Markdown templates
├── references/               # Reference docs (8D standard, etc.)
├── poc/                      # Proof-of-concept scripts
├── agents/                   # Sub-agent definitions
└── SKILL.md.backup-20260420  # Legacy markdown skill (do NOT follow manually)
```

---

## Development

Run the full test suite:

```bash
make test
# or: py -3 -m pytest tests/ -v
```

Run the closed-loop end-to-end harness (asserts all 11-layer seam contracts):

```bash
make audit-closed-loop
```

This produces `governance/audits/2026-04-26-closed-loop-e2e.json` — a
JSON trace of the contiguous seam-test sequence, used by the R17
integration-contract gate to confirm the pipeline is green.

---

## Key design decisions

- **LangGraph FSM, not markdown enforcement.** A previous markdown-only
  version reached ~84% phase-discipline compliance. The FSM is at 100%
  because the LLM physically cannot skip a node or transition before
  exit criteria are met.
- **Pydantic state.** All cross-phase data is typed; schema drift fails fast
  at the node boundary, not silently three phases later.
- **Selective reviewer.** A "devil's advocate" reviewer runs only when the
  problem is novel (Phase 0 classifier decides), keeping cost down.
- **Heartbeat by default.** A daemon thread aggregates phase events into a
  5-minute human-readable summary with per-phase ETA, in-flight LLM call
  duration, and the next-phase indicator — built-in so it cannot be
  forgotten.
- **Backend produces design; frontend implements.** Phase 11 hands off to
  `superpowers:executing-plans` because that's where R4 (process-skip on
  code Write) and the rest of the Superpowers pipeline gates live. If the
  8D shipped the report and stopped there, the prevention items would
  never land — this is the meta-recurrence the skill is built to prevent.

---

## License

MIT.

---

## Credits

Built on top of:

- [LangGraph](https://github.com/langchain-ai/langgraph) — stateful agent FSMs
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude API client
- [claude-agent-sdk](https://github.com/anthropics/claude-agent-sdk-python) — Claude Code session SDK
- 8D methodology — Ford Motor Company, *Team Oriented Problem Solving* (1987)
