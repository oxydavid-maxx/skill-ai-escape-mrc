# skill-ai-escape-mrc

<!-- WIKI-CONSULTED: wiki-to-code-traceability, silent-staleness, function-replacement-convention -->
<!-- WIKI-FINDING: README is a documentation surface, not behavioral code. Silent-staleness concern: README must describe the current state of the skill so staleness is visible. -->
<!-- WIKI-ACTION: README content authored from current SKILL.md + repo layout snapshot 2026-05-27; phase count, file list, and dependency list cross-checked against ai_escape_mrc/phases/, requirements.txt, and Makefile. -->

AI Escape MRC reviews AI harness and automation-flow escapes: cases where an
agent, CI job, browser/API automation, or review workflow reported completion
without proving that the resulting system was actually coherent.

Standalone distribution note: this is the non-discussion AI Escape MRC variant.
Paddy may maintain a separate discussion-oriented variant; keep that separate if
it is added later.

## Why This Skill Exists

AI automation can fail in a deceptively polished way. It can generate files,
push a review, update a README, and print a confident completion message while
still leaving one of the following gaps:

- A renamed entrypoint still has an old command path in docs or tests.
- A plugin link points at the wrong skill folder.
- Generated README membership differs from plugin membership.
- Runtime report names, delivery artifacts, managed-agent names, or env vars
  still use the old identity.
- Tests pass only on the old package name.
- A workflow says "done" without proof that artifacts, docs, tests, and runtime
  paths agree.

AI Escape MRC forces the review into a repeatable structure: research, IS/IS-NOT
scoping, four-quadrant TRC/MRC analysis, corrective and prevention matrices,
proof-of-action verification, report rendering, and final delivery.

## What You Get

A single invocation:

```powershell
py -3 run_ai_escape_mrc.py "<automation escape topic>"
```

produces:

1. A resumable LangGraph run with SQLite checkpointing under `runs/<run_id>/`.
2. Deterministic phase start, progress, summary, and error receipts printed to
   the active run output.
3. Persisted phase receipts under `runs/<run_id>/stage-summaries.md`,
   `stage-summaries.jsonl`, and `stage-progress.jsonl`.
4. A Markdown report under `docs/ai-escape-mrc-reports/`.
5. Corrective, prevention, and proof-of-action matrices.
6. A delivery status artifact under `runs/<run_id>/delivery-status.json`.
7. Optional Outlook email delivery to the requester, with operator CC.

## Architecture

```text
Phase 0  - Dual-tier research
Phase 1  - IS / IS-NOT scoping
Phase 2  - Why analysis across TRC/MRC and NC/ND quadrants
Phase 3  - Root-cause audit with evidence checks
Phase 4  - Corrective + prevention actions
Phase 5  - Prevention audit
Phase 6  - Verification plan + proof-of-action matrix
Phase 7  - Report render + closure audit
Phase 8  - Action collection
Phase 9  - Implementation plan generation
Phase 10 - Final report/plan delivery
```

Each phase is a node in a LangGraph `StateGraph`. The graph wrapper enforces a
runtime visibility contract: phase start, phase summary, and phase error
receipts are required deterministic outputs, and receipt failures fail closed
instead of being swallowed as optional logs.

## Installation

Clone the standalone repo:

```powershell
git clone https://github.com/oxydavid-maxx/skill-ai-escape-mrc.git D:/D-claude/skills/skill-ai-escape-mrc
```

Install it as a Claude skill by pointing the skill folder at the checkout:

```powershell
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\skill-ai-escape-mrc" -Target "D:\D-claude\skills\skill-ai-escape-mrc"
```

## Usage

From Claude Code, ask for an AI Escape MRC review, for example:

> Review the AI automation escape where the harness reported success after a
> review push, but did not verify renamed skill entrypoints, plugin links,
> generated README entries, tests, and runtime artifact names.

Direct CLI:

```powershell
py -3 run_ai_escape_mrc.py "<problem description>"
```

To send the final report/plan email to the real requester and CC the operator:

```powershell
py -3 run_ai_escape_mrc.py "<problem description>" --user-email user@example.com
```

For a Windows run that avoids opening a new black console window but still
streams the run output back to the current launcher, use:

```powershell
py -3 run_ai_escape_mrc_hidden.py "<problem description>" --user-email user@example.com
```

Use `--detach` only for true fire-and-forget background mode; detached runs
write summaries to the printed log files and `runs/<run_id>/stage-summaries.*`.

For Codex/Claude agent-mediated runs, use `--agent --watch` so the launcher
returns JSON metadata and streams the hidden child output back to the current
conversation:

```powershell
py -3 run_ai_escape_mrc_hidden.py --agent --watch "<problem description>" --user-email user@example.com
```

Detached agent runs are only for callers that already have a polling loop. In
that mode, the agent should poll `--status-json` and paste the returned
`human_summary` into the conversation:

```powershell
py -3 run_ai_escape_mrc_hidden.py --agent --detach "<problem description>" --user-email user@example.com
py -3 run_ai_escape_mrc.py --status-json "<run_dir from launcher JSON>"
```

Useful flags:

| Flag | Purpose |
| --- | --- |
| `--resume <run_id>` | Resume an interrupted run from its last checkpoint. |
| `--gc` | Garbage-collect runs older than 30 days. |
| `--dry-run` | Validate CLI discovery and planned run id without API calls. |
| `--user-email <email>` | Requester email. Final report/plan email is sent here. |
| `--operator-email <email>` | Operator email to CC, or fallback recipient if no requester is known. |
| `--detach` | Hidden launcher only: do not stream the child run log back to the current output. |
| `--agent` | Hidden launcher only: background run plus JSON metadata for chat polling. |
| `--watch` | Hidden launcher only: stream hidden child output even when `--agent` is used. |
| `--status-json <run_id_or_dir>` | Print current run status for agent/user polling. |
| `--approve` | Removed legacy flag; prints that Phase 11 approval execution was removed. |
| `--reject <reason>` | Removed legacy flag; prints that Phase 11 approval execution was removed. |
| `--status` | Removed legacy approval-status flag; use `--status-json`. |

## Configuration

| Surface | Current name |
| --- | --- |
| Skill folder | `skills/skill-ai-escape-mrc` |
| Python package | `ai_escape_mrc` |
| Local entrypoint | `run_ai_escape_mrc.py` |
| Managed-agent trigger | `trigger_ai_escape_mrc.py` |
| Managed-agent definition | `skill-ai-escape-mrc-v1.yaml` |
| Delivery status artifact | `runs/<run_id>/delivery-status.json` |
| Report directory | `docs/ai-escape-mrc-reports` |
| Report override env var | `CLAUDE_AI_ESCAPE_MRC_REPORTS_DIR` |
| Requester email env var | `CLAUDE_AI_ESCAPE_MRC_USER_EMAIL` |
| Operator email env var | `CLAUDE_AI_ESCAPE_MRC_OPERATOR_EMAIL` |
| Legacy operator fallback env var | `CLAUDE_AI_ESCAPE_MRC_EMAIL` |

`~/.claude/email.json`:

```json
{
  "recipient": "you@example.com",
  "enabled": true
}
```

Email routing:

- With requester email: `To=<requester>`, `Cc=<operator>`.
- Without requester email: `To=<operator>`, `recipient_source=operator_fallback`.
- Delivery status records `recipient_to`, `recipient_cc`, `recipient_source`,
  `email_delivery_result`, and any `email_delivery_error`.

Model routing:

- Local LangGraph runs use the active Claude/Codex environment model. The skill
  does not perform Anthropic API model discovery and does not hardcode a local
  model override.

## Repository Layout

```text
skill-ai-escape-mrc/
|-- SKILL.md
|-- run_ai_escape_mrc.py
|-- trigger_ai_escape_mrc.py
|-- generate_partial_report.py
|-- Makefile
|-- requirements.txt
|-- ai_escape_mrc/
|   |-- graph.py
|   |-- state.py
|   |-- models.py
|   |-- schemas.py
|   |-- heartbeat.py
|   |-- progress.py
|   |-- render.py
|   |-- validators.py
|   |-- parallel.py
|   |-- sdk_client.py
|   |-- delivery/
|   |-- managed_agent/
|   |-- phases/
|   `-- prompts/
|-- tests/
|-- docs/
|-- governance/
|-- templates/
|-- poc/
`-- agents/
```

## Development

Run the skill tests:

```powershell
py -3 -m pytest tests -q
```

Before committing, also run:

```powershell
py -3 -m compileall ai_escape_mrc run_ai_escape_mrc.py trigger_ai_escape_mrc.py
git diff --check
git status --short
```

Methodology note: the original lineage borrowed discipline from the 8D problem
solving method, but the active skill identity, command names, triggers, reports,
and runtime artifacts are AI Escape MRC.

## Credits

Built on top of:

- LangGraph
- Anthropic Python SDK
- claude-agent-sdk
