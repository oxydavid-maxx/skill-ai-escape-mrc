# 8D #2: Configured but Disconnected Features

**Date**: 2026-04-16
**Team**: 光佑 (Kuang-Yu) + Claude Code
**Status**: Analysis complete

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Data files created as standalone artifacts without corresponding consumer code. `lookups/recordings.yaml` (Apr 7) existed 10 days before `recording_discovery.py` (Apr 9, Chain 5 added Apr 17) read it. | Q2: No integration test verifies that configured data sources are actually consumed. Pipeline runs succeed with zero SharePoint results because the scan code simply didn't exist. |
| **MRC** | Q3: Config-first development pattern — config files are created as "planning artifacts" but treated as done, with no tracking of whether consumer code follows. | Q4: Silent zero-result is indistinguishable from legitimate zero-result. No observability layer distinguishes "source not scanned" from "source scanned, nothing found." |

---

## D2: Problem Definition (IS/IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Config data (`lookups/recordings.yaml`) with 3 SharePoint paths existed but no code read it. Strategy doc (`search_strategy.md`) described 7-step scan but code only implemented steps 1-4. | Not a code bug — the code that existed worked correctly. Not a missing config — the config was complete and correct. | The gap is between two correct artifacts that were never connected. |
| **WHERE** | `recording_discovery.py` Chains 1-4 (implemented Apr 9) vs Chain 5-7 (described in `search_strategy.md`, Chain 5 implemented Apr 17 only after user noticed). Same pattern in `copilot_fetch.py`: `_check_cdp_available` coexisted with `_ensure_cdp_has_copilot` across call sites. | NOT in the data fetching logic itself (Chains 1-4 work). NOT in the YAML syntax (valid, well-structured). | Both sides of the interface are individually correct but never wired together. |
| **WHEN** | 10-day gap: `recordings.yaml` committed Apr 7, `recording_discovery.py` created Apr 9 without reading it, Chain 5 added Apr 17. CDP pattern: 7-day gap between `_ensure` creation and full caller migration. | NOT a regression — the connection never existed. NOT intermittent — it was deterministically absent. | Distinguishes from "broke something that worked" — this never worked in the first place. |

---

## D4: Root Cause Analysis (Four Quadrants)

### Q1: Technical Root Cause — Non-Conformance

**Why did `recording_discovery.py` not read `recordings.yaml`?**

```
Why-1: recording_discovery.py was created (Apr 9) with Chains 1-3 only,
       treating Teams chat messages as the sole data source.
Why-2: The developer (Claude Code) treated lookups/recordings.yaml as a
       reference document, not as a runtime input — it was created in a
       separate session (Apr 7) with a different mental context.
Why-3: No import contract exists between config files and consumer modules.
       YAML files are passive — they don't error when unread.
Why-4: The development pattern is "build each piece when it comes up" rather
       than "trace the full data flow end-to-end before committing."
Why-5: There is no design document or interface spec that maps data sources
       to consumer code — each module is built in isolation.
```

**Root cause: Passive config files have no mechanism to assert they are consumed. The development process creates artifacts in isolation without end-to-end wiring verification.**

### Q2: Technical Root Cause — Non-Detection

**Why was the 10-day gap not detected?**

```
Why-1: The pipeline ran successfully every day during the gap — no errors,
       no warnings, no test failures.
Why-2: Zero recordings from SharePoint is a valid result (maybe no meetings
       that day), so the output looked normal.
Why-3: No test asserts "if recordings.yaml has entries, discover_recordings
       must attempt to read them." Tests only check functional correctness
       of existing chains.
Why-4: The search_strategy.md documented 7 steps but nothing verified the
       code implements all 7. Documentation was aspirational, not contractual.
Why-5: No observability distinguishes "scanned 0 sources" from "scanned 5
       sources, found 0 results." The output only reports what was found.
```

**Root cause: Zero-result success is indistinguishable from unconfigured-source success. No structural test verifies config-to-code completeness.**

### Q3: Management Root Cause — Non-Conformance

**Why does the development process produce disconnected artifacts?**

```
Why-1: Config files and strategy docs are created as planning/design
       artifacts, not as executable specifications.
Why-2: Sessions are context-bounded — the Apr 7 session created lookups/,
       the Apr 9 session created recording_discovery.py, neither checked
       what the other session produced.
Why-3: No cross-session checklist requires "verify all config files in
       lookups/ have corresponding consumer code."
Why-4: The wiki documents self-healing patterns but has no entry for
       "config-to-code integration verification."
Why-5: The project treats "config exists" as sufficient evidence of
       capability, creating false confidence ("we scan 3 SharePoint
       folders") when the reality is zero scanning.
```

**Root cause: Config-as-planning conflated with config-as-runtime. No process bridges the gap between "designed" and "wired."**

### Q4: Management Root Cause — Non-Detection

**Why did no process catch the false confidence?**

```
Why-1: Daily briefing output showed "0 recordings" which matched user
       expectation (not all days have recordings).
Why-2: The user trusted the configured paths were being scanned because
       the config file existed and the strategy doc described the flow.
Why-3: No "source coverage" metric reports which discovery chains actually
       executed vs which are configured.
Why-4: The existing regression tests (test_regression.py) only guard
       against known past bugs, not against incomplete integration.
Why-5: There is no periodic audit comparing search_strategy.md steps
       against actual code implementation.
```

**Root cause: False confidence from config existence. No coverage reporting reveals which configured capabilities are actually wired.**

---

## D5: Prevention Actions (One per Quadrant)

### P1 (Q1 — Wiring): Config consumer registry with import-time assertion

Every YAML file in `lookups/` must have a corresponding `_load_and_register()` call in exactly one consumer module. At import time, the consumer reads the file and registers which keys it consumes. A startup check in `main.py` verifies all `lookups/*.yaml` files have at least one registered consumer.

**Why chain**: Passive configs don't error when unread (W3) because no import contract exists (W3) because YAML files are treated as documentation (W2). An import-time registry makes configs active participants that fail loudly when orphaned.

### P2 (Q2 — Detection): Structural integration test

Add a test that parses `lookups/search_strategy.md` step references and verifies each referenced file/module has corresponding code paths. Specifically: for each `lookups/*.yaml`, assert that at least one `.py` file contains both `open(` and the yaml filename. For `search_strategy.md` steps, assert each "Step N" has a matching code comment or function.

**Why chain**: Zero-result success hides missing sources (W2) because tests only check functional output (W3) because no structural test maps config to code (W4). A structural test makes the gap a test failure, not a silent omission.

### P3 (Q3 — Process): Session handoff checklist

Add to CLAUDE.md a "cross-session integration check" rule: when creating a config/lookup file, the commit message must include `CONSUMER: <module.py>` or `CONSUMER: TODO`. Any `CONSUMER: TODO` triggers a follow-up item in the next session. When creating a consumer module, grep `lookups/` for relevant configs and verify all are loaded.

**Why chain**: Sessions are context-bounded (W2) so cross-session artifacts go unwired (W1) because no checklist bridges sessions (W3). The handoff checklist makes the gap explicit at commit time rather than discovery time.

### P4 (Q4 — Observability): Source coverage logging

Add a `[COVERAGE]` log line at pipeline end that reports: "Discovery chains executed: 4/7, SharePoint folders scanned: 0/3." This makes "configured but not scanned" visible in every run output, distinguishing it from "scanned but empty."

**Why chain**: User trusted configs were active (W2) because output only shows results not coverage (W3) because no metric reports executed-vs-configured (W3). Coverage logging converts invisible gaps into daily-visible signals.

---

## D8: Residual Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | New lookup YAML files added without consumer code, before registry is implemented | Medium | Medium | P3 (commit message convention) is manual and can be forgotten. P1 (registry) is the structural fix. |
| 2 | Strategy doc updated with new steps but structural test not updated to match | Low | Medium | Strategy doc and test must be co-edited. Could add a last-modified date comparison. |
| 3 | Pattern repeats in non-lookup contexts (e.g., prompt templates, config sections) | Medium | High | The "configured but disconnected" anti-pattern is broader than `lookups/`. Consider extending the registry pattern to all config-driven features. |
| 4 | Coverage logging shows 0/3 but gets normalized as "expected" over time | Low | Medium | Distinguish first-time-zero (warn) from repeated-zero (info). Alert on >7 consecutive days of 0/N for any source. |

---

## Timeline

| Date | Event | Commit |
|------|-------|--------|
| Apr 7 | `lookups/recordings.yaml` created with 3 SharePoint paths | 8860bc2, 2991e42 |
| Apr 9 | `recording_discovery.py` created with Chains 1-3 only | f0b7ca2 |
| Apr 9 | Chain 4 (email) added — still no recordings.yaml reader | 0ba762e |
| Apr 16 | User discovers the gap; 8D analysis initiated | — |
| Apr 17 | Chain 5 (SharePoint scan from recordings.yaml) implemented | 1bffbf7 |

**Gap duration**: 10 days (Apr 7 to Apr 17). During this period, 3 SharePoint folders were configured but never scanned, and `search_strategy.md` documented 7 steps while code implemented 4.
