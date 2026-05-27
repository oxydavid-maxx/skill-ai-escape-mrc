---
name: skill-ai-escape-mrc
wiki_exempt: backfill execution_mode per surface-acceptance charter; no wiki-governed pattern
description: Use when reviewing AI harness, agent, CI, or browser/API automation flows that reported success but may have missed verification, renamed entrypoints, plugin links, generated docs, tests, runtime artifacts, delivery artifacts, or other escape paths. Triggers on AI automation escape review, harness escape, automation-flow escape, missed verification, false completion, non-detection, recurrence prevention, corrective action, proof of action, and managerial root cause. LangGraph FSM-driven with research, IS/IS-NOT scoping, four-quadrant TRC/MRC analysis, corrective/prevention matrices, proof-of-action verification, report/plan generation, and email delivery.
execution_mode: both
variant_note: Standalone non-discussion variant; Paddy may maintain a separate discussion-oriented variant.
---

# AI Escape MRC

Use this skill to review an AI harness or automation workflow that may have
escaped its own guardrails: it claimed completion, generated artifacts, pushed a
review, or announced success without proving that entrypoints, plugin links,
tests, generated documentation, runtime artifact names, and delivery artifacts still
matched the intended skill identity.

The implementation is a Python/LangGraph finite-state machine. Run the CLI
entrypoint; do not manually improvise the phases from this document.

> Version note: this standalone copy is the non-discussion AI Escape MRC
> variant. Paddy may maintain a separate discussion-oriented variant; keep that
> as a separate skill/version if it is added later.

## Invocation

Run the local entrypoint:

```powershell
py -3 D:/D-claude/skills/skill-ai-escape-mrc/run_ai_escape_mrc.py "<automation escape topic>"
```

Use `--user-email <email>` when the final report/plan email should go to the
requester. The operator from `~/.claude/email.json` is copied. If no requester
email is available, delivery falls back to the operator and the delivery status records
`recipient_source=operator_fallback`.

For Windows runs that must not open a new console window but should still show
live output in the current launcher, use:

```powershell
py -3 D:/D-claude/skills/skill-ai-escape-mrc/run_ai_escape_mrc_hidden.py "<automation escape topic>" --user-email user@example.com
```

Add `--detach` only for true fire-and-forget background mode. Detached runs
cannot print to a visible screen; they write the same summaries to the printed
stderr log and to `runs/<run_id>/stage-summaries.md/jsonl`.

When you are running this skill from inside a Codex/Claude agent, do not block
the conversation on a long shell command. Use deterministic watch mode so the
launcher itself streams the hidden run output back to the active conversation:

```powershell
py -3 D:/D-claude/skills/skill-ai-escape-mrc/run_ai_escape_mrc_hidden.py --agent --watch "<automation escape topic>" --user-email user@example.com
```

Detached agent runs are allowed only when the caller has its own polling loop.
In that case start with agent metadata, report the returned run id to the user,
then poll status and paste the human summary back into the chat:

```powershell
py -3 D:/D-claude/skills/skill-ai-escape-mrc/run_ai_escape_mrc_hidden.py --agent --detach "<automation escape topic>" --user-email user@example.com
py -3 D:/D-claude/skills/skill-ai-escape-mrc/run_ai_escape_mrc.py --status-json "<run_dir from the JSON metadata>"
```

Poll at least every 60 seconds while the run is active, and immediately report
phase changes, stall warnings, and completed phase summaries. The user must not
have to tail logs manually.

Optional flags:

- `--resume <run_id>`: resume an interrupted run.
- `--gc`: clean runs older than 30 days.
- `--dry-run`: print the planned run id without calling the Anthropic API.
- `--user-email <email>`: requester delivery target.
- `--operator-email <email>`: operator CC/fallback override.
- `--detach`: hidden launcher only; stop streaming logs to the current output.
- `--agent`: hidden launcher only; start in background and print JSON metadata
  for agent polling.
- `--watch`: hidden launcher only; stream hidden child output back to the
  current output even when `--agent` is used.
- `--status-json <run_id_or_dir>`: print a machine-readable status snapshot.
- `--approve` / `--reject <reason>` / `--status`: legacy approval-execution
  flags; they now report that Phase 11 execution was removed. Use
  `--status-json` for status.

## What The User Gets

During the run, startup and each phase start print immediately to the active
run output. Each completed phase then prints a brief summary. The same
summaries are persisted in
`runs/<run_id>/stage-summaries.md` and included in the final delivery email.
This is enforced by the Python/LangGraph runtime through visibility receipts;
if a required phase start, phase summary, or phase error receipt cannot be
emitted, the run fails closed with a visible `run-error.json` artifact.

On success, `run_ai_escape_mrc.py` prints a final delivery block with the
report path, plan path, stage summaries path, delivery status path, and email
result. If email delivery fails, the artifacts remain valid and the CLI exits
non-zero after printing the error and manual fallback.
Reports default to:

```text
D:/D-claude/skills/skill-ai-escape-mrc/docs/ai-escape-mrc-reports/
```

Override with `CLAUDE_AI_ESCAPE_MRC_REPORTS_DIR`. Email delivery uses requester
metadata when present and falls back to `~/.claude/email.json` through Outlook
COM when enabled.

Local LangGraph execution uses the active Claude/Codex environment model. Do
not add hardcoded local model IDs or Anthropic API model-discovery calls.

Summarize the emitted report for the user. Do not re-run phases manually; the
FSM is the source of truth.

## Mandatory Post-Completion Handoff

The AI Escape MRC run produces diagnosis and implementation design. It does not
itself land the corrective and prevention changes. After a successful run:

1. Read the report path printed by `run_ai_escape_mrc.py`.
2. Focus on the corrective actions, prevention actions, and proof-of-action
   sections.
3. Execute the implementation plan through the foreground planning/execution
   workflow used by this environment.
4. Verify with concrete test evidence before claiming completion.

Bypass only when the user explicitly says the run is for design inspection
only, or includes:

```text
EXEMPT post-ai-escape-mrc-execution: <reason>
```

## Architecture

- Python package: `ai_escape_mrc/`
- Main entrypoint: `run_ai_escape_mrc.py`
- Managed-agent trigger: `trigger_ai_escape_mrc.py`
- Delivery status artifact: `runs/<run_id>/delivery-status.json`
- Report directory: `docs/ai-escape-mrc-reports`
- Managed-agent name: `skill-ai-escape-mrc-v1`

Phase outline:

- Phase 0: dual-tier research for the specific escape and comparable patterns.
- Phase 1: IS/IS-NOT scoping.
- Phase 2: four-quadrant why analysis across TRC/MRC and NC/ND.
- Phase 3: root-cause audit with state-of-art evidence checks.
- Phase 4: corrective and prevention action matrices.
- Phase 5: prevention audit.
- Phase 6: proof-of-action verification plan.
- Phase 7: detailed report rendering and closure audit.
- Phase 8: action collection.
- Phase 9: implementation plan generation.
- Phase 10: final report/plan delivery.

Methodology note: the original lineage borrowed discipline from the 8D problem
solving method, but the active skill identity, commands, triggers, reports, and
runtime artifacts are AI Escape MRC.

## Configuration

`~/.claude/email.json`:

```json
{
  "recipient": "you@example.com",
  "enabled": true
}
```

Requester/operator env vars:

- `CLAUDE_AI_ESCAPE_MRC_USER_EMAIL`
- `CLAUDE_AI_ESCAPE_MRC_OPERATOR_EMAIL`
- `CLAUDE_AI_ESCAPE_MRC_EMAIL` (legacy operator fallback)
