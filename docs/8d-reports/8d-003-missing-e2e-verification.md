# 8D #3: Missing End-to-End Verification

**Date**: 2026-04-16
**Team**: Claude Code (Opus)
**Problem class**: Premature completion declaration -- component-level fix verified but pipeline-level output not checked

---

## D2: Problem Definition (IS/IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Claude declares fix "done" after verifying a component works in isolation; pipeline output still broken (e.g., "Copilot fixed" but report says "所有昨日會議均無逐字稿") | Not a component failure -- each piece works when tested alone | Components pass unit-level checks but the integration seam between them is never verified |
| **WHERE** | At the boundary between data fetch and data assembly: `recording_discovery.py` meeting names do not match `copilot_fetch.py` cache keys; Copilot page goes stale after first query but second query proceeds on dead page | NOT inside any single module -- each module's logic is correct | The bug lives in the *wiring* between modules, invisible to single-module testing |
| **WHEN** | Every time a fix is applied and "verified" by re-running the fixed component only (port fix tested by checking CDP connection, cache tested by reading cache file, input fix tested by finding input element) | NOT during initial development -- problem is specific to the fix-verify cycle | Verification scope shrinks to match the fix scope instead of expanding to match the pipeline scope |

## D4: Root Cause Analysis (Four Quadrants)

### Q1: Technical Root Cause -- Non-Conformance

**Why did the pipeline output remain broken after each component was fixed?**

Why-1: Meeting summary cache uses `_summary_cache_path(meeting_name, date)` which sanitizes the name via regex. The `recording_discovery.py` produces names like "Standup Meeting-20260415_093000" while `main.py` line 194 passes `rec["meeting_name"]` directly. Cache key derived from discovery name differs from the name Copilot actually indexes the meeting under.
--> Evidence: `_summary_cache_path` strips non-word chars, truncates to 60 chars; meeting name from system_event contains timestamp suffix

Why-2: The Copilot page state is not validated between successive queries. After `fetch_teams_chats_via_copilot` uses the page, the DOM becomes stale (input field disappears, page context lost). `summarize_meetings_via_copilot` proceeds on the same browser context.
--> Evidence: commit 969a98f added forced restart specifically because stale page was discovered

Why-3: No contract exists between pipeline stages. `recording_discovery` outputs `meeting_name` as a free-form string; `copilot_fetch` consumes it as a Copilot search query AND a cache key. Name format assumptions are implicit.
--> Evidence: no schema, type hint, or assertion on meeting_name format

Why-4: Pipeline is a linear chain of function calls in `main.py` with no integration-level assertions. Each stage silently accepts whatever the previous stage produced.
--> Evidence: main.py lines 174-199 -- no validation between discovery and summarization

**Why-5 (Root):** No end-to-end output assertion exists. The pipeline has no mechanism to verify that data flowing through fetch -> discover -> summarize -> format -> generate actually produces the expected final content. Each stage is tested in isolation but the pipeline is tested only by human inspection of the final output.

### Q2: Technical Root Cause -- Non-Detection

**Why wasn't the broken pipeline output detected before declaring "done"?**

Why-1: Verification of a fix tests the fix itself, not its downstream effect. Port fix verified by `requests.get(CDP_URL/json)`. Cache fix verified by checking cache file exists. Input fix verified by finding the input element.
--> Evidence: each commit's test was scoped to the changed code

Why-2: The pipeline takes 3-8 minutes to run end-to-end (Copilot queries, Graph API calls, Claude API generation). Re-running the full pipeline after every fix is expensive and slow.
--> Evidence: `_send_and_wait` has 90-120s timeouts per query, multiple queries per run

Why-3: `--dry-run` prints the final output to stdout, but output is 2000+ chars of Chinese/English mixed text. Confirming "meeting summaries are present" requires reading the entire output and understanding the data provenance.
--> Evidence: main.py lines 341-349 -- dry run dumps full text

Why-4: No structured output validation exists. The pipeline produces free-form Markdown; there is no programmatic check like "if recap_events had N meetings with recordings, final output must contain N meeting summary sections."
--> Evidence: `generate_full_briefing` returns a string, not a structured object

**Why-5 (Root):** Verification is scoped to the change, not the outcome. The mental model is "fix X, verify X works" rather than "fix X, verify the pipeline output is correct." This is a systematic pattern: verification effort is proportional to fix effort, not to pipeline complexity.

### Q3: Managerial Root Cause -- Non-Conformance

**Why does the development process allow component-verified-but-pipeline-broken states?**

Why-1: No definition of "done" exists for a fix. "Fixed" means "the changed code runs without error," not "the pipeline produces correct output."
--> Evidence: completion declarations reference component behavior ("Copilot is connected," "cache file written") not pipeline behavior ("briefing contains meeting summaries")

Why-2: The verification-before-completion skill (`superpowers:verification-before-completion`) is available but was not invoked for these fixes.
--> Evidence: no evidence of structured verification in commit messages

Why-3: No CLAUDE.md rule requires pipeline-level verification after component fixes. The existing rules cover `--dry-run` for testing but don't define what constitutes a passing dry run.
--> Evidence: CLAUDE.md says "Test with --dry-run before full runs" -- no acceptance criteria

Why-4: Pipeline complexity is invisible. `main.py` reads as a simple sequential script, masking the fact that it has 6 data sources, 3 discovery chains, a cache layer, a summarization layer, a formatting layer, and a generation layer -- 15+ integration seams.
--> Evidence: main.py is 360 lines, appears simple

**Why-5 (Root):** No pipeline acceptance criteria are defined. Without explicit criteria ("a valid briefing must contain X when input contains Y"), there is no objective standard against which to verify. Completion is declared based on subjective judgment ("looks like it worked") rather than measurable outcome.

### Q4: Managerial Root Cause -- Non-Detection

**Why does the process not detect premature completion declarations?**

Why-1: The person fixing the bug is the same person verifying the fix and declaring it done. No independent verification exists.
--> Evidence: solo project, same Claude session fixes and verifies

Why-2: No automated smoke test validates the pipeline output after changes. The `--dry-run` flag exists but is manual and unstructured.
--> Evidence: no test_pipeline.py, no output validation script

Why-3: Feedback arrives only when the user reads the next day's briefing and notices missing content. Latency between fix and detection is 12-24 hours.
--> Evidence: "Copilot fixed" declared in one session, "no transcripts in report" discovered next morning

Why-4: Previous 8D reports (8D #1, #2) focused on detection artifacts for component-level bugs but did not address pipeline-level output validation.
--> Evidence: 8D #1 prevention creates tests for function binding, not pipeline correctness

**Why-5 (Root):** No automated pipeline smoke test exists that runs after code changes and asserts "given these inputs, the pipeline produces output containing expected sections." The feedback loop is human inspection with 12-24 hour delay.

---

## D6: Prevention Actions (One Per Quadrant)

### Q1 Prevention: Pipeline Stage Contracts

**Action:** Add a `PipelineData` dataclass or typed dict with explicit fields and validators at each stage boundary in `main.py`. Specifically: `discovered_recordings` must carry a `normalized_name` field used consistently as cache key, Copilot query term, and report label. Assert non-empty when source data indicates recordings exist.

**Why chain (5 whys):**
1. Root cause is implicit contracts between stages (free-form strings, no schema). Typed contracts make assumptions explicit and machine-checkable.
2. Stronger alternative (Level 1 -- eliminate)? Could merge discovery+summarization into one function, but separation is correct architecture; the boundary just needs a contract.
3. Prevents the class? Yes -- any new pipeline stage must conform to typed interface; implicit wiring bugs become type errors or assertion failures.
4. Persistent? Dataclass definitions live in code; assertions run every execution. No human memory needed.
5. Measurable? `grep -c "assert.*pipeline\|PipelineData" main.py sources/*.py` -- must be non-zero.

### Q2 Prevention: Outcome-Scoped Verification Rule

**Action:** Add to CLAUDE.md: "When declaring a fix complete, verification must target the pipeline *output*, not the changed component. For daily_brief, this means: run `py -3 main.py --dry-run` and confirm the specific data expected to flow through the fix appears in the final printed output. State what you checked."

**Why chain (5 whys):**
1. Root cause is verification scoped to fix, not outcome. This rule redefines verification scope.
2. Stronger? Automated E2E test (Q4 prevention) is stronger but takes time to build; this rule is immediately deployable and works even for novel bug types.
3. Prevents the class? Yes -- any fix must be verified at output level, not component level.
4. Persistent? CLAUDE.md is auto-loaded every session. Rule applies to Claude Code agent behavior directly.
5. Measurable? Completion declarations must include "Verified in dry-run output: [specific content seen]."

### Q3 Prevention: Pipeline Acceptance Criteria

**Action:** Add a `PIPELINE_ACCEPTANCE.md` or section in CLAUDE.md defining minimum output requirements: "A valid briefing for a workday with N calendar meetings that have recordings MUST contain N meeting summary sections in the `[VIDEO]` block. A briefing with Teams chat data MUST contain a non-empty `[CHAT]` section. Empty sections when source data exists = pipeline failure, not 'no data.'"

**Why chain (5 whys):**
1. Root cause is no objective "done" criteria. Written acceptance criteria create an unambiguous standard.
2. Stronger? Codified as assertions (Q1) is stronger; written criteria are the specification that assertions implement.
3. Prevents the class? Yes -- any future fix is verified against criteria, not subjective judgment.
4. Persistent? Lives in CLAUDE.md, auto-loaded. Updated when pipeline changes.
5. Measurable? Checklist format: each criterion is binary pass/fail.

### Q4 Prevention: Automated Pipeline Smoke Test

**Action:** Create `tests/test_pipeline_smoke.py` that: (1) constructs minimal mock input data (2 calendar events, 1 with recording, 1 Teams chat message, 1 JIRA issue), (2) runs the formatting functions (`_format_transcripts`, `_format_teams_chats`, etc.), (3) asserts output contains expected content markers. Run via `py -3 -m pytest tests/test_pipeline_smoke.py` in pre-commit hook.

**Why chain (5 whys):**
1. Root cause is no automated output validation with 12-24h feedback delay. Smoke test provides immediate feedback.
2. Stronger? Full E2E with real APIs would catch more but is flaky and slow. Mock-based smoke test is reliable and fast (<5s).
3. Prevents the class? Yes -- any formatting/wiring bug that drops data from output will fail the smoke test.
4. Persistent? pytest in pre-commit hook, runs automatically. No human memory needed.
5. Measurable? Test count, pass rate, coverage of formatting functions.

---

## D7: Residual Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Smoke test uses mocks that diverge from real data shapes over time | Medium | Medium | Quarterly review: compare mock shapes with actual `memory/briefing-*.md` outputs |
| 2 | Acceptance criteria become stale as pipeline evolves (new sources added) | Medium | Low | Update criteria whenever a new source module is added to main.py |
| 3 | Claude API generation layer may drop content even when input is correct (LLM non-determinism) | Low | Medium | Output validation in `generate_full_briefing` wrapper: assert key sections present in response |
| 4 | Full E2E path (COM + CDP + Graph + Claude API) cannot be smoke-tested; real integration bugs still require manual dry-run | High | Medium | Accepted constraint. Smoke tests cover formatting/wiring; real integration tested via daily scheduled run with staleness alerting |
| 5 | CLAUDE.md verification rule depends on agent compliance, no hard gate for "did you actually check the output" | Medium | Medium | Pair with Q4 automated test as hard gate; CLAUDE.md rule covers novel cases the test doesn't |

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: No pipeline stage contracts -- free-form strings flow between stages with implicit assumptions about format and naming. Cache key mismatch and stale page state are symptoms of missing interface contracts. | Q2: Verification scoped to fix, not outcome. Each component tested in isolation; no one checks if the fix actually produces correct pipeline output. Expensive full-run discourages re-testing. |
| **MRC** | Q3: No pipeline acceptance criteria -- "done" is subjective. No written definition of what a correct briefing looks like given specific inputs. Completion declared based on component behavior, not output behavior. | Q4: No automated pipeline smoke test. Feedback loop is human reading next morning's report (12-24h delay). Previous 8D prevention focused on component tests, not pipeline output validation. |
