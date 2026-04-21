# OAuth + Claude Agent SDK Feasibility Report — POC Results

**Date:** 2026-04-22
**Purpose:** Verify whether interpretation I1 (LangGraph Python + Claude Agent SDK subagents, Max OAuth, no API key) is viable for skill-8d-mrc before committing to a full rewrite.
**POC script:** `poc/sdk_subagent_probe.py`
**SDK version:** `claude-agent-sdk==0.1.63`

## Verdict

**Interpretation I1 is VIABLE.** All 5 POC tests pass. Proceed to spec → plan → implementation.

## Results

| # | Test | Status | Elapsed | Notes |
|---|------|--------|---------|-------|
| 1 | Auth via Max OAuth (no ANTHROPIC_API_KEY) | PASS | 13.8s | `setting_sources=None` + OAuth, returns "OK" |
| 2 | Narrow-scope vs drift | PASS | 13.8s | Open-ended question → 3 clean bullets, no agent-mode drift |
| 3 | Simple json_schema | PASS | 18.4s | `{"keywords":["pipeline","subprocess","hangs"]}` |
| 4 | Complex nested IS/IS NOT json_schema | PASS | 59.6s | Full 4-dimension × 3-field shape populated correctly |
| 5 | 4 parallel queries via `asyncio.gather` | PASS | 35.5s | ~4× parallelism vs serial (~140s) |

## Key Findings

### 1. OAuth works without ANTHROPIC_API_KEY
Ran with `ANTHROPIC_API_KEY` unset. SDK picked up Claude Max OAuth automatically via the claude CLI subprocess it spawns. No credential plumbing required.

### 2. SDK is a thin wrapper around claude CLI subprocess
`ClaudeAgentOptions.output_format={"type":"json_schema","schema":...}` translates to the `--json-schema <json>` CLI flag. **This means the SDK inherits claude CLI's subprocess characteristics**, but with structured message stream instead of ad-hoc stdout parsing. That structure is what made yesterday's CLI flakiness invisible — we were reading raw stdout; SDK gives us typed messages.

### 3. Schema enforcement arrives as a `StructuredOutput` tool_use
When `output_format=json_schema`, the model emits:
```python
AssistantMessage(content=[ToolUseBlock(name='StructuredOutput', input={...})])
```
**Not** on `ResultMessage.structured_output` (which was `None` in every test). Parser must look for `ToolUseBlock` with `name == "StructuredOutput"` and read `.input`. This is an undocumented but stable contract — same name across all schema calls in the POC.

### 4. `max_turns` must be ≥ 2 when using schema
Schema enforcement triggers a two-turn cycle: turn 1 = `StructuredOutput` tool_use, turn 2 = tool_result. `max_turns=1` cuts off mid-cycle and returns `is_error=True` with `"Reached maximum number of turns (1)"`. Use `max_turns=3` for safety margin.

### 5. `setting_sources=None` does NOT suppress SessionStart hook bleed
Observed in `ResultMessage.usage`: `cache_creation_input_tokens: 23015`. That 23K token cache = user `CLAUDE.md` + project context + superpowers SessionStart hook all loaded. **However, narrow `system_prompt` kept output on-topic despite the context pollution** (test 2). This is different from CLI's drift-to-agent-mode failure — the model stayed narrow because it had a clear schema/instruction target.

Practical implication: auto-memory still loads, but doesn't cause drift if the system_prompt is narrow. For cost optimization later, look into disabling SessionStart hooks via env (e.g., `ENV_CLEAN = {"CLAUDECODE": "", "DISABLE_SUPERPOWERS_SESSION_START": "1"}` — not verified in POC).

### 6. `env={"CLAUDECODE": ""}` did not cause nested-session rejection
Despite `CLAUDECODE=1` being the parent's env, overriding to empty string was accepted and the session completed. Issue #573 workaround confirmed working for this SDK version.

### 7. Parallelism via `asyncio.gather` delivers real speedup
4 concurrent queries completed in 35s vs projected ~140s serial. 4× parallelism achieved without any manual process management — each query's CLI subprocess runs independently.

## Timing Projection for Full Pipeline

Based on POC latencies:

| Phase | Calls | Pattern | Projected |
|-------|-------|---------|-----------|
| 0 — research (9 websearches) | 9 | parallel | ~60s |
| 1 — IS/IS NOT (1 nested schema) | 1 | serial | ~60s |
| 2 — 4× Why chains, 10 whys each | 40 | 4 parallel × 10 serial | ~150s |
| 3 — RC audit × 3 rounds | ~12 | serial | ~180s |
| 4 — 8 actions | 8 | parallel | ~60s |
| 5 — prevention audit × 3 rounds | ~12 | serial | ~180s |
| 6 — verification plan | 4 | parallel | ~30s |
| 7 — report rendering | 1 | serial | ~60s |
| **Total estimate** | | | **~13 min** |

Well under the 20-min user target. Headroom absorbs variance.

## Risks / Open Questions (defer to spec)

1. **Auto-memory cost:** 23K cached tokens × N calls adds real $. If bills matter, investigate suppressing SessionStart injection.
2. **CLI exit flakiness on schema queries:** we observed "Command failed with exit code 1" on `max_turns=1` tests but NOT on `max_turns=3` tests. Need to verify under load whether this re-appears.
3. **Rate limit:** `RateLimitInfo(status='allowed', rate_limit_type='five_hour', overage_status='rejected')` — we are inside five-hour window; pipeline burst must not exceed it. Measure actual usage in a full run.
4. **StructuredOutput parsing contract:** undocumented. Add defensive parsing — if future SDK version renames the tool, pipeline breaks silently. Wrap in a helper with logging.
5. **setting_sources=None incomplete isolation:** narrow prompts stayed on-topic despite context bleed, but for non-narrow prompts (e.g., "generate the 8D report markdown") this may need revisiting.

## Next Step

Proceed to write spec at `docs/superpowers/specs/2026-04-22-skill-8d-mrc-nested-session-design.md` covering:
- Architecture: LangGraph state + SDK-based node callables replacing `anthropic_client.py`
- `sdk_client.py` helper wrapping `query()` with StructuredOutput parsing + retry
- Phase-by-phase migration of existing nodes to SDK calls
- Parallelism: `asyncio.gather` at phase 2 / 4 / 6
- Checkpointer stays (SqliteSaver unchanged)
- Testing: mock SDK `query()` via AsyncIterator of synthetic messages
- Rollout: flag-gated (env var `USE_SDK=1` toggles between SDK and legacy CLI subprocess) for safe A/B
