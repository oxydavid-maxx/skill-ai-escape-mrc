<!--
WIKI-CONSULTED: function-replacement-convention
WIKI-FINDING: Coexisting old+new implementations behind a flag is the "later = never" anti-pattern. The 7-day window in the Copilot incident caused 4 days of silent data loss. Delete the replaced implementation in the same commit; rely on NameError as Level 1 prevention.
WIKI-ACTION: Removed the originally-planned `USE_SDK=0` feature flag and `anthropic_client_legacy.py` retention. The replacement commit deletes `anthropic_client.py` outright; all callers migrate in the same commit; rollback path is `git revert`, not a living dual implementation.
WIKI-CONSULTED: wiki-to-code-traceability
WIKI-FINDING: Marker convention (WIKI-CONSULTED / WIKI-FINDING / WIKI-ACTION) exists for exactly this case — design documents that touch wiki-governed patterns must record what wiki knowledge shaped the design.
WIKI-ACTION: This header block records the consultation.
-->

# skill-8d-mrc — Nested-Session Fix Design

**Status:** Draft (brainstorming complete, ready for plan writing)
**Author:** Claude (with user)
**Date:** 2026-04-22
**Scope:** Replace `eightd/anthropic_client.py`'s raw `claude -p` subprocess pattern with Claude Agent SDK. Keep LangGraph. Keep Max OAuth. Keep filesystem protection hooks firing. Eliminate the superpowers-plugin SessionStart token injection that bloats every SDK call.

---

## 1. Problem

`eightd/anthropic_client.py` calls `subprocess.run(["claude", "-p", ...])` per LLM call. When that Python process is itself spawned from inside a Claude Code session (via `Bash: py -3 run_8d.py`), every subprocess becomes a nested Claude Code session. Per official docs (`code.claude.com/docs/en/sub-agents`): *"Claude Code cannot be launched inside another Claude Code session — nested sessions share runtime resources and will crash all active sessions."*

Observed pathology in yesterday's 79-minute run:
- Each of ~14 LLM calls took 60–180s (vs ~10s expected), due to agent-mode drift and auto-memory bleed into narrow schema-emission prompts.
- Schema calls (`--json-schema`) hung or returned empty stdout.
- 4 of 7 generative phases fell through to stub fallbacks.
- Wall clock 79 min vs user target 10–20 min.

## 2. Constraints (user-directed, non-negotiable)

1. **LangGraph stays** as the orchestrator (StateGraph, SqliteSaver checkpointer, phase-level nodes).
2. **No API key.** Auth is Claude Max OAuth via the `claude` CLI. The April-4-2026 Anthropic policy blocks third-party OAuth proxies; only first-party paths (claude CLI, Claude Code, MCP) remain legal.
3. **Protection hooks stay.** `~/.claude/hooks/` gates (pipeline-gate, claudemd-gate, stop self-healing, auto-commit) must keep firing on SDK-spawned subprocess sessions exactly as they do for interactive sessions.
4. **3-round audit loops stay.** Rigor is not traded for runtime.
5. **Output: report only.** Skill generates the 8D markdown report; user approves before any implementation.

## 3. Decision

Use Claude Agent SDK (`claude-agent-sdk==0.1.63`) as the LLM transport inside LangGraph nodes. SDK spawns `claude` CLI under the hood — first-party, OAuth-covered, policy-safe. Use an **environment-gated short-circuit** in the superpowers-plugin SessionStart hook to suppress its ~23K token `additionalContext` injection for SDK-spawned sessions, while all other filesystem hooks continue to fire normally on both interactive and SDK paths.

### 3.1 Why this option over alternatives

| Alternative | Status | Reason |
|---|---|---|
| Mode A — inherited hooks, no mitigation | Rejected | 23K-token SessionStart bleed per SDK call; aesthetic and potential correctness concern for narrow schema prompts |
| Mode A+ — programmatic SDK hooks (`ClaudeAgentOptions.hooks=`) | Rejected | Requires refactoring hook rule engines into Python library + wiring adapters; overkill when only *one* hook (superpowers SessionStart) needs suppression |
| Mode D — LangGraph as standalone MCP server | Deferred | Adds server lifecycle, port management, and MCP registration; cleaner isolation but unnecessary if short-circuit works. Keep as contingency |
| Dario / OAuth proxy | Blocked | April-4-2026 policy ended third-party OAuth access to Max subscriptions |

The chosen option is minimum intervention: one env-check added to one hook script; one `env={}` field added to the SDK caller. Filesystem hooks continue to work for interactive sessions unchanged. SDK sessions fire the same protection hooks but skip the superpowers-specific injection.

## 4. Architecture

### 4.1 Process topology

```
User terminal  OR  Claude Code session (Bash: py -3 run_8d.py)
         ↓
  run_8d.py  (python entry, asyncio.run)
         ↓
  LangGraph StateGraph  (eightd/graph.py, unchanged)
         ↓
  eightd/sdk_client.py  (replaces anthropic_client.py)
         ↓ subprocess per call
  claude CLI in stream-json mode
         ↓ HTTPS
  api.anthropic.com  (Max OAuth)
```

### 4.2 Module-level changes

| File | Change | Purpose |
|------|--------|---------|
| `eightd/anthropic_client.py` | **Deleted** in same commit that introduces the replacement (per function-replacement-convention wiki) | Subprocess CLI path removed; coexistence forbidden |
| `eightd/sdk_client.py` | **NEW** | Async wrapper around `claude_agent_sdk.query()`; extracts text + `StructuredOutput` tool-block; retries; applies the hook-skipping env |
| `eightd/phases/*.py` | **Modified** | All imports `from eightd.anthropic_client import ...` → `from eightd.sdk_client import ...`; `def` → `async def`; serial loops → `asyncio.gather` within a phase where state allows |
| `eightd/progress.py` | Unchanged | JSONL append is already thread-/async-safe |
| `run_8d.py` | **Modified** | `asyncio.run(main())`; preserve `--resume`, `--resend` CLI flags |
| `tests/` | **Modified** | Mock `claude_agent_sdk.query` via synthetic AsyncIterator; reuse phase test structure; delete tests that exercised `anthropic_client` subprocess internals |
| `~/.claude/hooks/<superpowers-SessionStart-hook>` | **Modified** (one line added) | Exit early when `CLAUDE_SDK_CALL=1` in env |

Exact path of the superpowers SessionStart hook is determined at implementation time by inspecting `~/.claude/plugins/cache/claude-plugins-official/superpowers/<version>/hooks/` (or wherever the `using-superpowers` skill's SessionStart registration resolves to). Plan writes a dedicated task for this lookup.

### 4.3 `sdk_client.py` contract

```python
async def call_claude(
    prompt: str,
    *,
    system_prompt: str,
    schema: dict | None = None,
    timeout_sec: int = 90,
    max_turns: int = 3,
) -> dict:
    """Return {"text": str, "structured": dict|None, "usage": dict}.

    Implementation details:
      - setting_sources=None                 → no CLAUDE.md / auto-memory loading
      - env={"CLAUDECODE": "", "CLAUDE_SDK_CALL": "1"}
          - first pair: Issue #573 workaround for nested-session rejection
          - second pair: signals the superpowers SessionStart hook to skip injection
      - allowed_tools=[]                     → no tool use required for plain prompts
      - output_format={"type":"json_schema","schema":schema}  when schema given
      - Parse StructuredOutput tool_use blocks
          (AssistantMessage.content → ToolUseBlock where name == "StructuredOutput";
          return block.input as `structured`)
      - Retry once on (empty text AND no structured output AND ResultMessage.is_error == False)
      - Raise TimeoutError on asyncio wait_for timeout
    """
```

### 4.4 Environment short-circuit for superpowers SessionStart hook

At the top of the superpowers SessionStart hook script, add one guard:

```bash
# Skip superpowers additionalContext injection for skill-8d-mrc SDK calls.
# Interactive sessions and normal Claude Code use continue unchanged.
[ "$CLAUDE_SDK_CALL" = "1" ] && exit 0
```

SDK caller in `sdk_client.py` sets:

```python
opts = ClaudeAgentOptions(
    env={"CLAUDECODE": "", "CLAUDE_SDK_CALL": "1"},
    ...
)
```

Net effect:
- Interactive Claude Code session: `CLAUDE_SDK_CALL` not set → superpowers hook injects normally → user's sessions work as today.
- SDK-spawned subprocess session: env is set → superpowers hook exits 0 early → no ~23K injection → narrow-schema calls stay focused.
- All other filesystem hooks (pipeline-gate, claudemd-gate, stop self-healing, auto-commit) are unaffected in both paths; they fire on the actual events they care about.

### 4.5 Parallelism

`asyncio.gather` replaces serial loops where state allows:

| Phase | Current | New |
|-------|---------|-----|
| 0 research | 9 serial websearches | 9 parallel |
| 1 IS/IS NOT | 1 call | unchanged |
| 2 Why chains | 4 quadrants × 10 whys, all serial | 4 quadrants in parallel; 10 whys serial within a quadrant (state-dependent) |
| 3 RC audit | 3 rounds × per-quadrant review, serial | Rounds serial; per-round parallel across quadrants |
| 4 actions | 8 serial calls | 8 parallel |
| 5 prevention audit | 3 rounds, serial | Same pattern as phase 3 |
| 6 verification | 4 plan entries, serial | 4 parallel |
| 7 render | 1 call | unchanged |

Projected wall clock (from POC timing + parallelism projection): **~13 minutes**, safely under the 20-min target. Concurrency cap at 4 workers per phase to avoid tripping the `five_hour` rate-limit window.

### 4.6 Schema handling

`ClaudeAgentOptions.output_format={"type":"json_schema","schema":...}` translates internally to the claude CLI `--json-schema <json>` flag. The model emits schema-conforming data not on `ResultMessage.structured_output` (None in every POC test) but as:

```
AssistantMessage(content=[ToolUseBlock(name="StructuredOutput", input={...})])
```

`sdk_client.call_claude` scans `AssistantMessage.content` for this block and returns `block.input` as `structured`. `max_turns` must be `≥ 2` (tool_use + tool_result is two turns); default `max_turns=3` provides margin.

**Contract risk mitigation:** The `StructuredOutput` tool-block name is not documented in the public SDK reference. Pin SDK version (`claude-agent-sdk==0.1.63` in `requirements.txt`), log a WARNING-level message if a future version emits differently-named ToolUseBlocks, and include a defensive fallback: scan for any ToolUseBlock whose `input` is a dict with keys matching the schema's top-level properties.

## 5. Execution modes

Both modes use the same code path. No detached-vs-nested branching.

| Mode | Command | Parent session | Hooks that fire | Expected runtime |
|------|---------|----------------|-----------------|------------------|
| Terminal | `py -3 run_8d.py "problem"` | None | Filesystem hooks for claude CLI subprocess calls; superpowers SessionStart skipped via env | ~13 min |
| Inside Claude Code | `Bash: py -3 run_8d.py "problem"` | Claude Code parent session | Same as above, plus Claude Code's own parent-session hooks for the `Bash` invocation itself | ~13 min |

## 6. Rollout

**No feature flag. No legacy path.**

Per the function-replacement-convention wiki: the commit that introduces `sdk_client.py` *also* deletes `anthropic_client.py` and updates every caller. `NameError` at import time enforces correct migration — Level 1 architectural elimination of the subprocess CLI pathway.

**Rollback path:** `git revert <sha>`. Git history is the rollback mechanism, not a live flag. If a regression surfaces post-merge, the revert restores the subprocess CLI path as a single atomic change.

**OpenRouter fallback** is a separate, orthogonal retry path for API-level errors (already present in the codebase); it is NOT touched by this change and continues to serve its existing purpose.

## 7. Testing strategy

### 7.1 Unit tests (`tests/test_sdk_client.py`)
- Mock `claude_agent_sdk.query` as AsyncIterator yielding synthetic messages.
- Assert `call_claude` extracts text from `TextBlock` blocks.
- Assert it extracts structured output from `ToolUseBlock(name="StructuredOutput")`.
- Assert it raises TimeoutError on timeout.
- Assert it retries once on (empty text ∧ no structured ∧ not is_error).
- Assert `env` passed to options always includes `CLAUDE_SDK_CALL=1` and `CLAUDECODE=""`.

### 7.2 Existing phase tests
- Each phase test replaces its `call_claude` mock to return the new `{"text", "structured", "usage"}` shape.
- Tests that exercised subprocess stdout/stderr/exit-code flows are deleted alongside `anthropic_client.py`.

### 7.3 Integration test (`tests/integration/test_phase_1_live.py`, skipped unless `RUN_LIVE=1`)
- Runs Phase 1 (IS/IS NOT) end-to-end against the real SDK on a minimal fixture problem.
- Asserts: structured output populated; elapsed < 2 min; `runs/<id>/progress.jsonl` contains `phase_1_start` and `phase_1_end`.

## 8. Risks + mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `StructuredOutput` tool name changes in future SDK version | Medium | Pin SDK version; defensive fallback scans ToolUseBlocks by schema-key shape |
| Five-hour rate limit trips during burst parallelism | Medium | Concurrency cap of 4 per phase; tenacity retry on 429 with exponential backoff |
| `CLAUDE_SDK_CALL` env accidentally persists in user shell and disables superpowers hook globally | Low | Env is set via SDK `options.env` dict per call — it does not export to the shell; documented in spec |
| Schema subprocess flakiness recurs at `max_turns=3` under load | Low-Medium | Integration test exercises schema + long prompt; retry policy documented; single-commit revert is the rollback if regression ships |
| Path to the superpowers SessionStart hook is not obvious at implementation time | Low | Plan includes an explicit "locate hook script" task with grep command |
| Anthropic further tightens first-party scope to exclude SDK subprocess | Low | Contingency: Mode D (MCP server) — preserved as a deferred option in this spec |
| `git revert` rollback reintroduces the nested-session bug mid-investigation | Low | Revert is reserved for genuine regressions, not for side-by-side comparison. Comparison use case is covered by running `poc/sdk_subagent_probe.py` (kept post-merge) |

## 9. Non-goals

- Not migrating away from LangGraph.
- Not adding programmatic SDK hook wiring (`ClaudeAgentOptions.hooks`). Filesystem hooks + one env short-circuit suffices.
- Not standing up an MCP server (Mode D); deferred.
- Not touching the OpenRouter fallback path.
- Not refactoring `~/.claude/hooks/_common/` rule engines.
- Not reducing audit round count (user requires 3).
- Not eliminating per-call API latency below Anthropic's inference time.
- **Not keeping a flag-gated legacy implementation alive** (per function-replacement-convention wiki).
- Not addressing production-SDK concerns (cost governance, circuit breakers, spend ledger, multi-tenant permission scoping) — skill-8d-mrc is single-user, Max-subscription, checkpointed via existing SqliteSaver.

## 10. Verification

**POC (done).** `poc/sdk_subagent_probe.py` passes 5/5:
1. Max OAuth auth without `ANTHROPIC_API_KEY` — 13.8s.
2. Narrow-scope resistance to drift — 13.8s, clean 3-bullet output.
3. Simple json_schema structured output — 18.4s.
4. Nested IS/IS NOT schema — 59.6s.
5. 4-way asyncio.gather parallelism — 35.5s.

Full report: `docs/oauth-sdk-feasibility-report.md`.

**Implementation-level (future).**
1. `py -3 -m pytest tests/ -q` all green.
2. `py -3 run_8d.py "small-test-problem"` completes in < 20 min wall-clock.
3. `runs/<id>/progress.jsonl` shows overlapping timestamps for phase-2 quadrants (proves parallelism).
4. SDK subprocess session shows `cache_creation_input_tokens < 3K` in `ResultMessage.usage` (proves superpowers SessionStart injection skipped).
5. Interactive Claude Code session *still* shows the superpowers injection (proves short-circuit is env-gated, not global).
6. Pipeline-gate / claudemd-gate / stop-hook fire when SDK-generated tool calls violate rules (end-to-end hook protection).
7. `grep -rn "anthropic_client" eightd/ tests/` returns no hits (proves clean replacement, not coexistence).

## 11. Open questions (deferred to plan/implementation)

- Exact filesystem path to the superpowers SessionStart hook script inside the plugin cache. Resolved during plan writing via grep.
- Whether `setting_sources=None` alone skips loading `~/.claude/settings.json` hook registrations. If yes, Section 4.4's env short-circuit still works and is additionally insured by the settings-load bypass. Integration test confirms behavior.
- Whether `asyncio.gather` over 9+ websearches trips the five-hour overage rejection. Measure on first real run; adjust concurrency cap if needed.

---

## Appendix: POC references

- Feasibility report: `D:/D-claude/skills/skill-8d-mrc/docs/oauth-sdk-feasibility-report.md`
- POC scripts:
  - `poc/sdk_subagent_probe.py` — 5-test suite (~2 min total)
  - `poc/schema_messages_probe.py` — dumps full SDK message stream for schema queries (debugging aid for StructuredOutput contract)
