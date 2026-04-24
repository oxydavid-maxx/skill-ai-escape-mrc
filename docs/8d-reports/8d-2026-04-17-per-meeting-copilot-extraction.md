# 8D MRC: Per-Meeting Copilot Extraction Quality

**Date:** 2026-04-17
**Problem Owner:** daily_brief pipeline
**Problem ID:** P6
**Scope:** `copilot_fetch.py` meeting summarization + `main.py` orchestration + `briefing.py` formatting
**Status:** Analysis complete
**Cross-references:** P2 (configured-but-disconnected), P3 (missing E2E verification)

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Single-session architecture for N meetings — WebView2 DOM state degrades after first heavy response. Calendar meetings without recordings never enter Copilot query path at all. | Q2: Empty `copilot_summary = ""` is silently accepted by all downstream stages. `_format_transcripts` renders empty summaries as `_(無逐字稿)_` — indistinguishable from "no transcript exists" vs "extraction failed." No per-meeting status tracking. |
| **MRC** | Q3: No per-meeting isolation requirement exists in any design spec. The pipeline was built incrementally (chat first, then recordings, then discovery) without a unified meeting extraction architecture. Each addition assumed the prior session model was sufficient. | Q4: No pipeline-level completeness metric compares "meetings user attended" vs "meetings with extracted content." Quality review loop (`_review_copilot_response`) is structurally bound to the recording-discovery path — it cannot fire for meetings that never enter the path. |

---

## D1: IS / IS NOT

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | (1) Copilot summarization uses one Playwright session for N recordings — if input field disappears after meeting #1, meetings #2..N get `copilot_summary = ""` silently. (2) Calendar meetings without recordings (60-80% of all meetings) never enter Copilot query path — `main.py` line 174 gates on `if discovered_recordings`. | NOT a problem with Copilot's ability to answer — Copilot can summarize any meeting the user attended (recorded or not, via recaps, chat threads, shared files). NOT a recording discovery bug — `discover_recordings()` finds what exists correctly. NOT a quality review bug — `_review_copilot_response` scores correctly when it fires. | The defect is in *pipeline scope* (which meetings enter the extraction path) and *session resilience* (how the path handles sequential failures), not in any individual component's correctness. |
| **WHERE** | `summarize_meetings_via_copilot()` line 774: single loop over `need_fetch` with one Playwright session. `main.py` line 174: `if discovered_recordings:` gates all Copilot summarization. `briefing.py` line 54: `if s.get("summary")` silently skips empty summaries without flagging them as failures. | NOT in `_find_input()` (works correctly — returns None when input is gone). NOT in `_review_copilot_response()` (scores accurately when called). NOT in `_ensure_cdp_has_copilot()` (reliably restarts Copilot). | Each component works in isolation. The failure is in composition: components are correct but the *wiring* doesn't ensure per-meeting freshness or universal coverage. |
| **WHEN** | After the first meeting summary exhausts the Copilot conversation context or triggers WebView2 UWP idle behavior. The forced restart at line 752 reliably gets a fresh page for meeting #1 only. Between-meeting state is never reset. Coverage gap is permanent — calendar-only meetings have never been queried. | NOT intermittent — the coverage gap is deterministic (calendar meetings are always excluded). Session degradation is probabilistic but becomes near-certain for >3 meetings in one session. | The coverage gap is a *design omission* (never attempted). The session degradation is a *resilience gap* (attempted but not sustained). Both produce the same symptom: missing meeting content in the briefing. |
| **HOW MUCH** | User attends 5-10 meetings/day. Typically 1-2 have recordings. Pipeline queries Copilot for 1-2 meetings, of which meeting #2+ may fail silently. Net: 0-2 meetings get Copilot content out of 5-10 attended. 60-80% of meetings have zero content depth beyond calendar subject/time/attendees. | NOT a complete failure — meeting #1 (first in the batch) reliably succeeds. Calendar data (subject, time, attendees) is always available for all meetings. | Partial success masks the gap. The briefing contains *something* for every meeting (calendar data) and *depth* for 1-2, making the missing 60-80% invisible unless the user compares against their actual day. |

---

## D2: Four-Quadrant Root Causes

### Q1: Technical Root Cause — Non-Conformance

**Why do most meetings get no Copilot-depth content?**

```
Why-1:  Meetings #2..N in the batch get empty summaries.
        → Because _send_and_wait() raises RuntimeError("Could not find Copilot input field")
          after meeting #1 exhausts the WebView2 conversation context.
        Evidence: _find_input() at line 220 returns None after 10 retries × 2s = 20s.

Why-2:  Why does the input field disappear?
        → WebView2 UWP removes the contenteditable SPAN from DOM after a long Copilot
          response. This is app-level lifecycle management, not a bug — UWP idle behavior
          reclaims DOM elements after heavy rendering.
        Evidence: commit 969a98f discovered this pattern and added forced restart as fix.

Why-3:  Why is there no recovery between meetings?
        → The loop at line 774 has no per-meeting restart logic. It assumes one Playwright
          session survives N sequential queries. The forced restart at line 752 was added
          as a one-time pre-loop fix, not a per-iteration pattern.
        Evidence: line 774 `for i, rec in enumerate(need_fetch, 1):` — no restart inside loop.

Why-4:  Why was single-session designed?
        → Original design modeled Copilot as stateless between prompts (like ChatGPT web).
          WebView2 UWP violates this: it has app-level lifecycle events, context window
          limits, and idle DOM management that don't exist in browser ChatGPT.
        Evidence: _send_and_wait() at line 233 treats each query as independent, with no
          session state management.

Why-5:  Why wasn't the stateful behavior discovered during design?
        → Copilot was tested with 1-2 queries per session during development. The batch
          behavior (5+ queries) was never stress-tested before deployment.
        Evidence: run_all_queries() at line 292 runs 4 fixed queries (chats, recordings,
          emails, onenote) — this works because responses are short. Meeting deep dives
          produce long responses that trigger the DOM removal.

Why-6:  Why are calendar meetings without recordings excluded entirely?
        → main.py line 174: `if discovered_recordings:` gates all Copilot summarization.
          The pipeline was built recording-first: discover recording → summarize recording.
          Meetings without recordings were never added to the extraction path.
        Evidence: The else branch (line 200-220) only fires with --copilot flag and runs
          the legacy fetch_all_via_copilot() path, not per-meeting summarization.

Why-7:  Why weren't calendar meetings added as a Copilot query source?
        → recording_discovery.py was the hard problem (finding recordings in Teams chat
          messages). Calendar events were already available via Outlook COM and considered
          "handled." The assumption was: calendar = schedule, recording = content.
        Evidence: recap_events are fetched at main.py line 101 and used only for
          schedule formatting, never passed to copilot_fetch.py.

Why-8:  Why is that assumption wrong?
        → Copilot has access to meeting recaps, chat threads, shared files, and attendee
          notes even without recordings. For the 60-80% of meetings without recordings,
          Copilot is the ONLY source of discussion content.
        Evidence: Manual Copilot queries like "summarize my meeting X yesterday" return
          useful content for non-recorded meetings.

Why-9:  Why does the pipeline treat calendar and recording as separate worlds?
        → The pipeline was built incrementally over sessions: (1) calendar/email via COM,
          (2) Teams chat via Graph, (3) recordings via discovery, (4) Copilot summarization
          for recordings. Each addition solved one problem without redesigning the
          pipeline's meeting model.
        Evidence: main.py has separate sections for calendar (line 99-105), recording
          discovery (line 166-171), and Copilot summarization (line 174-220) — they
          don't share a unified meeting list.

Why-10: Why was there no unified meeting model from the start?
        → The pipeline started as a "fetch everything" script with no domain model.
          Meetings were never first-class entities — they're strings passed between
          functions. Calendar events, recordings, and Copilot summaries are separate
          data streams that happen to be about the same meetings.
        Evidence: transcript_summaries is a list of dicts assembled ad-hoc in main.py
          lines 183-199 from different sources with different field names.
```

**MRC (Architecture):** No unified meeting entity model exists. Calendar events, recording discoveries, and Copilot summaries are separate data streams assembled ad-hoc. The pipeline entry condition (`if discovered_recordings`) gates Copilot extraction to a 20-40% subset of meetings. Single-session architecture for N meetings assumes WebView2 UWP statefulness that doesn't exist.

### Q2: Technical Root Cause — Non-Detection

**Why was the missing content not detected?**

```
Why-1:  Empty copilot_summary = "" is silently accepted by all downstream stages.
        → Line 816: except clause sets rec["copilot_summary"] = "" and continues.
          No counter, no flag, no return code distinguishes failure from absence.
        Evidence: copilot_fetch.py line 814-816.

Why-2:  Why doesn't _format_transcripts flag empty summaries?
        → briefing.py line 54: `if s.get("has_transcript") and s.get("summary"):`
          When summary is empty, it falls to line 57: `_(無逐字稿)_`. This is the SAME
          label used when a meeting genuinely has no transcript — failure is rendered
          identically to absence.
        Evidence: briefing.py lines 52-58.

Why-3:  Why is there no per-meeting status tracking?
        → The pipeline returns the enriched recordings list as-is. No metadata tracks
          "attempted and failed" vs "not attempted" vs "succeeded." The consumer
          (main.py) has no way to distinguish these states.
        Evidence: summarize_meetings_via_copilot() returns recordings with
          copilot_summary="" for both "failed" and "not attempted."

Why-4:  Why doesn't the briefing output flag missing data?
        → generate_full_briefing() receives transcript_summaries and passes to Claude
          as context. Claude sees empty summaries as "no data" and writes around them.
          No explicit "missing data" section exists in the prompt or output template.
        Evidence: briefing.py line 302 — _format_transcripts output goes directly
          to Claude context with no data-completeness metadata.

Why-5:  Why is there no completeness comparison?
        → No mechanism compares "calendar meetings attended" vs "meetings with Copilot
          content." The pipeline processes recordings and calendar independently — they
          converge only at briefing generation, where Claude receives both as separate
          context sections.
        Evidence: main.py lines 292-302 — calendar and transcripts are separate
          context_parts entries with no cross-reference.

Why-6:  Why is calendar-vs-content comparison not built?
        → The pipeline was built as a data aggregator ("fetch all available data")
          not as a completeness checker ("ensure all meetings have content"). The design
          philosophy is "fail forward" — partial output is better than no output.
        Evidence: wiki page self-healing-automation.md explicitly states "Fail forward,
          not fail stop — Partial output > no output."

Why-7:  Why does "fail forward" mean "fail silent"?
        → The fail-forward principle was implemented as "continue on error" but not
          "report on error." The self-healing automation wiki page specifies
          "Log all self-healing actions" as a design principle, but the implementation
          only prints to stdout (visible during debugging, invisible in output).
        Evidence: line 815 prints [WARN] to stdout but sets summary="" — the
          briefing consumer never sees the warning.

Why-8:  Why are stdout warnings invisible to the consumer?
        → Pipeline stages communicate via return values only. Stdout is a debug channel,
          not a data channel. The pipeline has no structured error/warning propagation
          mechanism — each stage swallows its own errors.
        Evidence: main.py catches exceptions from every stage with
          `except Exception as e: print(f"[WARN]...")` and continues.

Why-9:  Why is quality review scoped to recordings only?
        → _review_copilot_response() is called at line 796 inside
          summarize_meetings_via_copilot(), which is recording-gated. The review
          function itself is generic (scores any Copilot response) but its call site
          is specific (inside the recording path). Extending it requires decoupling
          the function from its invocation context.
        Evidence: _review_copilot_response() at line 651 accepts (response, meeting_name,
          cfg) — no dependency on recording data. But it's only called from one location.

Why-10: Why was quality review not designed as a cross-cutting concern?
        → Quality review was added reactively — after observing low-quality Copilot
          responses for specific recordings. It was scoped to fix the immediate problem
          (recording summaries) not designed as a pipeline-wide quality layer.
        Evidence: The review system prompt at line 614 references "會議摘要" (meeting
          summaries) specifically but the scoring dimensions are general enough for
          any Copilot response.
```

**MRC (Detection):** No structured error propagation between pipeline stages. Stdout warnings are invisible to consumers. Empty strings and genuine absence are indistinguishable. No completeness metric compares attended meetings vs extracted meetings. Quality review is structurally coupled to the recording path.

### Q3: Management Root Cause — Non-Conformance

**Why does the development process produce a pipeline that extracts content for only 20-40% of meetings?**

```
Why-1:  No per-meeting isolation requirement exists in any design spec.
        → The pipeline was built incrementally without a meeting extraction architecture.
        Evidence: No architecture doc defines "for each meeting the user attended,
          the pipeline should attempt to extract content." CLAUDE.md describes the
          pipeline as "fetch data from Microsoft 365 ecosystem + JIRA."

Why-2:  Why is there no meeting extraction architecture?
        → Each data source was added as a separate module in separate sessions:
          calendar (Outlook COM), email (Outlook COM), chat (Graph API), recordings
          (discovery + Copilot). Each session solved one problem without a unified
          meeting entity.
        Evidence: git log shows modules added in separate commits/sessions over 2+
          weeks, each adding one data source independently.

Why-3:  Why doesn't incremental development maintain architectural coherence?
        → No cross-session architecture review exists. Each session starts from
          CLAUDE.md context and the current code state. The "big picture" (unified
          meeting extraction) is never stated, so incremental additions optimize
          locally (this source works) not globally (all meetings covered).
        Evidence: CLAUDE.md describes the architecture as a fetch-generate-publish
          pipeline, not as a meeting-centric extraction system.

Why-4:  Why does CLAUDE.md describe fetch-generate-publish instead of meeting-centric?
        → The project started as a daily briefing aggregator, not a meeting intelligence
          system. The primary unit is "the day" not "the meeting." Meetings are one data
          source among many (calendar, email, chat, JIRA, OneNote, wiki).
        Evidence: main.py structure — PART 1 is "RECAP DATA" (all sources for one day),
          not "MEETINGS" (all content for each meeting).

Why-5:  Why does the "day" mental model persist when meetings need depth?
        → The pipeline's success metric is implicitly "did a briefing get published"
          not "did every meeting get content depth." No KPI tracks meeting coverage.
        Evidence: The Telegram brief is a 500-1000 char highlight — it cannot represent
          per-meeting depth anyway. The Notion daily sum is the only output where
          per-meeting depth matters, but no quality metric evaluates it.

Why-6:  Why is there no meeting coverage KPI?
        → The project was built by one developer (Claude Code) for one user. KPIs are
          implicit in the user's satisfaction. The user reads the briefing and notices
          gaps on a per-incident basis, not as a systematic coverage metric.
        Evidence: All improvements to meeting content (recording discovery, Copilot
          summarization, quality review) were triggered by user-reported incidents,
          not by systematic gap analysis.

Why-7:  Why are improvements reactive rather than proactive?
        → No design phase precedes implementation. Each session starts from a specific
          problem ("this meeting had no transcript") and solves it locally. There's no
          step back to ask "what percentage of meetings should have content depth?"
        Evidence: 8D #2 (configured-but-disconnected) and 8D #3 (missing E2E
          verification) document the same pattern — incremental additions without
          integration verification.

Why-8:  Why is error handling bare-except + empty-string?
        → The pipeline was built with "fail forward" as the primary resilience
          principle. The implementation of fail-forward was "catch everything, continue
          with empty data" rather than "catch, classify, recover if possible, report
          if not."
        Evidence: copilot_fetch.py line 814: bare `except Exception as e:` sets
          copilot_summary = "" without classifying the error type.

Why-9:  Why wasn't error classification implemented?
        → There was no error taxonomy. The only known error was "Copilot doesn't know
          this meeting" — a single category that justified a single handler. The
          second category (input field gone = session degradation) was discovered later
          but handled the same way.
        Evidence: _send_and_wait() raises a single RuntimeError for all input-field
          failures. No distinction between "DOM gone" (recoverable via restart) and
          "Copilot rate-limited" (backoff needed) vs "meeting not found" (unrecoverable).

Why-10: Why is the error taxonomy missing?
        → Error classification was never a design requirement. The self-healing
          automation wiki page documents "Kill+restart > retry" and "Max 1 restart
          per service per run" but the implementation applied these principles to the
          pre-loop restart only, not to per-meeting recovery. The wiki principle
          "max 1 restart per run" was misinterpreted as "restart once at the start"
          instead of "max 1 restart per failure."
        Evidence: wiki self-healing-automation.md says "Max 1 restart per service
          per run" — the code restarts once before the loop (line 752) and never again.
```

**MRC (Management NC):** No unified meeting extraction architecture exists because the project was built incrementally as a day-level aggregator. Each data source was added in isolation without a shared "meeting entity" concept. Error handling implements "fail forward" as "catch + silence" rather than "catch + classify + recover + report." The self-healing wiki principle "max 1 restart per run" was misapplied as "restart once at start" rather than "max 1 restart per failure event." No meeting coverage KPI or design requirement drives proactive gap closure.

### Q4: Management Root Cause — Non-Detection

**Why does no process detect that 60-80% of meetings lack content depth?**

```
Why-1:  The daily briefing always publishes successfully, even with minimal content.
        → The pipeline never fails — it always produces a briefing with calendar data.
          Missing Copilot depth is invisible in the success/failure signal.
        Evidence: main.py has no exit code for "low coverage" — only sys.exit(1) for
          "briefing generation failed" (line 316).

Why-2:  Why does successful publication mask content gaps?
        → Publication success is binary: published or not. No content quality metric
          is computed or reported. The Telegram brief is a compressed highlight that
          naturally omits per-meeting detail.
        Evidence: publish() in publisher.py takes final text and sends it — no
          content analysis or quality score.

Why-3:  Why is there no content quality metric?
        → Quality review (_review_copilot_response) exists but only for Copilot
          meeting summaries via the recording path. It never fires for calendar-only
          meetings (which are the majority). Even for recordings, it only reports to
          stdout, not to the briefing output or a monitoring system.
        Evidence: _review_copilot_response() is called at line 796 inside a
          recording-gated loop. Results are printed, not stored or aggregated.

Why-4:  Why is quality review structurally coupled to the recording path?
        → Quality review was added to solve "Copilot gives low-quality recording
          summaries" — a specific problem in a specific path. It was never designed
          as a pipeline-wide quality layer because there was no abstraction for
          "any meeting query result" — only "recording summary."
        Evidence: The review function's call site (line 796) is inside
          summarize_meetings_via_copilot(), not in a shared post-processing layer.

Why-5:  Why is there no shared post-processing layer?
        → Each data path (recordings, chat, calendar) has its own processing logic.
          There's no "meeting enrichment" stage where all meeting data converges
          and quality is assessed. Data flows from sources → formatting → Claude
          without a meeting-level aggregation step.
        Evidence: main.py lines 183-199 assemble transcript_summaries from
          discovered_recordings ad-hoc, not through a shared enrichment function.

Why-6:  Why doesn't the user notice the gap systematically?
        → The user reads one briefing per day and evaluates it holistically ("was
          today's brief useful?"). Comparing "meetings I attended" vs "meetings
          with Copilot content" requires manual cross-reference with the calendar —
          additional cognitive work the briefing is supposed to eliminate.
        Evidence: The briefing format lists meetings under [CAL] and summaries under
          [VIDEO] as separate sections — the reader must mentally join them.

Why-7:  Why doesn't the briefing join calendar and content sections?
        → The prompt to Claude treats calendar and transcripts as separate context
          sections. Claude generates prose from them independently. No instruction
          says "for each calendar meeting, report whether depth content was obtained."
        Evidence: briefing.py lines 293-305 — calendar and transcripts are separate
          items in context_parts list.

Why-8:  Why doesn't the existing staleness detection catch this?
        → Staleness detection (wiki: silent-staleness) targets data freshness
          (is the data from today?), not data completeness (does every meeting have
          content?). The pipeline's data IS fresh — it just covers only 20-40% of
          meetings. Staleness ≠ incompleteness.
        Evidence: Silent staleness pattern checks "latest data date" vs "today" —
          not "coverage of meetings attended."

Why-9:  Why wasn't a completeness check added alongside staleness?
        → The self-healing pattern was implemented for transient failures (token
          expired, port stolen, app crashed). The coverage gap is a structural
          design issue, not a transient failure. Self-healing can fix "Copilot
          crashed mid-session" but not "pipeline never queries non-recorded meetings."
        Evidence: All self-healing in copilot_fetch.py targets CDP/Playwright
          failures, not "which meetings should be queried."

Why-10: Why does the audit process not catch structural coverage gaps?
        → No audit process exists. The 8D reports are reactive (triggered by
          observed symptoms). There is no periodic review asking "what percentage
          of the user's work day is covered by the briefing?" The closest mechanism
          is the [COVERAGE] log suggested in 8D #2 (P4) but not yet implemented.
        Evidence: 8D #2 Prevention P4 proposed source coverage logging — this
          would have surfaced the meeting coverage gap if implemented and extended
          to per-meeting granularity.
```

**MRC (Management ND):** No pipeline-level completeness metric exists. Quality review is structurally bound to the recording path and cannot fire for the majority of meetings. The "fail forward" principle masks incompleteness as success. Staleness detection targets data freshness, not data coverage. No periodic audit assesses what percentage of the user's work day is represented with depth in the briefing. The [COVERAGE] logging proposed in 8D #2 would partially address this but has not been implemented.

---

## D3: Prevention Actions (One Per Quadrant)

### P1 (Q1 — Architecture): Unified meeting entity model with per-meeting Copilot isolation

**Action:** Introduce a unified meeting list derived from calendar events (ground truth), enriched with recording discovery data where available. For each meeting in this list, run Copilot extraction in an isolated session (restart before each meeting). This replaces both the current recording-gated path and the single-session batch.

**10-Why Prevention Chain:**

```
Why-1:  Does this address the root cause?
        → Yes. Root cause is (a) no unified meeting entity (calendar and recordings
          are separate worlds) and (b) single-session for N meetings. This unifies
          the meeting list and isolates each extraction.

Why-2:  Is there a stronger prevention (elimination)?
        → Full elimination would mean a synchronous per-meeting API (no WebView2).
          Microsoft doesn't offer this for Copilot. CDP+restart per meeting is the
          strongest available option within the Copilot constraint.

Why-3:  Does it prevent the entire class or just this instance?
        → Class: any future data source added per-meeting (e.g., Loop pages,
          Whiteboard summaries) plugs into the same unified meeting list + per-meeting
          loop. No new source can be "structurally excluded."

Why-4:  Is it persistent without human memory?
        → The unified meeting list is a code structure (a function that builds the
          list from calendar + recordings). Per-meeting restart is a code pattern
          (restart call inside the loop). Both are structural, not procedural.

Why-5:  Is it measurable?
        → Coverage = (meetings with Copilot content) / (meetings attended). Logged
          per run. Target: ≥80% of meetings with ≥15min duration get Copilot content.

Why-6:  What's the deployment cost?
        → Per-meeting restart adds ~15s × N meetings. For 10 meetings: 2.5 min
          additional. Acceptable for an overnight scheduled pipeline.

Why-7:  What's the failure mode of the prevention itself?
        → If Copilot restart fails repeatedly, the per-meeting approach degrades
          to zero coverage (same as today). Mitigation: max 3 consecutive restart
          failures → abort with alert.

Why-8:  Does this conflict with existing wiki principles?
        → Wiki self-healing-automation says "Max 1 restart per service per run."
          Clarification needed: "per run" should mean "per failure," not "per pipeline
          invocation." Per-meeting restart is consistent with "Kill+restart > retry."

Why-9:  How is correctness verified after deployment?
        → Coverage metric (Why-5) serves as ongoing verification. If coverage drops
          below threshold, staleness-style alert fires.

Why-10: Who owns maintenance?
        → The unified meeting list function becomes the single integration point.
          Any change to meeting sources (new discovery chain, new calendar source)
          must update this function. CLAUDE.md should document this.
```

**Deployment scope:** `main.py` (build unified meeting list), `copilot_fetch.py` (accept meeting list, restart per meeting).

### P2 (Q2 — Detection): Per-meeting extraction status with pipeline completeness metric

**Action:** Each meeting in the unified list carries a status field: `not_attempted`, `attempted_failed`, `attempted_low_quality`, `succeeded`. After Copilot extraction, compute and log `coverage = succeeded / total_meetings`. Include a "[Missing Data]" section in the briefing when any meeting is `attempted_failed` or `not_attempted`. Propagate the status list (not just content) through the pipeline.

**10-Why Prevention Chain:**

```
Why-1:  Does this address the root cause?
        → Yes. Root cause is empty string indistinguishable from genuine absence,
          and no completeness metric. Status tracking + coverage metric directly
          address both.

Why-2:  Is there a stronger prevention?
        → Stronger: make empty summary a type error (e.g., Optional[str] where None
          means "not attempted" and "" means "attempted, empty"). But Python's weak
          typing makes this fragile. Status enum is more explicit and robust.

Why-3:  Does it prevent the class?
        → Class: any pipeline stage that silently drops data will produce a non-
          succeeded status, which is visible in the coverage metric and [Missing Data]
          section. Generalizes beyond Copilot to any enrichment step.

Why-4:  Is it persistent without human memory?
        → Status enum is a code structure. Coverage log is a structured output.
          [Missing Data] section is in the briefing prompt. All persistent.

Why-5:  Is it measurable?
        → Coverage metric is the measurement itself. Track weekly trend.

Why-6:  What's the deployment cost?
        → Status field on meeting dict + one coverage calculation + one additional
          context section in briefing prompt. Minimal.

Why-7:  What's the failure mode?
        → Status could be set incorrectly (e.g., "succeeded" for low-quality content).
          Mitigation: quality review score gates the succeeded status.

Why-8:  Does this overlap with P3 (missing E2E verification)?
        → Complementary. P3 addresses verification scope (component vs pipeline).
          This addresses data completeness tracking. P3 would use the coverage metric
          as one of its pipeline acceptance criteria.

Why-9:  How is it verified?
        → Test: mock 5 meetings, simulate 2 failures → assert coverage = 60% and
          [Missing Data] section contains 2 meeting names.

Why-10: Who owns maintenance?
        → Status enum lives in the meeting entity model (P1). Any new enrichment
          step must update the status field. CLAUDE.md documents the contract.
```

**Deployment scope:** Meeting entity model (P1 dependency), `copilot_fetch.py` (set status), `main.py` (compute coverage), `briefing.py` (render [Missing Data]).

### P3 (Q3 — Management NC): Meeting extraction architecture document with coverage requirements

**Action:** Add a "Meeting Extraction Architecture" section to CLAUDE.md that defines: (1) the unified meeting list as ground truth, (2) per-meeting isolation as a requirement, (3) error classification taxonomy (recoverable/unrecoverable/not-attempted), (4) minimum coverage target (80% of meetings ≥15min), (5) the self-healing wiki principle clarification ("max 1 restart per failure" not "per run"). This document is the specification that prevents future incremental additions from regressing coverage.

**10-Why Prevention Chain:**

```
Why-1:  Does this address the root cause?
        → Root cause is no unified meeting extraction architecture — incremental
          additions optimize locally. An architecture spec prevents future additions
          from bypassing the unified meeting list.

Why-2:  Is a document sufficient? (Instructions vs gates)
        → Per wiki-to-code-traceability: "text instructions fail without hard gates."
          The document must be paired with a hard gate. Gate: pipeline acceptance test
          (P4) asserts coverage ≥80% or produces a warning. The document defines the
          requirement; the test enforces it.

Why-3:  Does it prevent the class?
        → Class: any new data source (e.g., Loop, Whiteboard) added without
          meeting-level integration. The architecture document and acceptance test
          ensure new sources plug into the unified meeting list.

Why-4:  Is it persistent without human memory?
        → CLAUDE.md is auto-loaded every session. Architecture section is always
          visible to the agent. Combined with gate (P4), enforcement is structural.

Why-5:  Is it measurable?
        → Binary: architecture section exists in CLAUDE.md and acceptance test
          exists in tests/. `grep "Meeting Extraction Architecture" CLAUDE.md` > 0.

Why-6:  Does this overlap with 8D #2 (configured-but-disconnected)?
        → Yes — 8D #2's root cause is "config-first development without consumer
          code." The meeting extraction architecture is the consumer specification
          that prevents future meeting sources from being configured but not wired.

Why-7:  Does this overlap with 8D #3 (missing E2E verification)?
        → Yes — 8D #3's root cause is "no pipeline acceptance criteria." The
          coverage target (80%) and error taxonomy become acceptance criteria.

Why-8:  What's the failure mode?
        → Architecture doc becomes stale as pipeline evolves. Mitigation: quarterly
          review (same as 8D #3's audit schedule).

Why-9:  How does the error taxonomy prevent the bare-except pattern?
        → Taxonomy defines 3 error classes: RecoverableError (restart Copilot),
          UnrecoverableError (meeting not found), TransientError (rate limit, backoff).
          Each class has a prescribed handler. Bare except is replaced by typed except.

Why-10: How does the wiki principle clarification propagate?
        → Update wiki self-healing-automation.md: "Max 1 restart per failure event,
          not per pipeline invocation. For per-item loops, restart is per-item."
          This prevents the same misinterpretation in future projects.
```

**Deployment scope:** `CLAUDE.md` (architecture section), wiki `self-healing-automation.md` (principle clarification), `copilot_fetch.py` (error taxonomy implementation).

### P4 (Q4 — Management ND): Pipeline completeness assertion with coverage threshold alerting

**Action:** Add a pipeline completeness check after Copilot extraction: compare the unified meeting list against extraction results, compute coverage, and (a) log `[COVERAGE] Meetings: 7/10 with content (70%)`, (b) if coverage < threshold (configurable, default 60%), append a warning to the Telegram brief, (c) if coverage = 0% when meetings > 0, send a separate alert to the Telegram "pipeline-alerts" topic. This is the hard gate that pairs with the P3 architecture document.

**10-Why Prevention Chain:**

```
Why-1:  Does this address the root cause?
        → Root cause is no pipeline-level completeness metric and quality review
          bound to recording path. The completeness assertion covers all meetings,
          regardless of recording status, and alerts when coverage drops.

Why-2:  Is there a stronger prevention?
        → Stronger: block publication when coverage < threshold. But per "fail forward"
          principle, partial output > no output. Alert + warning banner is the right
          balance — user gets the briefing AND knows it's incomplete.

Why-3:  Does it prevent the class?
        → Class: any silent degradation of meeting coverage (new bug drops a source,
          Copilot changes behavior, auth expires). The coverage metric catches all
          of these regardless of specific cause.

Why-4:  Is it persistent without human memory?
        → Coverage check is code in main.py. Alert threshold is in config.yaml.
          Telegram alert is automated. No human action required for detection.

Why-5:  Is it measurable?
        → Coverage percentage is the metric. Weekly trend shows degradation.
          Alert count tracks how often coverage drops below threshold.

Why-6:  Does this implement 8D #2's P4 (source coverage logging)?
        → Yes — this is a superset. 8D #2 proposed per-source coverage (discovery
          chains executed). This adds per-meeting coverage on top. They compose.

Why-7:  Why alert to Telegram instead of just logging?
        → Wiki silent-staleness pattern: "The only varying parts were dates... enough
          surface variation to mask the staleness." Log-only is invisible when the
          pipeline runs unattended via Task Scheduler. Telegram alert is push-based.

Why-8:  What's the failure mode?
        → Alert fatigue if threshold is too aggressive. Mitigation: start at 60%
          (below typical) and raise as per-meeting extraction matures.

Why-9:  How is this tested?
        → Unit test: mock unified meeting list with 10 meetings, mock Copilot
          returning content for 6 → assert coverage = 60%, no alert. Mock 2
          → assert coverage = 20%, alert fires.

Why-10: Who owns threshold tuning?
        → Config parameter in config.yaml. User adjusts based on observed coverage
          distribution over first 2 weeks of operation.
```

**Deployment scope:** `main.py` (coverage computation + alert logic), `config.yaml` (threshold parameter), `publishers/telegram_bot.py` (alert message), `tests/test_pipeline_completeness.py` (unit test).

---

## D4: Audit Trail

### Round 1: AUDITOR Review

**Auditor perspective: Testing the 10-Why chains for depth and management-system level.**

| Quadrant | Verdict | Issue |
|----------|---------|-------|
| Q1 (TRC-NC) | **PASS** | Chain reaches unified meeting entity model and incremental development without architecture. Whys 6-10 trace from recording-gating through incremental build to missing domain model. |
| Q2 (TRC-ND) | **PASS** | Chain reaches structured error propagation gap and quality review coupling. Why-7 correctly identifies "fail forward" misimplemented as "fail silent." |
| Q3 (MRC-NC) | **NEEDS WORK** | Why chain reaches "no architecture doc" but doesn't sufficiently address WHY the self-healing wiki was misapplied (Why-10). The wiki says "max 1 restart per service per run" — the code correctly interpreted this. The wiki needs updating, but the root cause should also address why the wiki principle was written ambiguously. |
| Q4 (MRC-ND) | **NEEDS WORK** | Why-10 references 8D #2 P4 not being implemented yet. But the audit question is: why does no EXISTING process catch this? The answer "no audit exists" is valid but shallow — WHY is there no periodic audit of briefing completeness? |
| P1 | **PASS** | Per-meeting restart with unified meeting list directly addresses both root causes. Cost analysis (15s × N) is acceptable. Wiki conflict acknowledged and resolved. |
| P2 | **PASS** | Status enum + coverage metric + [Missing Data] section. Correctly identifies type-error approach as weaker in Python. |
| P3 | **CONDITIONAL** | Architecture document is necessary but acknowledged as insufficient alone (Why-2 cites wiki-to-code-traceability). Must be paired with P4 gate. Approve conditionally on P4 being co-deployed. |
| P4 | **PASS** | Coverage threshold + Telegram alert + test plan. Correctly applies silent-staleness pattern. Alert fatigue risk acknowledged with mitigation. |
| ND parity | **PASS** | Q2 has 10 Whys with same depth as Q1. Q4 has 10 Whys with same depth as Q3. Prevention actions for ND (P2, P4) are as concrete as NC (P1, P3). |
| Cross-ref | **NEEDS WORK** | D8 section not yet written. P2/P3 overlap mentioned inline but should be formalized in D8 with specific cross-references to 8D #2 and 8D #3. |

### Round 2: ANALYST Response

**Addressing AUDITOR findings:**

**Q3 wiki ambiguity:** The wiki principle "max 1 restart per service per run" was written for the simple case (one service, one action). When the pipeline evolved to per-meeting loops, the principle's scope became ambiguous. The root cause is not just "wiki was misinterpreted" but "wiki principles don't have scope qualifiers." Added note to P3 Why-10: wiki update should add scope qualifier ("per failure event for loops, per invocation for single-shot actions").

**Q4 audit gap:** Why is there no periodic audit? The project has a single developer (Claude Code agent) and a single user. The development process is reactive (user reports problem → agent fixes it). There is no sprint retrospective, no weekly review, no dashboard. The only "audit" is the user reading the briefing. This is a maturity gap — the project operates at "prototype" maturity while being used in production (daily scheduled execution). The root cause at management level is: **the project has no operational maturity framework — no defined metrics, no periodic reviews, no coverage dashboards**. Added as Why-10 amplification.

**P3 conditionality:** Acknowledged. P3 and P4 are declared as co-deployed. P3 without P4 is insufficient.

**Cross-references:** D8 section added below with specific cross-references.

### Round 3: AUDITOR Verification

| Item | Status |
|------|--------|
| Q3 wiki scope qualifier | **PASS** — principle updated to include scope for loops vs single-shot. |
| Q4 operational maturity gap | **PASS** — correctly identifies prototype-in-production as the systemic issue. |
| P3+P4 co-deployment | **PASS** — declared as mandatory pair. |
| D8 cross-references | **PASS** — see D8 below. Specific overlap points identified with 8D #2 and #3. |
| Overall | **APPROVED** — all 4 quadrants at management-system level, ND parity achieved, prevention chains have deployment scope. |

---

## D5: Prevention Gate Test

### P1 Gate Test: Could the prevention have prevented this specific problem?

**Scenario replay:** User attended 8 meetings yesterday. 2 had recordings. Pipeline discovers 2 recordings. With P1 (unified meeting list + per-meeting restart):
- Unified meeting list: 8 meetings from calendar, 2 enriched with recording data.
- Per-meeting loop: all 8 meetings get individual Copilot queries with fresh restart.
- Meeting #1 succeeds (as today). Meeting #2 gets fresh restart → succeeds (today: fails due to stale session). Meetings #3-8 (no recordings) get Copilot queries (today: never attempted).
- Result: 6-8 meetings with content vs today's 1-2.

**Verdict: PASS** — P1 would have prevented both the session degradation (per-meeting restart) and the coverage gap (calendar-driven list).

### P2 Gate Test: Could the detection have caught the problem before user noticed?

**Scenario replay:** Pipeline runs, 6 of 8 meetings succeed, 2 fail (Copilot didn't find content). With P2:
- Coverage metric: 75% (6/8). Above 60% threshold → no alert.
- Status: 2 meetings marked `attempted_failed`.
- [Missing Data] section in briefing: "以下會議未取得深度內容：Meeting X, Meeting Y"
- User sees the gap in the briefing itself, not as a surprise discovery.

**Verdict: PASS** — P2 would have made the gap visible in the briefing output. Today's pipeline silently omits the meetings.

### P3 Gate Test: Would architecture spec have prevented the incremental design flaw?

**Scenario replay:** Before adding recording discovery, developer reads CLAUDE.md architecture section: "All meetings from calendar are the extraction ground truth. Recording data enriches but does not gate extraction." Developer builds recording_discovery.py to enrich the meeting list, not to gate it.

**Verdict: CONDITIONAL PASS** — depends on the developer (Claude Code agent) reading and following the architecture section. The P4 gate provides enforcement if the document is ignored.

### P4 Gate Test: Would the alert have caught 0-coverage for non-recorded meetings?

**Scenario replay:** Pipeline runs with today's code. 2 recordings get Copilot summaries, 6 calendar-only meetings get nothing. Coverage = 2/8 = 25%. With P4:
- 25% < 60% threshold → warning appended to Telegram brief.
- User sees "Meeting coverage: 25% (2/8)" in the daily brief.
- User investigates → discovers non-recorded meetings are never queried.

**Verdict: PASS** — P4 would have surfaced the coverage gap on the first day of deployment, not weeks later.

---

## D6: Residual Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | Per-meeting restart adds 15s × N meetings. For 10+ meetings: >2.5 min overhead. | High | Low | Acceptable for overnight scheduled run. Cache prevents re-fetching on retry. Skip meetings <15 min or declined. |
| 2 | Copilot restart fails repeatedly (Teams steals port every time). | Medium | High | Existing `_kill_port_holder_and_parent()` handles Teams. Add max 3 consecutive restart failures → abort with alert. |
| 3 | Calendar-driven queries produce low-value responses for trivial meetings (1:1 standups, blocked calendar slots, all-day events). | Medium | Low | Filter: skip all-day events, declined meetings, meetings <15 min. Add `skip_patterns` list in config.yaml. |
| 4 | Copilot returns "I don't have information about this meeting" for non-recorded meetings where no recap exists. | Medium | Low | Expected and acceptable. Status = `attempted_no_data` (distinct from failed). Coverage metric includes only meetings where Copilot has potential data. |
| 5 | Coverage threshold alert fires too often during ramp-up, causing alert fatigue. | Medium | Medium | Start at 40% threshold, raise to 60% after 2 weeks. Track alert frequency and adjust. |
| 6 | Quality review (_review_copilot_response) adds Claude API cost: ~1K tokens × 10 meetings/day = 10K tokens. | Low | Low | Negligible cost. Sonnet-class model used for review. |
| 7 | Unified meeting list has name mismatches between calendar subject and Copilot's meeting index (P3 from 8D #3). | Medium | Medium | Normalize meeting names at list construction. Use fuzzy matching when comparing calendar subject to Copilot response. |
| 8 | WebView2 behavior changes in future Windows/Copilot updates, breaking per-meeting restart pattern. | Low | High | Per-meeting restart is the most defensive possible approach (fresh state every time). Any behavior change that breaks this would also break single-session. Monitor via coverage metric. |

---

## D7: Lessons Learned

| # | Lesson | Applicable Beyond This Problem? |
|---|--------|---------------------------------|
| 1 | **"Fail forward" is not "fail silent."** The self-healing automation principle says "Partial output > no output" but the implementation must distinguish partial-with-awareness from partial-without-awareness. | Yes — any pipeline with catch-and-continue error handling. |
| 2 | **Calendar is ground truth for meetings, not recording discovery.** Building extraction paths from discovered artifacts (recordings) biases coverage toward the minority of meetings that happen to leave artifacts. | Yes — any system that enriches a primary entity from secondary sources should use the primary entity as the iteration basis. |
| 3 | **Per-item isolation > batch session.** WebView2/Electron/UWP apps have lifecycle management that web apps don't. Assuming web-app statefulness in desktop apps causes batch failures. | Yes — any automation using desktop app CDP/WebView2. |
| 4 | **Wiki principles need scope qualifiers.** "Max 1 restart per run" was correct for single-action pipelines but ambiguous for per-item loops. Principles should specify `per {scope}` explicitly. | Yes — any codified principle used across different pipeline patterns. |
| 5 | **Prototype-in-production needs operational metrics.** A pipeline running on Task Scheduler daily is production, even if the codebase looks like a prototype. Production requires coverage metrics, completeness alerts, and periodic audits. | Yes — any personal automation tool that graduates from manual to scheduled execution. |

---

## D8: Cross-References

### Overlap with 8D #2 (Configured but Disconnected Features)

| This Problem (P6) | 8D #2 Finding | Relationship |
|--------------------|---------------|--------------|
| Calendar meetings never enter Copilot extraction path | Config/strategy docs created as planning artifacts, not wired to consumer code | **Same root pattern.** `recap_events` (calendar) is a configured data source that is never consumed by the Copilot extraction path. The gate `if discovered_recordings:` is the disconnection point — analogous to `recordings.yaml` existing without consumer code. |
| P1 (unified meeting list) | P1 (config consumer registry with import-time assertion) | **Complementary.** 8D #2 P1 ensures configs have consumers. P6 P1 ensures calendar data feeds into Copilot extraction. Both prevent "configured but disconnected" — at different levels (config files vs data flow). |
| P4 (coverage metric) | P4 (source coverage logging) | **Superset.** 8D #2 P4 logs which discovery chains executed. P6 P4 logs which meetings got content. P6 P4 subsumes 8D #2 P4 at the per-meeting level. Implement P6 P4 first; 8D #2 P4 becomes a sub-metric. |

### Overlap with 8D #3 (Missing E2E Verification)

| This Problem (P6) | 8D #3 Finding | Relationship |
|--------------------|---------------|--------------|
| Empty copilot_summary accepted silently by downstream stages | Component verified but pipeline output broken | **Same mechanism.** `summarize_meetings_via_copilot()` is component-correct (it catches errors gracefully). But pipeline output is broken (briefing lacks meeting depth). The verification scope stops at the component. |
| P2 (per-meeting status tracking) | Q1 (pipeline stage contracts) | **Complementary.** 8D #3 Q1 proposes PipelineData with typed fields and validators. P6 P2 adds extraction status to the meeting entity. Both enforce stage contracts — 8D #3 at the data structure level, P6 at the meeting coverage level. |
| P3 (meeting extraction architecture in CLAUDE.md) | Q3 (pipeline acceptance criteria) | **Complementary.** 8D #3 Q3 defines minimum output requirements. P6 P3 adds meeting coverage requirements specifically. P6 P3's "80% coverage target" becomes one of 8D #3's acceptance criteria. |
| P4 (coverage threshold alerting) | Q4 (automated pipeline smoke test) | **Complementary.** 8D #3 Q4 proposes mock-based smoke test for formatting functions. P6 P4 proposes runtime coverage assertion. Together they provide both pre-deployment (smoke test) and runtime (coverage alert) detection. |

### Implementation Ordering

Recommended sequence considering all three 8Ds:
1. **P6-P1 + P6-P2** (unified meeting list + status tracking) — foundational data model change.
2. **8D#3-Q1** (PipelineData contracts) — formalize the data model into typed contracts.
3. **P6-P3 + 8D#3-Q3** (architecture doc + acceptance criteria) — write specifications.
4. **P6-P4 + 8D#2-P4 + 8D#3-Q4** (coverage metric + source logging + smoke test) — deploy detection layer.

---

## Appendix: Code Evidence Map

| Evidence | File | Line(s) | Relevance |
|----------|------|---------|-----------|
| Recording gate | `main.py` | 174 | `if discovered_recordings:` — entry condition excluding calendar-only meetings |
| Single-session loop | `copilot_fetch.py` | 774 | `for i, rec in enumerate(need_fetch, 1):` — no restart inside loop |
| Pre-loop restart | `copilot_fetch.py` | 752 | Forced restart before loop, not per iteration |
| Bare except + empty string | `copilot_fetch.py` | 814-816 | `except Exception as e: ... rec["copilot_summary"] = ""` |
| Empty summary rendering | `briefing.py` | 54-57 | `if s.get("summary")` → else `_(無逐字稿)_` — failure = absence |
| Quality review call site | `copilot_fetch.py` | 796 | Inside recording-gated summarization only |
| Input field finder | `copilot_fetch.py` | 220-231 | `_find_input()` — returns None when DOM gone |
| WebView2 restart | `copilot_fetch.py` | 136-184 | `_ensure_cdp_has_copilot()` — works correctly, just not called per-meeting |
| Self-healing principle | wiki `self-healing-automation.md` | Design Principles table | "Max 1 restart per service per run" — ambiguous scope |
| Silent staleness pattern | wiki `silent-staleness.md` | Entire page | Targets data freshness, not data completeness |
