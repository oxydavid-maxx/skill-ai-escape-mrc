# skill-8d-mrc → Claude Managed Agents Migration Design

**Date:** 2026-04-26
**Status:** brainstorm → spec (user authorized 2026-04-26 "use Managed Agents whenever possible. change skill 8d mrc"; user approved Q1=A skill-8d-mrc-only, Q2=A Phase 11 stays local; user added constraint "artifacts stays local")
**Source:** ecosystem 8D 2026-04-25 escape recurrence (R1-gate-failure on inventing-without-research, in-flight 8D fired 2026-04-26).

## Research informing this design (8 distinct WebSearches)

- **Anthropic Managed Agents docs (2026-04-08 launch):** [overview](https://platform.claude.com/docs/en/managed-agents/overview), [quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart), [agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup), [tools](https://platform.claude.com/docs/en/managed-agents/tools), [MCP connector](https://platform.claude.com/docs/en/managed-agents/mcp-connector), [environments](https://platform.claude.com/docs/en/managed-agents/environments), [memory](https://platform.claude.com/docs/en/managed-agents/memory).
- **Anthropic engineering deep dive:** [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents).
- **Pricing reference:** [WaveSpeed AI pricing](https://wavespeed.ai/blog/posts/claude-managed-agents-pricing-2026/), [Tygart Media pricing](https://tygartmedia.com/claude-managed-agents-complete-pricing-guide-2026/).
- **Human-in-the-loop pattern:** [SRE incident responder cookbook](https://platform.claude.com/cookbook/managed-agents-sre-incident-responder), [data analyst agent cookbook](https://platform.claude.com/cookbook/managed-agents-data-analyst-agent).
- **LangGraph→Managed Agents migration:** [eesel AI guide](https://www.eesel.ai/blog/claude-managed-agents) ("1-to-2-day porting"), [QubitTool framework comparison](https://qubittool.com/blog/ai-agent-framework-comparison-2026).
- **Rate limits + file API:** Managed Agents endpoints rate-limited 60 req/min create, 600 req/min read; `client.beta.files.list()` + `client.beta.files.download()` for /workspace artifact retrieval.
- **Sandbox:** gVisor-isolated container; /workspace writable, /source read-only; network egress default-deny.
- **Pydantic v2 strict mode:** ConfigDict(strict=True) for output schema validation; ValidationError aggregates all errors in single exception (used by trigger_8d.py for fail-closed validation).
- **win32com.outlook robustness:** single-threaded execution required (RPC_E_WRONG_THREAD on multi-thread); HRESULT '-2147221005' for invalid class string; "Operation aborted" on mail.Send() with security policy violations; Microsoft "unified Outlook" abandoned COM in 2024 (classic Outlook still works; future migration target = Graph API).

## Wiki consultation (per R6 + wiki-to-code-traceability convention)

- **WIKI-CONSULTED:** `function-replacement-convention#delete-in-same-commit` — old run_8d.py / phase_*.py / graph.py / sdk_client.py / child_runner.py MUST be deleted in same commit as new trigger_8d.py + managed_agent/ lands; preserved only as `legacy-pre-migration` git tag for rollback. WIKI-FINDING: dual-coexistence is a latent bug. WIKI-ACTION: spec mandates atomic-switch commit.
- **WIKI-CONSULTED:** `silent-staleness#misleading-metadata-trap` — gate file `created_at` recorded for audit only; freshness derives from data content (cloud session_id + phase_metadata.completed_phases). WIKI-FINDING: freshness must derive from data content, not timestamp metadata. WIKI-ACTION: applies same as prior design.
- **WIKI-CONSULTED:** `wiki-to-code-traceability` — triple-marker pattern enforced via pre-commit hook; spec uses WIKI-CONSULTED/FINDING/ACTION format. WIKI-FINDING: text instructions fail; structural gates enforce. WIKI-ACTION: trigger_8d.py + managed_agent yaml will include triple markers per FRC.
- **WIKI-CONSULTED:** `degraded-emission-with-warning` — producer is responsible for bundling everything the recipient needs; never emit a partial artifact that requires the recipient to perform additional retrieval. WIKI-FINDING: redirect-to-external-source patterns are forbidden. WIKI-ACTION: error emails fetch the cloud session event log via API and include inline; spend alerts include current month-to-date spend inline.
- **WIKI-CONSULTED:** `claude-agent-sdk-patterns` — Issue #573 (CLAUDECODE inheritance) becomes irrelevant post-migration: cloud agent runs in Anthropic sandbox, no local subprocess at all. WIKI-FINDING: nested-session detection bug only affects local subprocess.Popen of SDK; not applicable to managed cloud sessions. WIKI-ACTION: child_runner.py + Issue #573 mitigation deleted as part of migration.
- **WIKI-CONSULTED:** `anthropic-oauth-policy-2026` — Managed Agents are billed separately from Claude Max OAuth subscription. WIKI-FINDING: Max sub does not cover Managed Agents session-hour billing. WIKI-ACTION: spec includes pricing analysis + org-level spend cap.

## Goal

Migrate skill-8d-mrc from local LangGraph FSM (12-phase, SqliteSaver, asyncio.gather, child SDK Popen) to a single Anthropic Claude Managed Agents session. Keep artifacts local (per user directive 2026-04-26). Keep Phase 11 (executing-plans) local. Eliminate the local CPU pressure that today spawns 3+ python processes per 8D run.

## Non-goals

- Migrating skill-deep-* / skill-deep-research-* / skill-deep-sys2 (markdown-driven, not Python compute, not the CPU bottleneck)
- Migrating daily_brief LLM calls (bounded; ~5 min/day; not the CPU bottleneck)
- Cloud-side artifact storage as the long-term home (artifacts stay local per directive; cloud /workspace is staging only, downloaded to local at boundary)
- Multi-user agent sharing (single user — kuangyu)
- Auto-failover from Managed Agents back to local LangGraph (rollback via `git checkout legacy-pre-migration`)
- Migrating ~/.claude hooks/gates/governance (local-by-design; ManagedAgents has no equivalent for personal-workflow scaffolding)
- Migration to Microsoft Graph API for email (deferred; classic Outlook COM still works in 2026)

## Constraints (research-validated)

1. **Beta status:** Managed Agents currently beta; all endpoints require `anthropic-beta: managed-agents-2026-04-01` header. SDK sets it automatically. Pin beta version; monitor changelog.
2. **gVisor sandbox + network default-deny:** cloud agent has /workspace (writable) + /source (read-only) but cannot reach user's local FS, Outlook COM, WebView2 CDP, or any non-allowlisted domain.
3. **Pricing:** $0.08/session-hour runtime + standard Claude API token rates ($5/M input + $25/M output for Opus 4.6) + $10/1k WebSearches. Idle time excluded. Cache reads 0.1× discount.
4. **Rate limits:** 60 req/min create endpoints, 600 req/min read endpoints. Our 5-min poll cadence = 0.2 req/min, well under.
5. **MCP toolset permission policy default `always_ask`** — would require human approval per tool call. We use NO MCP servers in v1 to avoid this; only built-in tools.
6. **Custom tools as pause primitive:** when agent calls a custom tool, session goes `stop_reason.type == "requires_action"` and waits for `user.custom_tool_result`. We don't use this in v1; cloud session ends after Phase 9 returns artifacts; local handles approval.
7. **Phase 11 must stay local:** executing-plans modifies the user's repo; cloud sandbox can't reach local FS. Phase 11 invokes superpowers:executing-plans in the user's interactive Claude Code session.
8. **File API for /workspace:** `client.beta.files.list()` + `client.beta.files.download()` retrieves artifacts from the cloud sandbox to local disk.
9. **win32com single-threaded:** Outlook COM email send must run in the main thread of trigger_8d.py; no asyncio dispatch. Trap COM exceptions and retry on transient errors.
10. **Pydantic strict-mode validation:** trigger_8d.py uses `ConfigDict(strict=True)` to refuse coerced types in cloud-returned payload.

## Architecture

### Single-shot cloud session, local approval portal, local Phase 11

```
LOCAL                                  CLOUD (single Managed Agent session)
trigger_8d.py <problem>
  POST /v1/agents/sessions
  headers: anthropic-beta: managed-agents-2026-04-01
  body: {agent_id: skill-8d-mrc-v1, input: <problem>}
  ────────────────────────────────►   Session: /workspace + sandbox + harness
                                      Tools: agent_toolset_20260401 + websearch_20260401
                                      Phases 0-9 run as natural agent flow:
                                        - Phase 0: 8 parallel WebSearch calls
                                        - Phase 1-2: IS/IS NOT + Why analysis
                                        - Phase 3: SoA + RC audit (3 rounds)
                                        - Phase 4: 4 parallel quadrant action gen
                                        - Phase 5: Prevention audit (3 rounds)
                                        - Phase 6: Verification plan
                                        - Phase 7: Report rendering (~770s)
                                        - Phase 8: Action collection (instant)
                                        - Phase 9: writing-plans (consolidated into prompt)
                                      Final response = structured payload
                                      Artifacts also written to /workspace

  Poll GET /v1/agents/sessions/<id>/events  (every 5 min)
    - filter for phase-complete events
    - post each to Telegram diagnostics topic 63

  session.status == "completed"
  ◄──────────────────────────────── {report_md, actions_json, plan_md, phase_metadata}

  client.beta.files.list(session_id) + .download(file_id)
    → mirror /workspace artifacts to local runs/<run_id>/

  Pydantic strict-mode validation of payload (R13: refuse if malformed)
  writes runs/<run_id>/report.md  (or uses downloaded copy)
  writes runs/<run_id>/actions.json
  writes runs/<run_id>/plan.md
  writes runs/<run_id>/cloud_events.jsonl  (full event log archive for replay)
  writes ~/.claude/.pending-8d-approvals/<run_id>.json
  sends consolidated email via Outlook COM (single-thread, com_error retry)
  exits 0 (cloud session terminated; no further billing)

(user approves via email reply OR session reply — UNCHANGED from today's portals)

trigger_8d.py --resume <run_id> --approve
  reads gate's plan_md (gate file is self-contained)
  invokes superpowers:executing-plans IN-SESSION (user's Claude Code)
  → files modified locally + commits land
```

### Components

| File | Status | Responsibility |
|---|---|---|
| `eightd/managed_agent/skill-8d-mrc-v1.yaml` | NEW | Anthropic Managed Agents config: name, description, model, system prompt ref, tools, network allowlist |
| `eightd/managed_agent/system_prompt.md` | NEW | Extracted system prompt (consolidated from prior phase_*.py prompts) |
| `eightd/managed_agent/output_schema.py` | NEW | Pydantic v2 BaseModel with ConfigDict(strict=True) for the structured payload |
| `trigger_8d.py` | NEW | Thin orchestrator: Anthropic API client + heartbeat + file download + artifact writer + gate emitter + email send + Phase 11 dispatcher |
| `eightd/delivery/email.py` | KEPT | Outlook COM email send unchanged; single-threaded with com_error retry |
| `eightd/heartbeat.py` | MODIFIED | Source changed from local progress.jsonl to Anthropic /v1/agents/sessions/<id>/events polling; same Telegram diagnostics output |
| `~/.claude/.pending-8d-approvals/<run_id>.json` | KEPT (convention) | Gate file format unchanged; trigger_8d.py writes it |
| `~/.claude/hooks/sessionstart-8d-approval-banner.sh` | KEPT | Approval portal unchanged |
| `~/.claude/hooks/userpromptsubmit-8d-approval-detect.sh` | KEPT | Session approval portal unchanged |
| `~/.claude/bin/outlook-approval-poller.py` | KEPT | Email approval portal unchanged |
| `run_8d.py` | DELETED | Per FRC; replaced by trigger_8d.py atomically |
| `eightd/graph.py` | DELETED | LangGraph FSM logic ported to system_prompt.md |
| `eightd/state.py` | DELETED | EightDState TypedDict not needed (cloud agent manages own state via session log) |
| `eightd/phases/phase_0_research.py` ... `phase_9_write_plan.py` | DELETED | Logic ported to system_prompt.md |
| `eightd/phases/phase_10_emit_and_wait.py` | DELETED | Replaced by trigger_8d.py post-cloud orchestration |
| `eightd/phases/phase_11_execute.py` | DELETED | Replaced by trigger_8d.py --resume --approve invoking superpowers:executing-plans directly |
| `eightd/sdk_client.py` | DELETED | Cloud agent IS the Anthropic API caller; local doesn't need wrapper |
| `eightd/child_runner.py` | DELETED | No subprocess.Popen; no Issue #573 mitigation needed |
| `eightd/parallel.py` | DELETED | Cloud agent's internal harness handles parallelism |
| `eightd/prompts/` | DELETED (after porting) | All prompts consolidated into system_prompt.md |
| `eightd/schemas.py` | KEPT (modified) | Pydantic models for output_schema validation in trigger_8d.py |
| `eightd/utils.py` | KEPT (audit) | Utility functions still useful for trigger_8d.py |
| `tests/test_phase_*.py` | DELETED | Phases no longer exist as Python; new tests focus on trigger_8d.py + schema validation + heartbeat polling |
| `tests/test_trigger_8d.py` | NEW | Unit + integration tests for the new orchestrator |
| `tests/test_managed_agent_yaml.py` | NEW | Validates yaml config + system prompt structure |

### Anthropic API endpoints used

| Endpoint | Purpose | Frequency |
|---|---|---|
| `POST /v1/agents/sessions` | Create session, start agent | 1× per 8D run |
| `GET /v1/agents/sessions/<id>/events` | Poll for phase progress events | Every 5 min while session running |
| `GET /v1/agents/sessions/<id>` | Check session status | At end of polling cycle |
| `client.beta.files.list(session_id)` | List /workspace artifacts | 1× at session completion |
| `client.beta.files.download(file_id)` | Pull each artifact to local | N× per session (one per artifact) |
| `DELETE /v1/agents/sessions/<id>` | Terminate session after final response (best-effort cleanup) | 1× per run |

All require `anthropic-beta: managed-agents-2026-04-01` header. Total req/min budget well under the 600/min read limit.

### Output payload schema (Pydantic v2 strict)

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class ActionItem(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    files_touched: list[str] = Field(default_factory=list)
    owner: str = "kuangyu"
    priority: Literal["low", "medium", "high", "verification"] = "medium"
    source_quadrant: str

class PhaseMetadata(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    phases_completed: list[str]
    phase_durations_sec: dict[str, float]
    total_runtime_sec: float
    total_tokens_used: dict[str, int]

class CloudPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    report_md: str = Field(..., min_length=1000)
    actions_json: list[ActionItem]
    plan_md: str = Field(..., min_length=500)
    phase_metadata: PhaseMetadata
```

trigger_8d.py validates against `CloudPayload` BEFORE writing any artifact. On `ValidationError`, the exception aggregates all field errors; trigger_8d.py extracts each error + maps to which schema rule failed; emails the full diagnostic inline. Refuses to write artifacts (R13 fail-closed).

### Pricing analysis (per 8D run, research-backed)

| Component | Cost | Notes |
|---|---|---|
| Session runtime ($0.08/session-hour) | ~$0.04 | Current 8D runs ~30 min; idle time during user approval doesn't count (session terminates at Phase 9 end) |
| Token cost (Opus 4.6 $5/M input + $25/M output) | ~$1-3 | Same as today's local API calls; no change |
| WebSearch ($10/1k searches) | ~$0.08 | ~8 searches per Phase 0 + 0 in other phases |
| **Total per 8D run** | **~$1.20-3.20** | Driven by token costs (model usage) more than runtime |

Net delta vs today: +$0.04 runtime cost per run, minus local CPU/RAM saved. Worth it.

**Spend cap:** set Anthropic org-level spend limit at $50/month for Managed Agents. Alert email at 80% threshold includes current month-to-date spend + remaining budget + run-count breakdown inline.

### Migration strategy: parallel preservation, atomic switch

1. **Phase A (build alongside, no destruction):** Create `eightd/managed_agent/` + `trigger_8d.py` alongside existing `run_8d.py`. Both exist.
2. **Phase B (test parity):** E2E test trigger_8d.py against a small problem; verify output matches run_8d.py output for the same problem (modulo non-determinism in LLM responses).
3. **Phase C (atomic switch in single commit, per FRC):**
   - SKILL.md: change invocation example from `py -3 run_8d.py` to `py -3 trigger_8d.py`
   - DELETE: run_8d.py, eightd/graph.py, eightd/state.py, eightd/phases/, eightd/sdk_client.py, eightd/child_runner.py, eightd/parallel.py, eightd/prompts/
   - All in ONE commit so rollback = `git revert <sha>`
   - Tag prior commit as `legacy-pre-managed-agents-migration` for safety
4. **Phase D (monitor 1 week):** Run 1-2 8Ds via trigger_8d.py; verify cost + correctness; confirm CPU pressure resolved. If issues, revert atomically.

## Error handling — self-contained per R13

The principle: producer bundles every piece the recipient needs to act. No external retrieval steps required.

| Failure | Handling |
|---|---|
| Cloud session creation fails | Retry 1× with exponential backoff; on second failure trigger_8d.py emails error containing the HTTP status + response body + last 10 lines of local log. Exit non-zero. No artifacts written. |
| Cloud session times out / errors mid-run | trigger_8d.py polls events endpoint, fetches full event log via the /events API, emails error with: session_id + total_runtime_sec + first 50 events + last 10 events + error_reason — all inline. No partial artifact write. |
| Output payload schema-invalid | trigger_8d.py extracts the invalid payload + ValidationError aggregated errors + maps each error to which schema rule failed; emails the full diagnostic inline. Refuses to write artifacts (R13). |
| Local Outlook COM email send fails | Gate file still written (Portal B / session approval still works); email-send failure logged to `runs/<run_id>/email_failure.log` with full COM exception trace inline. SessionStart hook surfaces both the gate AND the email-failure-log path in the next session's banner. |
| Outlook COM raises RPC_E_WRONG_THREAD | Indicates threading bug in trigger_8d.py; alert inline + abort run; this is a code defect not a transient. |
| Phase 11 (executing-plans) fails | Same as today — heartbeat surfaces failure; user can retry via --resume --approve idempotently. trigger_8d.py captures executing-plans exit code + tail of session output, includes inline in email if failure. |
| Anthropic spend cap hit | API returns error; trigger_8d.py emails alert containing: current month-to-date spend, remaining budget, last 5 run costs, projected days until cap at current rate — all inline. |
| Beta API breaks (header version bump) | trigger_8d.py refuses to call with mismatched header; emails error with the expected header version + observed version + inline-fetched Anthropic changelog excerpt + suggested action. |

## Testing strategy

- **Unit:** trigger_8d.py heartbeat polling logic with mocked Anthropic API responses (3 fixtures: in-progress, complete, error)
- **Unit:** Pydantic CloudPayload validation (3 fixtures: valid, missing field, malformed actions)
- **Unit:** managed_agent/skill-8d-mrc-v1.yaml structural validation (required keys, model name correctness, tool list)
- **Unit:** file download flow (mock client.beta.files.list/download)
- **Unit:** Outlook COM single-thread enforcement (assert no asyncio dispatch around send)
- **Integration:** end-to-end with mocked Anthropic responses → assert all artifacts written + gate file appears + email called
- **Live E2E:** real 8D run on a trivial problem ("test problem for managed-agent migration verification"); compare output structure to a parallel run via legacy run_8d.py before deleting it (Phase B above); cost ≤ $5

## Risks + mitigations (research-backed)

| Risk | Mitigation |
|---|---|
| **Beta API changes** mid-deployment | Pin `managed-agents-2026-04-01` header version; trigger_8d.py emits weekly Anthropic-changelog summary inline to Telegram diagnostics so version drift is visible without polling external sources |
| **Session timeout for long 8Ds** (no max documented) | First live test is small problem; if 30+ min runs hit timeout, investigate session-extension API or split into multiple sessions |
| **Cost runaway** | Org-level spend limit $50/month; weekly review automation: trigger_8d.py weekly cron emails spend report inline |
| **Cloud agent invents wrong outputs** (no LangGraph schema enforcement) | Pydantic strict-mode validation at boundary; refuse-on-malformed (R13); compare structure vs legacy run_8d.py during Phase B |
| **Loss of LangGraph time-travel debugging** | Anthropic's session event log replaces this; trigger_8d.py archives full event log to runs/<run_id>/cloud_events.jsonl for local replay |
| **Migration breaks Phase 11** | Phase 11 is local + reads gate file's plan_md (self-contained); doesn't depend on cloud session being alive |
| **Skills (superpowers:writing-plans) not invocable from cloud agent** | Phase 9's writing-plans logic ported INTO the system prompt (cloud agent emits plan directly, not via skill invocation); no dependency on Claude Code skills cloud-side |
| **Vendor lock-in** | Legacy run_8d.py preserved in git history; rollback via `git revert`; alternative path = re-implement LangGraph FSM if Anthropic deprecates Managed Agents |
| **Network egress allowlist insufficient** | Test WebSearch tool (cloud-native) early; only Anthropic-domain calls needed for v1; no external custom MCP servers |
| **Heartbeat polling burns Anthropic API quota** | 5-min cadence = 0.2 req/min, well under 600 req/min read limit; bounded |
| **Outlook COM threading bug** | Tests assert single-threaded send path; CI catches RPC_E_WRONG_THREAD on multi-thread call attempts |
| **Future Outlook COM deprecation** | Microsoft "unified Outlook" abandoned COM in 2024; classic Outlook still works in 2026; deferred migration target = Microsoft Graph API for email send |

## Out-of-scope deferrals

- MCP server integration (deferred until Phase 11 needs cloud-side file access — currently local)
- Custom tool definitions for human-in-the-loop pause inside cloud session (deferred — local approval portal handles HITL externally)
- Telegram inline-button approval (Portal C from prior design) — still deferred
- Multi-concurrent 8D runs sharing approval state — defer to v2
- Auto-cleanup of stale gate files (>30d unanswered) — manual; defer to quarterly audit
- Memory store mounts for cross-run persistence (cookbook pattern; not needed for v1 since each 8D is independent)
- Migration to Microsoft Graph API for email (classic Outlook COM still works; revisit if/when COM breaks)

## Owner

skill-8d-mrc maintainer (kuangyu).

## Source

- User directives 2026-04-26: "use to manage agent whenever possible. change flow and superpower. change skill 8d mrc.", Q1=A (skill-8d-mrc only), Q2=A (Phase 11 stays local), "artifacts stays local", "I'm on the move, can't reply. move on by yourself. fix any hang. make the full research on managed agent, and move on."
- Research 2026-04-26 (8 distinct WebSearches): Anthropic Managed Agents docs, pricing analysis, MCP server patterns, HITL patterns, LangGraph migration guide, framework comparisons, rate limits, file download API, Pydantic v2 strict mode, win32com Outlook robustness.
- Wiki concepts: function-replacement-convention, silent-staleness, wiki-to-code-traceability, degraded-emission-with-warning, claude-agent-sdk-patterns, anthropic-oauth-policy-2026.
