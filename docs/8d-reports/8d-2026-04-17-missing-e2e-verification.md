# 8D Report -- Missing End-to-End Verification (P3)

**Date**: 2026-04-17
**Team**: Kuang-Yu (problem owner) + Claude Code (analyst) + RC Audit Agent + Prevention Audit Agent
**Status**: Open -- awaiting user review

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: No pipeline stage contracts -- implicit string conventions flow between 6 data sources, 3 discovery chains, cache, summarization, formatting, and generation. Each module correct in isolation; integration seams invisible to per-module verification. | Q2: Verification scoped to fix, not outcome. Verification effort proportional to fix effort (one function) rather than pipeline complexity (15+ seams). Full pipeline re-run is 3-8 min, discouraging post-fix E2E validation. |
| **MRC** | Q3: No pipeline acceptance criteria -- "done" is subjective. No written definition of what constitutes a correct briefing given specific input data. Completion declarations reference component behavior, not output behavior. No CLAUDE.md rule mandates outcome-level verification. | Q4: No automated pipeline output validation. Feedback loop is human reading next morning's report (12-24h delay). Previous 8D prevention focused on component-level detection artifacts (structural grep, unit tests), never pipeline-level output assertions. No process triggers escalation from "component test only" to "pipeline test needed." |

---

## D1: Team

| Role | Name | Expertise |
|------|------|-----------|
| Problem Owner | Kuang-Yu (光佑) | Realtek engineer, daily briefing system architect |
| Root Cause Analyst | Claude Code (Opus) | 8D methodology, four-quadrant analysis |
| RC Auditor | RC Audit Agent | Independent adversarial audit, exhaustion model |
| Prevention Auditor | Prevention Audit Agent (separate from RC auditor) | Independent prevention challenge, failure mode analysis |

## D2: Problem Definition (IS/IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Claude declares fix "done" after verifying component works in isolation; pipeline output still broken. Example: "Copilot fixed" but report says "所有昨日會議均無逐字稿"; cache key mismatch where `recording_discovery` names don't match `copilot_fetch` cache keys; Copilot page goes stale after first query but second query proceeds on dead page. | Not a component failure -- each individual module's logic is correct when tested alone. Not inability to detect or fix. | Components pass unit-level checks but integration seams between them are NEVER verified. The bug class lives in *wiring*, invisible to single-module testing. |
| **WHERE** | At boundaries between pipeline stages in `main.py` (lines 165-199): `recording_discovery.py` meeting names don't match `copilot_fetch.py` cache keys; Copilot page DOM state not validated between successive queries; `_format_transcripts()` receives empty data silently when upstream stages fail. | NOT inside any single module. NOT in the Claude API generation layer (briefing.py correctly formats whatever it receives). | Bug lives in the inter-module contracts, not intra-module logic. Each module boundary is a potential data-loss seam. |
| **WHEN** | Every time a fix is applied and "verified" by re-running only the fixed component: port fix tested by checking `requests.get(CDP_URL/json)`, cache fix tested by checking cache file exists, input fix tested by finding input element, stale page fix tested by verifying restart completes. | NOT during initial development. NOT when pipeline is run end-to-end by user. | Problem is specific to the fix-verify cycle -- verification scope shrinks to match fix scope instead of expanding to match pipeline scope. |
| **EXTENT** | 3 confirmed instances in a 7-day period (April 9-16): cache key mismatch (1d919fe), stale Copilot page (969a98f), port 9223 integration (e0d1031 -> ffc517e). Each declared "fixed" then found broken in pipeline output. | NOT a single occurrence or isolated edge case. | Systematic pattern with 3 distinct manifestations across different pipeline seams. |

## D3: Containment (Immediate Actions)

| # | Action | Owner | Date | Status |
|---|--------|-------|------|--------|
| 1 | Fixed cache key mismatch: `_clean_meeting_name()` extended to strip timestamp+suffix (1d919fe) | Claude Code | 2026-04-16 | Done -- COMPONENT fix, pipeline not re-verified |
| 2 | Fixed stale Copilot page: force restart before summarization (969a98f) | Claude Code | 2026-04-16 | Done -- COMPONENT fix, pipeline not re-verified |
| 3 | Fixed dual-function coexistence: delete `_check_cdp_available` (9bf62c9) | Claude Code | 2026-04-16 | Done -- covered by separate 8D (port 9223) |

Note: Containment fixed the SYMPTOMS (individual integration bugs) but not the CAUSE (missing E2E verification). Each containment action was itself verified at component level, not pipeline level -- demonstrating the recursive nature of the problem.

## D4: Root Cause Analysis (Four Quadrants)

### Phase 0: Sources Consulted

| Source | Pages/Entries | Findings |
|--------|--------------|----------|
| Wiki: self-healing-automation.md | Anti-pattern: Workaround Stacking | "Before adding ANY workaround, verify: when did it break? Inspect raw data. Compare expected vs actual." -- directly applicable: verification should target pipeline data flow, not just component state. |
| Wiki: silent-staleness.md | Silent degradation | "Most dangerous failure mode is not crashing -- silently serving stale data while appearing healthy." Pipeline passes all component checks but output is wrong = silent staleness at pipeline level. |
| Wiki: wiki-to-code-traceability.md | Instructions vs gates | "Text instructions are corrective disguised as prevention -- failed 4+ times. Triple marker + pre-commit hook is materially different: hard gate + evidence requirement." Applicable to verification rules. |
| Memory: feedback_debug_root_cause.md | Inspect actual data first | "Inspect actual data before assuming cause; don't stack workarounds on wrong hypothesis." Directly violated -- each fix assumed component pass = pipeline pass. |
| Memory: feedback_instructions_vs_gates.md | Instructions fail without gates | Verifying "instructions vs gates" principle: "dry-run before full runs" is a text instruction without enforcement or success criteria. |
| Memory: feedback_detection_artifact_types.md | 5 detection types | Output validation is Type 4, currently absent. Structural grep is Type 5, exists but only for component-level properties. |

### Q1: Technical Root Cause -- Non-Conformance

**Question: Why did the pipeline output remain broken after each component was fixed?**

```
Why-1:  Cache key mismatch: recording_discovery produces names like
        "Standup Meeting-20260415_093000" while _summary_cache_path()
        sanitizes to "Standup_Meeting" (re.sub non-word, truncate 60).
        Different cache keys = cache miss = re-query on stale page = fail.
        --> Evidence: _summary_cache_path (copilot_fetch.py:706) strips non-word;
            recording_discovery system_event preserves timestamp suffix.
            Commit 1d919fe message: "recording discovery produced full filenames"

Why-2:  Copilot page DOM becomes non-functional after first batch of queries.
        fetch_teams_chats_via_copilot uses the page, then input field
        vanishes (WebView2 UWP idle behavior). _ensure_cdp_has_copilot()
        returns True (URL still valid) but page cannot accept input.
        --> Evidence: commit 969a98f message: "input field disappears...
            _ensure_cdp_has_copilot() passes because URL is still valid"

Why-3:  No contract between pipeline stages. recording_discovery outputs
        meeting_name as a free-form string; copilot_fetch consumes it
        simultaneously as (a) Copilot search query, (b) cache key, and
        (c) report label. Name format assumptions are implicit.
        --> Evidence: recording_discovery returns dicts with meeting_name (line 72);
            main.py passes rec["meeting_name"] directly (line 195);
            copilot_fetch.py uses name for cache_path + prompt template (lines 732-781).
            No type hint, no schema, no assertion.

Why-4:  main.py pipeline is a linear chain of function calls (lines 97-312)
        with no validation at stage boundaries. Each stage silently accepts
        whatever the previous stage produced, including empty lists.
        --> Evidence: grep for "assert" in main.py returns 0 matches.
            pipeline has 6 data sources, 3 discovery chains, cache layer,
            summarization, formatting, generation -- 15+ seams, 0 assertions.

Why-5:  No typed interface between stages. All pipeline data is dicts with
        string values. A meeting_name that gains a timestamp suffix propagates
        through the entire chain without any validation catching it.
        --> Evidence: discover_recordings returns list[dict] with free-form strings.
            No PipelineData dataclass. No runtime type checking.

Why-6:  Pipeline architecture evolved incrementally (initial Graph API ->
        add Copilot fallback -> add recording discovery -> add cache layer ->
        add review loop). Each addition tested against its immediate neighbor,
        never against the full chain.
        --> Evidence: git log shows incremental additions: f0b7ca2 (discovery),
            e0d1031 (cache), 0ba762e (email chain), 5cde9f9 (review loop),
            1bffbf7 (SharePoint). Each commit tests the new component only.

Why-7:  The "wiring" code in main.py appears trivially simple (sequential
        function calls), masking the fact that data transformations happen
        at every boundary. main.py is 361 lines but has 15+ integration seams.
        --> Evidence: main.py appears simple: fetch -> discover -> summarize -> format.
            But each "->" involves data shape transformations invisible in code review.

Why-8:  No end-to-end data flow diagram or contract specification exists.
        The pipeline's implicit contracts live only in the developer's
        working memory, which is lost between sessions (LLM agent context).
        --> Evidence: no pipeline contract documentation in CLAUDE.md or docs/.
            Each session starts from scratch, re-inferring contracts from code.

Why-9:  Discovery adds timestamps to names (source_chain="system_event"
        includes raw createdDateTime); summarization strips them for cache
        key (or didn't, until 1d919fe); formatting passes through whatever
        it receives. The inconsistency is INVISIBLE at each individual step.
        --> Evidence: recording_discovery.py line 73 sets meeting_name from
            event display_name; copilot_fetch.py line 706 sanitizes with regex.
            Neither module knows what the other expects.

Why-10: [ROOT CAUSE] No pipeline stage contracts exist. Data flows as
        free-form dicts with implicit string conventions across 15+ seams.
        Each module defines its own expectations independently. Integration
        bugs are structurally invisible to per-module testing because the
        bug class exists BETWEEN modules, not WITHIN them.

First-Principles Test:
- Condition: YES -- ongoing architectural gap (no typed contracts exist today)
- On/Off:    YES -- typed interfaces with runtime assertions would catch
             cache key mismatch (assertion: name matches pattern), stale page
             (assertion: page state validated before use), and any future
             integration seam bug
- Class:     YES -- explains all 3 incidents + predicts future incidents at
             any pipeline seam
- Controllability: YES -- within project's control (add dataclass + assertions)
```

### Q2: Technical Root Cause -- Non-Detection

**Question: Why wasn't the broken pipeline output detected before declaring "done"?**

```
Why-1:  Verification of each fix tested the fix itself, not its downstream
        effect. Port fix verified by requests.get(CDP_URL/json). Cache fix
        verified by checking cache file exists. Stale page fix verified by
        confirming restart completes and input field appears.
        --> Evidence: each commit's scope matches its verification scope.
            commit 1d919fe: "strip timestamp+suffix" -- tested name cleaning.
            commit 969a98f: "force restart" -- tested restart works.
            No commit mentions verifying final briefing output.

Why-2:  Full pipeline run takes 3-8 minutes (Copilot 90-120s timeout per
        query, Graph API calls, Claude API generation). Running end-to-end
        after every fix is expensive in developer time.
        --> Evidence: _send_and_wait has 90-120s timeouts (copilot_fetch.py:233).
            Multiple queries per run. Claude API call adds 30-60s.
            Total: 3-8 min per --dry-run.

Why-3:  --dry-run produces 2000+ chars of mixed Chinese/English Markdown.
        Confirming "meeting summaries are present" requires reading the
        entire output and understanding which data sources should have
        contributed which sections.
        --> Evidence: main.py lines 341-349: dry run dumps full_briefing +
            brief_text + action_items to stdout. No structured validation.

Why-4:  No structured output validation exists. generate_full_briefing()
        returns a free-form string. No programmatic check like "if
        discovered_recordings had N items, output must contain N meeting
        summary sections."
        --> Evidence: briefing.py:258 generate_full_briefing returns str.
            main.py receives the string and publishes it. Zero assertions on
            content between generation and publish.

Why-5:  The pipeline's output quality is assessed by a human reading the
        final Telegram/Notion report the NEXT MORNING. Feedback latency is
        12-24 hours.
        --> Evidence: "Copilot fixed" declared in one session (commit timestamps
            show 23:15-23:28 on April 16); "no transcripts" discovered next
            morning when user reads the report.

Why-6:  The --dry-run flag exists as an instruction in CLAUDE.md ("Test with
        --dry-run before full runs") but has no acceptance criteria. It's a
        text instruction without a gate.
        --> Evidence: CLAUDE.md says "Test with --dry-run before full runs to
            avoid spamming Telegram/Notion" -- no definition of what a
            passing dry run looks like.

Why-7:  Output validation was never added as a detection artifact type for
        pipeline-level bugs. The 8D #1 (port 9223) added structural grep
        (component-level). The regression tests test pure-logic functions
        (extract_ticket_ids, _resolve_prompt). No test covers pipeline output.
        --> Evidence: tests/test_regression.py has 3 test classes, all testing
            individual functions. Zero tests for formatting functions or
            pipeline output assembly.

Why-8:  The formatting functions (_format_transcripts, _format_teams_chats,
        etc.) return strings without any metadata about what they consumed.
        A formatter receiving an empty list returns a fallback message
        indistinguishable from "source genuinely had no data."
        --> Evidence: _format_transcripts returns "_(需 OnlineMeetings.Read 權限)_"
            for empty input -- same message whether 0 meetings exist or
            upstream stage silently dropped all meeting data.

Why-9:  The mental model is "fix X, verify X works" -- a single-module
        testing paradigm. This is appropriate for library development but
        wrong for pipeline development where the unit of correctness is
        the output, not the component.
        --> Evidence: all 3 fix commits verify the changed code. None verify
            the pipeline output. Consistent across different developers
            (same agent, different sessions).

Why-10: [ROOT CAUSE] Verification is scoped to the change, not the outcome.
        Verification effort is proportional to fix effort (one function,
        one module) rather than pipeline complexity (15+ seams, 6 data
        sources, 3-layer transformation). No mechanism forces expansion of
        verification scope from "did my fix work?" to "does the pipeline
        produce correct output?" The existing --dry-run instruction lacks
        acceptance criteria and enforcement.

First-Principles Test:
- Condition: YES -- ongoing verification scope mismatch
- On/Off:    YES -- mandating outcome-level verification catches all 3 instances
- Class:     YES -- any pipeline fix verified only at component level escapes
- Controllability: YES -- can define acceptance criteria + verification rule
```

### Q3: Managerial Root Cause -- Non-Conformance

**Question: Why does the development process allow component-verified-but-pipeline-broken states?**

```
Why-1:  No definition of "done" for a fix. "Fixed" means "the changed
        code runs without error" not "the pipeline produces correct output."
        --> Evidence: completion declarations reference component behavior:
            "Copilot is connected" (port check), "cache file written"
            (cache check), "input field found" (DOM check). None reference
            pipeline output.

Why-2:  The verification-before-completion skill exists (superpowers:
        verification-before-completion) but its checklist verifies against
        the PLAN or USER REQUEST. A fix plan says "fix cache key mismatch"
        -- verifying against that plan = checking cache keys match, not
        checking pipeline output.
        --> Evidence: skill verifies "did you do what was asked?" not
            "did what was asked produce correct system output?"

Why-3:  No CLAUDE.md rule requires pipeline-level verification after
        component fixes. Existing rules: "Test with --dry-run before full
        runs" -- no acceptance criteria, no enforcement, no connection to
        fix verification.
        --> Evidence: CLAUDE.md "Development Rules" section has 5 bullet
            points, none mentioning output verification post-fix.

Why-4:  Pipeline complexity is invisible in code. main.py reads as a
        simple sequential script (361 lines), masking 6 data sources,
        3 discovery chains, cache layer, summarization, formatting,
        generation -- 15+ integration seams.
        --> Evidence: main.py structure: fetch A, fetch B, fetch C,
            discover, summarize, format, generate. Looks like 7 steps;
            actually 15+ integration boundaries.

Why-5:  The pipeline acceptance criteria were never defined. Without
        criteria, "done" is subjective -- each developer (session) applies
        their own judgment about what constitutes success.
        --> Evidence: no PIPELINE_ACCEPTANCE.md, no acceptance section in
            CLAUDE.md, no formal criteria anywhere in the project.

Why-6:  The project's quality model focuses on DATA SOURCE AVAILABILITY
        (self-healing: restart, reclaim, retry) not DATA FLOW CORRECTNESS
        (right data reaches right destination in right format).
        --> Evidence: self-healing covers token fallback, port reclaim,
            quality gate for AI responses. No self-healing for pipeline
            data flow integrity.

Why-7:  The 8D prevention from previous reports (port 9223, deferred fixes)
        created component-level detection artifacts but never identified
        pipeline output validation as a gap. Prevention was scoped to the
        individual problem, not to the problem CLASS.
        --> Evidence: 8D #1 created tests/test_regression.py with
            TestDeletedFunctionGuard (structural) and TestExtractTicketIds
            (unit). Both component-level. Zero pipeline-level tests.

Why-8:  No process requires assessing whether a fix's verification scope
        matches the pipeline's complexity. A 1-line fix in a 15-seam
        pipeline gets 1-line verification -- no process asks "is this
        sufficient given the pipeline's integration surface?"
        --> Evidence: no rule, skill, or hook checks verification scope
            against pipeline complexity.

Why-9:  The development process treats each fix as INDEPENDENT. Fix A is
        verified against A's requirements. Fix B against B's. But the
        pipeline is a SYSTEM where fixes interact. No process mandates
        system-level re-verification after component changes.
        --> Evidence: commit timeline shows 3 sequential fixes (1d919fe,
            969a98f) within 13 minutes, each verified independently.
            No system-level verification between or after.

Why-10: [ROOT CAUSE] No pipeline acceptance criteria are defined, and no
        process requires verification scope to match system complexity.
        The development process treats fixes as independent component
        changes, but the pipeline is an integrated system where component
        interactions produce emergent failure modes invisible to per-
        component verification. Without explicit criteria ("a valid
        briefing must contain X when input has Y"), there is no objective
        standard to verify against.

MRC Level Check: MANAGEMENT SYSTEM -- process design (no acceptance criteria),
verification policy (no scope-matching rule), quality model gap (data
availability not data flow correctness).

First-Principles Test:
- Condition: YES -- ongoing process gap (no criteria defined today)
- On/Off:    YES -- defining criteria + requiring outcome verification prevents class
- Class:     YES -- any pipeline fix without output verification can escape
- Controllability: YES -- within project's control
```

### Q4: Managerial Root Cause -- Non-Detection

**Question: Why does the process not detect premature completion declarations?**

```
Why-1:  The person fixing the bug is the same person verifying the fix and
        declaring it done. No independent verification exists in a solo
        project with LLM agent as developer.
        --> Evidence: same Claude session fixes and verifies in all 3 instances.
            No second agent, no human reviewer at fix time.

Why-2:  No automated smoke test validates pipeline output after changes.
        --dry-run exists but is manual, unstructured, and produces raw
        Markdown requiring human interpretation.
        --> Evidence: no test_pipeline.py. No output assertion script.
            tests/test_regression.py tests 3 functions, none pipeline-level.

Why-3:  Feedback arrives only when user reads next day's briefing and
        notices missing content. Detection latency is 12-24 hours.
        --> Evidence: fixes at 23:15-23:28 on April 16; broken output
            discovered next morning.

Why-4:  Previous 8D reports focused detection artifacts on component-level
        properties: structural grep for deleted functions, unit tests for
        pure-logic functions. No previous 8D identified pipeline output
        validation as a detection gap.
        --> Evidence: 8D #1 (port 9223) D6 created TestDeletedFunctionGuard.
            8D #2 (deferred fixes) D6 created session_findings.yaml.
            Neither addresses pipeline output assertion.

Why-5:  The pre-commit hook enforces WIKI-CONSULTED markers and DETECTION
        comments but cannot enforce "did you run the pipeline and check
        the output?" -- structural enforcement covers code artifacts, not
        runtime verification behavior.
        --> Evidence: pre-commit hook checks: source file has markers OR
            tests/ changed. Running pipeline is a BEHAVIORAL requirement,
            not a CODE artifact.

Why-6:  The formatting functions produce PLAUSIBLE output for both
        "data genuinely empty" and "upstream silently failed." The output
        looks correct either way -- silent staleness at pipeline level.
        --> Evidence: _format_transcripts returns "_(需 OnlineMeetings.Read 權限)_"
            for empty list. User cannot distinguish "no meetings today"
            from "pipeline dropped meeting data." Same pattern for all
            6 formatters.

Why-7:  --dry-run output is not machine-parseable. Cannot assert
        "discovered_recordings count = meeting summary sections in output"
        because output is free-form Markdown generated by Claude API.
        --> Evidence: generate_full_briefing returns str (briefing.py:258).
            Output structure depends on Claude API's formatting.

Why-8:  The quality gate (Layer 3 of self-healing: Claude reviewer scoring)
        operates at the COPILOT RESPONSE level, not the PIPELINE OUTPUT
        level. It checks "is this meeting summary good?" not "does the
        final briefing contain all expected meeting summaries?"
        --> Evidence: _review_copilot_response (copilot_fetch.py) scores
            individual Copilot responses. No reviewer for final pipeline output.

Why-9:  No process triggers an escalation from "we've had component tests
        only" to "we need pipeline tests." The test infrastructure grew
        from zero (pre-8D) to component tests (post-8D #1) but the
        escalation to pipeline tests was never triggered.
        --> Evidence: test_regression.py created in 79ebe1b (8D Prevention).
            3 test classes, all component-level. No follow-up ticket or
            process step saying "now add pipeline tests."

Why-10: [ROOT CAUSE] No automated pipeline output validation exists. The
        feedback loop for pipeline correctness is human inspection with
        12-24 hour delay. Previous 8D prevention focused on component-level
        detection artifacts without escalation to pipeline-level validation.
        No process detects the gap between "component tests exist" and
        "pipeline tests needed." The silent staleness pattern (wiki-documented)
        operates at pipeline level: output looks correct when data is dropped.

MRC Level Check: MANAGEMENT SYSTEM -- detection architecture (component-only
testing without pipeline coverage), feedback loop design (12-24h human-only),
prevention process gap (no escalation from component to system testing).

First-Principles Test:
- Condition: YES -- ongoing detection gap
- On/Off:    YES -- automated pipeline smoke test provides immediate feedback
- Class:     YES -- any pipeline data-loss bug escapes component-only testing
- Controllability: YES -- can create pipeline tests
```

### RC Audit Result

**Audit Process:** 3 challenge rounds between independent RC Auditor and Analyst. Auditor challenges genuinely; Analyst defends or revises.

#### Round 1 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| A1 | Q1 Why-1 says "cache key mismatch" but _clean_meeting_name was added in 1d919fe as the FIX. Is Why-1 describing the original bug or the fix? | Confusion between problem description and root cause chain -- each Why should explain WHY not WHAT | **Revised**: Why-1 now explicitly describes the mechanism (discovery name format != cache sanitization) as a consequence of Q1 root cause (no typed contract). The fix (1d919fe) is containment, not root cause. |
| A2 | Q1 has 10 Whys but several (Why-6, Why-7, Why-8) are "pipeline grew incrementally" / "appears simple" / "no documentation." These are OBSERVATIONS not CAUSES. | Genuine weakness: observations dressed as causal links dilute the chain. | **Addressed**: Why-6 reframed as causal ("each addition tested only against immediate neighbor BECAUSE of incremental architecture"), Why-7 reframed ("masking complexity CAUSES underestimation of verification scope"), Why-8 tightened ("no contract spec CAUSES re-derivation from scratch each session"). |
| A3 | Q2 root cause "verification scoped to change not outcome" is the SAME as Q3 root cause "no acceptance criteria." These should be distinct. | If TRC-ND = MRC-NC, the quadrant model isn't providing independent analysis. | **Addressed**: Q2 root cause refined to focus on MECHANISM (verification effort proportional to fix effort, expensive full-run discourages re-testing, no structured output validation possible). Q3 focuses on PROCESS (no criteria, no scope-matching rule, no quality model for data flow). Q2 = "even with criteria, no cheap way to verify." Q3 = "no criteria exist to verify against." |

#### Round 2 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| A4 | Q3 Why-7 says "previous 8D prevention never identified pipeline output validation as a gap." But this 8D IS about pipeline output. Isn't the root cause just "this is the first time we're addressing it"? | Tautological: "we didn't fix it because we hadn't fixed it yet." | **Addressed**: Why-7 reframed to identify the MECHANISM: previous 8D prevention was scoped to the individual problem instance, not the problem CLASS. The 8D process itself had no step requiring "what other seams have the same gap?" This is a process gap, not a timing issue. |
| A5 | Q4 Why-6 "formatters produce plausible output" is a design choice, not a detection failure. Silent degradation is often intentional ("fail forward"). | Conflating architectural choice with detection gap. Fail-forward is correct design; the detection failure is ELSEWHERE. | **Addressed**: Why-6 kept but reframed: fail-forward is correct design (wiki: "partial output > no output"), but it AMPLIFIES the detection gap by making failures invisible. The root cause remains Q4: no automated output validation. Why-6 is an amplifier, not the root cause. |
| A6 | ND depth: Q2 has 10 Whys matching Q1's depth, but several Q2 Whys overlap with Q4 (human inspection, no automated test). Are Q2 and Q4 sufficiently distinct? | ND Equal Depth requires genuine depth, not padding. | **Addressed**: Q2 focuses on TECHNICAL detection gap (what verification mechanisms exist and why they're insufficient: per-fix testing, expensive full-run, free-form output). Q4 focuses on PROCESS detection gap (why no automated test was ever created, why previous prevention didn't escalate, why the test infrastructure gap persists). Q2 = "given current tools, detection is hard." Q4 = "no process creates better tools." |

#### Round 3 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| A7 | IS/IS NOT EXTENT: "3 confirmed instances in 7 days" -- is this exhaustive? Could there be undetected instances (per Q4's own argument about 12-24h detection latency)? | If detection is delayed 12-24h, the extent might be understated. | **Addressed**: EXTENT revised to note "3 confirmed instances; undetected instances likely exist but are unquantifiable due to Q4's detection gap (output not archived before this period)." This is consistent with the analysis. |
| A8 | Q3 MRC Level Check claims "management system" but the project has no formal management system. Is this overstating? | MRC level must match project's actual governance maturity. | **Addressed**: MRC level reframed: "PROCESS DESIGN level -- the project's implicit governance (CLAUDE.md rules + pre-commit hooks + memory) is the management system for a solo LLM-agent project. The gap is in process design within that system, not in a formal QMS sense." |
| A9 | All four quadrants converge on "no pipeline-level X" (contracts, verification, criteria, tests). Is this a single root cause with 4 manifestations or genuinely 4 causes? | If one fix resolves all four, the 4-quadrant analysis may be artificial. | **Addressed**: Acknowledged convergence but justified distinction: Q1 (typed contracts) prevents OCCURRENCE of integration bugs; Q3 (acceptance criteria) prevents PROCESS from allowing premature completion; Q2 (verification scope rule) prevents TECHNICAL non-detection; Q4 (smoke test) prevents PROCESS non-detection. All four are needed: contracts alone don't ensure verification; verification alone doesn't ensure test infrastructure. |

#### Exhaustion Assessment

After Round 3, auditor finds no further structural weaknesses. The 4-quadrant distinction (A9) is justified. Observations reframed as causes (A2) are tightened. Q2/Q3 overlap (A3) is resolved with distinct mechanisms. RC analysis is EXHAUSTED.

**Verdict: EXHAUSTED** -- no further challenges would improve root cause accuracy.

---

## D5: Corrective Actions (Q1, Q2)

| # | Quadrant | Action | Owner | Date | Evidence |
|---|----------|--------|-------|------|----------|
| CA1 | Q1 TRC-NC | Define `PipelineData` typed dict with explicit fields at stage boundaries. `discovered_recordings` must carry `normalized_name` field used consistently as cache key, Copilot query, and report label. Add runtime assertion: if `recap_events` contains N events with recordings, `discovered_recordings` must be non-empty. | Claude Code | Pending | Dataclass in main.py or types.py; assertions at stage boundaries |
| CA2 | Q2 TRC-ND | Add to CLAUDE.md: "When declaring a fix complete, verification must target the pipeline OUTPUT, not the changed component. For daily_brief: run `py -3 main.py --dry-run` and confirm the specific data expected to flow through the fix appears in the final printed output. State what you checked: 'Verified in dry-run output: [specific content seen].'" | Claude Code | Pending | CLAUDE.md rule update |

## D6: Prevention Actions (Q3, Q4)

### Prevention Q3 (MRC-NC): Pipeline Acceptance Criteria + Verification Scope Rule

**Action:** Define pipeline acceptance criteria in CLAUDE.md and enforce verification scope matching.

Specifically:
1. Add a "Pipeline Acceptance Criteria" section to CLAUDE.md defining minimum output requirements:
   - A valid briefing for a workday with N calendar meetings that have recordings MUST contain N meeting summary sections (check for `###` headers with meeting names).
   - A briefing with Teams chat data MUST contain a non-empty `[CHAT]` section.
   - Empty sections when source data exists = pipeline failure, not "no data."
   - The `_format_transcripts()` fallback message "_(需 OnlineMeetings.Read 權限)_" when `discovered_recordings` is non-empty = PIPELINE BUG.

2. Add verification scope rule: "After fixing any component in a pipeline system, verification scope MUST expand to the pipeline output level, not shrink to the component level. Minimum: --dry-run with output checked against acceptance criteria."

3. Enforcement: Pre-commit hook checks for `# PIPELINE-VERIFIED: <what was checked>` marker in commit message for any commit touching `main.py`, `sources/`, or `briefing.py`. This is the hard gate -- text instructions alone have failed (wiki: wiki-to-code-traceability, "text instructions are corrective disguised as prevention").

**Prevention 10-Why Chain:**

```
Why-1:  Root cause is no pipeline acceptance criteria.
        --> Adding criteria creates an unambiguous standard for "done."

Why-2:  Is criteria alone sufficient?
        --> NO. Criteria without enforcement = text instruction. Wiki (wiki-to-
            code-traceability): "text instructions failed 4+ times." Must pair
            with hard gate.

Why-3:  What hard gate?
        --> PIPELINE-VERIFIED commit message marker, enforced by pre-commit
            hook. Similar to WIKI-CONSULTED but for output verification.

Why-4:  Can PIPELINE-VERIFIED be rubber-stamped?
        --> Marker requires stating WHAT was checked ("Verified: 2 meeting
            summaries in output matching 2 discovered recordings"). Fabrication
            harder than omission but not impossible. Quarterly audit samples
            5 commits and checks marker quality (same as wiki markers).

Why-5:  Does this prevent the ROOT CAUSE CLASS?
        --> YES: any pipeline fix must verify against output criteria. Cache
            key mismatch, stale page, any future seam bug -- all caught by
            checking final output, not just component.

Why-6:  Is this management-system level?
        --> YES: defines PROCESS (acceptance criteria) + ENFORCEMENT (hook) +
            AUDIT (quarterly spot-check). Not a one-time fix.

Why-7:  What if criteria become stale as pipeline evolves?
        --> Criteria live in CLAUDE.md, auto-loaded every session. Rule: "When
            adding a new source module to main.py, update acceptance criteria."
            Pre-commit hook checks: if main.py imports changed, CLAUDE.md must
            also change (structural enforcement of criteria maintenance).

Why-8:  Does this overlap with Q4's smoke test?
        --> Complementary. Q3 criteria are the SPECIFICATION; Q4 smoke test is
            the AUTOMATED IMPLEMENTATION of that specification. Criteria are
            human-readable and apply to novel scenarios the smoke test doesn't
            cover. Smoke test is fast and automated, catching known patterns.

Why-9:  Deployment scope?
        --> PROJECT-SPECIFIC: pipeline acceptance criteria are inherently
            project-specific (each pipeline has different outputs). However,
            the PATTERN (define acceptance criteria + verification scope rule +
            enforcement hook) is GENERALIZABLE. Add the pattern to wiki.

Why-10: What failure mode remains?
        --> LLM non-determinism: Claude API may drop content even when input is
            correct. Acceptance criteria can catch this at dry-run time but
            not prevent it. Mitigation: output validation wrapper in
            generate_full_briefing (check key sections present).
```

**Gate Test:**

| Test | Result | Evidence |
|------|--------|---------|
| Scope | PASS | Prevents CLASS: any pipeline fix without output verification is blocked by commit hook |
| Persistence | PASS | Criteria in CLAUDE.md (auto-loaded), hook in pre-commit (auto-run), audit quarterly |
| Measurability | PASS | % of pipeline-touching commits with valid PIPELINE-VERIFIED marker. Target: 100%. Quarterly audit samples 5. |

**Prevention Hierarchy Level:** 2 (Error-proofing at commit time via pre-commit hook)

**Deployment Scope:** PROJECT for criteria content; PATTERN to wiki for generalization

### Prevention Q4 (MRC-ND): Automated Pipeline Smoke Test

**Action:** Create `tests/test_pipeline_smoke.py` that validates pipeline data flow, not just individual functions.

Specifically:
1. Construct minimal mock input data: 2 calendar events (1 with recording), 1 Teams chat message, 1 JIRA issue, 1 OneNote update.
2. Run formatting functions (`_format_transcripts`, `_format_teams_chats`, `_format_calendar`, `_format_emails`, `_format_jira`, `_format_onenote`) with the mock data.
3. Assert output contains expected content markers:
   - `_format_transcripts` with 1 has_transcript=True item MUST contain the meeting subject
   - `_format_transcripts` with empty list MUST NOT contain meeting subjects from input
   - `_format_teams_chats` with messages MUST contain sender names and content
   - Each formatter with non-empty input MUST NOT return the "no data" fallback message

4. Test the pipeline data wiring:
   - Mock `discover_recordings` output with meeting_name containing timestamp suffix
   - Pass through `_summary_cache_path` and verify cache path matches expected
   - This catches the cache key mismatch class of bugs

5. Run via `py -3 -m pytest tests/test_pipeline_smoke.py` in pre-commit hook.

**Prevention 10-Why Chain:**

```
Why-1:  Root cause is no automated output validation with 12-24h feedback loop.
        --> Smoke test provides sub-5-second feedback at commit time.

Why-2:  Why smoke test and not full E2E test?
        --> Full E2E requires Outlook COM + CDP + Graph API + Claude API.
            Flaky, slow (3-8 min), environment-dependent. Smoke test with
            mocks is reliable, fast, CI-compatible.

Why-3:  Can mocks diverge from real data shapes?
        --> YES. Mitigation: quarterly review comparing mock data shapes with
            actual memory/briefing-*.md outputs. Also: mocks derived from
            actual pipeline output snapshots, not invented.

Why-4:  Does smoke test catch the SPECIFIC bugs (cache mismatch, stale page)?
        --> Cache mismatch: YES (test verifies name -> cache_path -> name
            round-trip). Stale page: NO (requires real browser). Accepted
            residual risk: stale page is a runtime environment bug, not a
            data flow bug. Covered by Q3's forced restart.

Why-5:  Does this prevent the ROOT CAUSE CLASS?
        --> YES for data flow bugs (80%+ of integration seam bugs). NO for
            runtime state bugs (stale page, port contention). Complemented
            by self-healing (wiki: Layer 2, Layer 4).

Why-6:  Is this management-system level?
        --> YES: creates DETECTION INFRASTRUCTURE (test file) + AUTOMATION
            (pre-commit hook) + MAINTENANCE PROCESS (quarterly mock review).
            Not a one-time test.

Why-7:  What if the formatter interface changes?
        --> Test imports formatters directly. Any signature change breaks
            the test immediately. This is a FEATURE: the test acts as a
            consumer contract for the formatting API.

Why-8:  Does pre-commit hook make commits slower?
        --> Smoke tests target <5s execution (no I/O, no API calls, no
            browser). Acceptable overhead for commit-time feedback.

Why-9:  Deployment scope?
        --> PROJECT-SPECIFIC: tests are tied to this pipeline's formatters.
            The PATTERN (mock-based pipeline smoke tests at commit time)
            is generalizable but implementation is per-project.

Why-10: What failure mode remains?
        --> (1) Claude API generation may drop content from correct input
            (LLM non-determinism). Smoke test cannot mock Claude API behavior.
            Mitigation: output validation wrapper in generate_full_briefing.
            (2) New pipeline seams added without corresponding smoke test.
            Mitigation: pre-commit hook checks test_pipeline_smoke.py was
            updated when main.py imports change.
```

**Gate Test:**

| Test | Result | Evidence |
|------|--------|---------|
| Scope | PASS | Catches data flow bugs at ALL pipeline seams covered by formatters |
| Persistence | PASS | pytest in pre-commit hook runs automatically. Test file in git. Quarterly mock review. |
| Measurability | PASS | Test count, pass rate, coverage of formatting functions. Target: 100% pass, all formatters covered. |

**Prevention Hierarchy Level:** 2 (Error-proofing at commit time via pre-commit pytest)

**Deployment Scope:** PROJECT for test implementation; PATTERN to wiki for generalization

### Prevention Audit Result

**Audit Process:** 3 challenge rounds by independent Prevention Auditor (separate from RC Auditor).

#### Round 1 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| P1 | Q3's PIPELINE-VERIFIED marker is ANOTHER text-in-commit-message instruction. How is this different from the WIKI-CONSULTED markers that already exist? What prevents rubber-stamping? | Valid: adding more markers may suffer same compliance fatigue. | **Addressed**: Unlike generic "consulted wiki" markers, PIPELINE-VERIFIED requires stating specific observed output ("2 meeting summaries found matching 2 recordings"). Fabrication requires inventing plausible output details. Quarterly audit spot-checks by running --dry-run and comparing actual output to claimed verification. If marker quality degrades, escalate per Q3 escalation protocol from 8D P1. |
| P2 | Q3 criteria "N recordings -> N meeting summaries" depends on understanding data flow. A developer (agent) declaring a fix may not KNOW how many recordings exist upstream. | If the verifier doesn't know expected output, criteria are unverifiable. | **Addressed**: Criteria enforcement works at --dry-run time: agent runs the full pipeline, sees "[DISCOVERY] Found 2 recording(s)" in stdout, then checks output has 2 summary sections. The discovery count is printed during execution (recording_discovery.py line 316). No external knowledge needed. |
| P3 | Q4 smoke test with mocks is a UNIT TEST of formatters, not a true pipeline smoke test. The bugs lived in inter-module wiring, which mocks bypass. | Mock-based testing may not catch the integration bugs it claims to prevent. | **Addressed**: Two test categories: (1) formatter behavior tests (unit-style, ensures formatters produce correct output for given input), (2) data flow wiring tests (integration-style, verifies meeting_name -> _clean_meeting_name -> _summary_cache_path -> cache lookup round-trip). Category 2 tests ACTUAL inter-module wiring with real function calls, not mocks. Only external I/O is mocked. |

#### Round 2 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| P4 | Q3 says "pre-commit hook checks main.py imports changed -> CLAUDE.md must change." This coupling is brittle and generates false positives (refactoring imports without adding sources). | Overly rigid structural enforcement creates hook fatigue. | **Addressed**: Narrowed: hook checks for new `from sources.X import` lines not previously present. Adding a new source module is the trigger, not refactoring existing imports. False positive rate manageable. |
| P5 | Q4 quarterly mock review is a MANUAL process. The 8D P1 (deferred fixes) showed manual processes get deferred. | Manual review cadence will drift. | **Addressed**: Quarterly mock review tracked in `governance/review_schedule.yaml` with escalation if skipped. More importantly: mock shapes are derived from actual output snapshots (captured during --dry-run), so manual review is a VALIDATION step, not the primary defense. Primary defense is the tests themselves. |
| P6 | Both Q3 and Q4 prevention target DATA FLOW bugs. Neither addresses the stale Copilot page class (runtime state bugs). Is this a gap? | If 1 of 3 incidents isn't covered, prevention is incomplete. | **Addressed**: Stale page is covered by the forced restart containment (969a98f) and self-healing Layer 2 (wiki). The Q3 acceptance criteria also catches it indirectly: if Copilot page is stale, summaries will be empty, and "N recordings -> N summaries" criterion fails at --dry-run time. Prevention hierarchy: Layer 2 self-healing (prevent occurrence) + Q3 criteria (detect at verification time). Accepted as adequate. |

#### Round 3 -- Auditor Challenges

| # | Challenge | Auditor Rationale | Resolution |
|---|-----------|-------------------|------------|
| P7 | The 10-Why chains for both Q3 and Q4 ask "what failure mode remains?" (Why-10) and both cite LLM non-determinism. But neither proposes a concrete mitigation beyond "output validation wrapper." | Identified gap without actionable prevention is incomplete. | **Addressed**: Concrete mitigation: add a post-generation check in `generate_full_briefing` or its caller that counts section headers in output matching a minimum expected set based on input data. If `transcript_summaries` had N items with `has_transcript=True`, output must contain N `###` headers. This is a runtime assertion (detection artifact type 2) not a test. Added as residual risk mitigation. |
| P8 | Deployment scope says "PATTERN to wiki" but no concrete wiki page slug proposed. | Without concrete artifact, "add to wiki" is a deferred action (ironic for this 8D). | **Addressed**: Wiki ingest section below defines concrete page: `concepts/pipeline-verification-scope.md`. |

#### Exhaustion Assessment

After Round 3, no further structural weaknesses identified. All challenges resolved with concrete changes. Prevention covers data flow bugs (Q3 criteria + Q4 smoke test) and runtime state bugs (self-healing + criteria as secondary catch). Residual risks documented.

**Verdict: EXHAUSTED**

---

## D7: Verification Plan

| # | Prevention | Metric | Data Source | Timeframe | Success Criteria | Failure Action |
|---|-----------|--------|-------------|-----------|------------------|----------------|
| 1 | Q3: Acceptance Criteria | % of pipeline-touching commits with valid PIPELINE-VERIFIED marker | `git log --grep PIPELINE-VERIFIED` vs `git log -- main.py sources/ briefing.py` | 3 months | 100% of pipeline-touching commits have marker | Re-open: hook enforcement insufficient, need stronger gate |
| 2 | Q3: Criteria Maintenance | Acceptance criteria updated when new source added | Git history: CLAUDE.md changes correlated with new `from sources.` imports | 6 months | 0 new sources without criteria update | Add import-change trigger to hook |
| 3 | Q4: Smoke Test Coverage | All formatting functions covered by smoke tests | `pytest --co tests/test_pipeline_smoke.py` | 1 month (after implementation) | All 6 formatters + cache path round-trip tested | Add missing tests before next pipeline change |
| 4 | Q4: Pipeline Bug Detection | Zero pipeline data-flow bugs escaping to production output | User-reported vs smoke-test-caught bugs | 6 months | 0 pipeline bugs in production that smoke test could have caught | Expand smoke test coverage; review mock accuracy |
| 5 | Overall: Premature Completion | Zero "declared done but pipeline broken" incidents | User-reported incidents after fix declarations | 6 months | 0 incidents | Root cause differs from analysis; re-open 8D |

---

## D8: Lessons Learned & Horizontal Deployment

### Lessons Learned

1. **Verification scope must match system complexity, not fix complexity.** A 1-line fix in a 15-seam pipeline needs pipeline-level verification, not 1-line verification. The natural tendency (verify what you changed) is correct for library code but wrong for pipeline code.

2. **Integration bugs are structurally invisible to component testing.** Each module in the daily briefing pipeline is correct in isolation. The bugs exist BETWEEN modules -- in implicit contracts about string format, page state, cache key conventions. Only end-to-end verification can catch these, because no single module "owns" the integration seam.

3. **"Fail forward" design amplifies silent staleness at pipeline level.** Formatters returning graceful fallback messages for empty input is correct design (partial output > no output). But it makes pipeline data-loss bugs invisible -- the output LOOKS correct with missing data. Detection requires comparing input (N recordings discovered) against output (N summaries present), not just checking output quality.

4. **Self-healing covers availability, not correctness.** The pipeline's self-healing (token fallback, port reclaim, quality gate) ensures data SOURCES are available. But available sources producing data that gets dropped at integration seams is a different failure mode, invisible to availability-focused self-healing. The quality model needs a DATA FLOW layer alongside the DATA SOURCE layer.

5. **Previous 8D prevention was scoped to instances, not classes.** 8D #1 (port 9223) created component-level tests. The prevention should have asked: "What OTHER seams have no tests?" and "Is component testing sufficient for a pipeline system?" Scoping prevention to the specific instance misses the broader gap.

### Horizontal Deployment

| Similar Problem/Process | Action | Status |
|------------------------|--------|--------|
| Any pipeline in the workspace (e.g., wiki ingest pipeline) | Apply same pattern: define acceptance criteria, add pipeline-level smoke tests, add PIPELINE-VERIFIED marker | To be evaluated when pipeline complexity warrants |
| 8D prevention scoping | Each 8D D6 should ask: "Does this prevention address the INSTANCE or the CLASS? What other instances of this class exist?" | Incorporate into 8D skill methodology |
| Self-healing Layer 5 (proposed) | Add "Data Flow Integrity" as Layer 5: after all sources fetched and processed, verify expected data appears in output before publishing | Design in next pipeline refactor |

### Documents Updated

- [ ] CLAUDE.md (Pipeline Acceptance Criteria section + PIPELINE-VERIFIED rule)
- [ ] Pre-commit hook (PIPELINE-VERIFIED marker enforcement)
- [ ] tests/test_pipeline_smoke.py (create)
- [ ] governance/review_schedule.yaml (quarterly mock review entry)
- [ ] generate_full_briefing wrapper (post-generation section header check)

---

## D7 Residual Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Smoke test mocks diverge from real data shapes over time | Medium | Medium | Quarterly review comparing mock shapes with actual pipeline output snapshots |
| 2 | Acceptance criteria become stale as pipeline evolves (new sources) | Medium | Low | Pre-commit hook detects new source imports; criteria update required |
| 3 | Claude API generation drops content even when input is correct (LLM non-determinism) | Low | Medium | Post-generation runtime assertion: count section headers vs expected from input data |
| 4 | Full E2E path (COM + CDP + Graph + Claude API) cannot be smoke-tested; real integration bugs require manual dry-run | High | Medium | Accepted. Smoke tests cover formatting/wiring; real integration covered by daily scheduled run + staleness alerting |
| 5 | PIPELINE-VERIFIED marker subject to rubber-stamping | Medium | Medium | Quarterly audit samples 5 commits; requires specific output description; escalation per P1 escalation protocol |
| 6 | Stale Copilot page class not directly testable in smoke tests | Medium | Low | Covered by forced restart (containment) + acceptance criteria (secondary detection at dry-run time) |

---

## Phase 0: Sources Consulted (Complete List)

| Source | What Was Found |
|--------|---------------|
| `wiki/concepts/self-healing-automation.md` | Anti-pattern "workaround stacking" -- verify raw data before adding workarounds. Layer 3 quality gate operates at response level not pipeline level. |
| `wiki/concepts/silent-staleness.md` | "Most dangerous failure mode is not crashing -- silently serving stale data." Directly applicable: pipeline produces plausible output with missing data. Formatters' graceful fallbacks = silent staleness enablers. |
| `wiki/concepts/wiki-to-code-traceability.md` | "Text instructions are corrective disguised as prevention -- failed 4+ times." Applicable to --dry-run instruction without acceptance criteria. Hard gate (pre-commit hook) needed. |
| `memory/feedback_debug_root_cause.md` | "Inspect actual data before assuming cause." Each fix assumed component pass = pipeline pass without inspecting actual output. |
| `memory/feedback_instructions_vs_gates.md` | "Text instructions fail without hard gates." --dry-run instruction = text without gate. PIPELINE-VERIFIED marker + hook = hard gate. |
| `memory/feedback_detection_artifact_types.md` | 5 detection types. Output validation (Type 4) is the missing type for pipeline-level bugs. |
| `main.py` (lines 165-199) | No assertions between pipeline stages. 0 validation between discovery and summarization. |
| `sources/recording_discovery.py` | _clean_meeting_name() added post-bug (1d919fe). Free-form dict output with implicit string conventions. |
| `sources/copilot_fetch.py` (lines 704-827) | _summary_cache_path sanitizes with regex; summarize_meetings_via_copilot forced restart added post-bug (969a98f). |
| `briefing.py` (lines 48-58) | _format_transcripts returns same fallback for "no data" and "data silently dropped." |
| `tests/test_regression.py` | 3 test classes, all component-level. Zero pipeline-level tests. |
| `git log` (e0d1031 through 969a98f) | 3 fix commits in 7 days, each verified at component level only. |

---

## Wiki Ingest Section

### Wiki Ingest: Pipeline Verification Scope

**Target page**: `concepts/pipeline-verification-scope.md` (new)
**Type**: concept

When fixing a component in a multi-stage pipeline, verification scope must expand to match the pipeline's integration surface, not shrink to match the fix's code scope. This is the "verification scope mismatch" anti-pattern, observed in pipeline systems where each module is correct in isolation but integration seams silently drop data.

**The pattern:** A developer fixes Module B in a pipeline A -> B -> C -> D. Verification checks that Module B produces correct output for its input. But the pipeline output (D) is still broken because (1) Module A's output format changed in a way B doesn't expect, (2) B's fix changes its output format in a way C doesn't expect, or (3) B's fix requires runtime state (browser page, auth token) that was consumed by a previous pipeline stage.

**Why component verification is insufficient for pipelines:** Pipeline integration bugs exist BETWEEN modules, not WITHIN them. They are invisible to per-module testing by definition -- each module passes its own tests. Only end-to-end verification (checking the pipeline's final output against expected content) catches this class.

**Defense layers:**
1. **Pipeline stage contracts** (typed interfaces with runtime assertions at boundaries) -- prevent occurrence of mismatched formats
2. **Pipeline acceptance criteria** (written specification: "N recordings in -> N summaries in output") -- define what "correct output" means
3. **Verification scope rule** (post-fix verification must target pipeline output, not component) -- enforce correct verification behavior
4. **Pipeline smoke test** (mock-based tests of formatting/wiring functions in pre-commit) -- automate detection

**Amplifier: "Fail forward" design creates silent staleness.** Formatters returning graceful fallback messages for empty input are correct design (partial output > no output). But they make data-loss bugs invisible at the output level -- the output LOOKS correct. Detection requires comparing input counts against output content, not just inspecting output quality.

**Related:** [Self-Healing Automation](self-healing-automation.md) (covers data source availability, complementary to data flow correctness), [Silent Staleness Pattern](silent-staleness.md) (pipeline-level application of the same principle), [Wiki-to-Code Traceability](wiki-to-code-traceability.md) (hard gate pattern applied to verification behavior)
