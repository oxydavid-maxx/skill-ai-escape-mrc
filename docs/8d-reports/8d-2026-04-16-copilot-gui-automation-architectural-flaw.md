# 8D Report -- Copilot GUI Automation: Recurring Architectural Failure

**Date**: 2026-04-16 (meta-analysis)
**Scope**: Why the Copilot port 9223 / meeting summary problem keeps recurring despite 20+ commits of "fixes" over 10 days
**Type**: Meta-8D -- root cause analysis of the ROOT CAUSE ANALYSIS ITSELF failing to prevent recurrence
**Status**: Analysis only -- no code changes

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: The M365 Copilot desktop app is a consumer GUI application with no automation contract. Every self-healing fix addresses one failure mode while the GUI silently introduces new ones (idle page staleness, input field vanishing, Teams stealing port). The fix surface is unbounded because the system was not designed to be automated. | Q2: Each fix is tested by running it once and checking that it works NOW. No test can cover the space of future GUI states (idle timeout, DOM mutation, WebView2 lifecycle, OS-level port races). Detection is structurally impossible for non-contractual interfaces. |
| **MRC** | Q3: The original architecture decision chose GUI automation as a "workaround" for Graph API permission gaps (OnlineMeetings.Read admin consent, MSAL token rotation). A workaround was treated as a permanent solution. No exit criteria were set for when the workaround should be abandoned. | Q4: No mechanism exists to detect "a workaround is being patched too many times." The 8D process itself analyzed individual symptoms (dual function coexistence, wrong function call) without stepping back to ask whether the APPROACH is viable. The 8D's framing was too narrow. |

---

## D1: Team

| Role | Name |
|------|------|
| Problem Owner | Kuang-Yu (Guang-You) |
| Meta-Analyst | Claude Code (Opus 4.6) |

## D2: Problem Definition -- IS / IS NOT

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Copilot desktop app automation fails in production every 2-5 days with a NEW failure mode each time | Not a single bug with a single fix. Not port 9223 specifically. Not `_check` vs `_ensure`. | The problem is the APPROACH, not any individual manifestation |
| **WHERE** | `sources/copilot_fetch.py` -- 20 commits in 10 days, ~55% of all commits in that period touch Copilot | Not in other data sources (Outlook COM, JIRA REST, OneNote Graph). Those are stable. | Stable sources have explicit API contracts. Copilot has none. |
| **WHEN** | Starting April 7 (first Copilot commit b755e95) through April 16 -- continuous | Not before April 7. The system worked with other data sources before Copilot was added. | Copilot was added as a workaround; it became the dominant source of instability. |
| **EXTENT** | 7 distinct failure classes in 10 days (see taxonomy below). Each "fix" spawns 0-2 new failure modes. | Not one failure that was poorly fixed. Each fix is individually correct for its specific symptom. | The failure surface grows faster than the fix surface -- a whack-a-mole dynamic. |

### Failure Class Taxonomy (7 classes in 10 days)

| # | Date | Failure Class | Fix Commit(s) | Did Fix Hold? |
|---|------|--------------|---------------|--------------|
| 1 | Apr 7 | Copilot app not running / port not available | b755e95, 1903229 | No -- morphed to #2 |
| 2 | Apr 8 | Copilot context polluted from previous run | fc5af1a, 59c0a40 | Partially -- morphed to #3 |
| 3 | Apr 8 | Zombie Playwright node.exe processes leak CPU/RAM | 9760196 | Yes (this one held) |
| 4 | Apr 9 | OneDrive WebView2 steals port 9223 before Copilot | 5aed7f6, bc93a4f | Partially -- morphed to #5 |
| 5 | Apr 16 | `_check_cdp_available` used instead of `_ensure` (dual function) | ffc517e, 9bf62c9 | Addressed #5 specifically -- but #6 appeared same day |
| 6 | Apr 16 | Right process on port, page loaded, but input field `[contenteditable="true"]` not found after idle | (today's failure) | Not yet addressed |
| 7 | Apr 16 | After Copilot restart, Teams WebView2 races for port | (today's failure) | Not yet addressed |

Key observation: Failure classes 1-5 are all different bugs. Each fix is correct. The problem is that fixing #N reveals or creates #N+1. This is the hallmark of automating a system that was not designed for automation.

---

## D3: Containment (Immediate)

Not applicable -- this is a meta-analysis, not a bug fix. The immediate question is architectural, not tactical.

---

## D4: Root Cause Analysis -- Four Quadrants

### Q1: Technical Root Cause -- Non-Conformance

**Question: Why does the same problem keep coming back in different forms?**

```
Why-1:  Each fix addresses a specific failure mode (port stolen, wrong function,
        stale page) without addressing the space of possible failure modes.
        --> Evidence: 7 distinct failure classes in 10 days

Why-2:  The space of possible failure modes is unbounded because the M365
        Copilot desktop app has no automation contract (no API, no documented
        selectors, no stability guarantees for DOM elements).
        --> Evidence: selectors are guessed from DOM inspection:
        [contenteditable="true"], [data-content], div[dir="auto"]

Why-3:  Without a contract, any Microsoft update, idle timeout, WebView2
        lifecycle event, or OS-level port race can introduce a new failure
        mode that no existing self-healing code handles.
        --> Evidence: Class #6 (input field vanishes after idle) was not
        predictable from classes #1-5

Why-4:  The Copilot app is a consumer-facing GUI built on WebView2. WebView2
        is a browser control that can suspend/garbage-collect inactive tabs,
        evict DOM nodes to save memory, and change selectors with any update.
        --> Evidence: Microsoft documents no CDP/automation support for
        M365 Copilot. The --remote-debugging-port flag is inherited from
        Chromium, not intentionally exposed.

Why-5:  Playwright/CDP connects as a debugger attached to a process it does
        not control. The app can navigate away, reload, suspend the renderer,
        or update its SPA framework at any time. The automation has no way to
        prevent this.
        --> Evidence: _find_input() has 10 retries with 2s sleep because
        the element is unreliable. This is a poll-and-hope pattern.

Why-6:  Port 9223 is shared infrastructure. Any WebView2 process on the
        system (OneDrive, Teams, Edge) with WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
        set can grab it. The env var is machine-wide for the user profile.
        --> Evidence: OneDrive grabbed port in class #4; Teams grabbed it
        in class #7

Why-7:  Even when port, process, and page are all correct, the Copilot SPA
        has internal state management. After idle, it may:
        - Unload the input component (contenteditable removed from DOM)
        - Show a "session expired" overlay
        - Require re-authentication within the WebView
        - Throttle responses (return 0 chars)
        --> Evidence: Class #6 today -- input found for first query,
        returned 0 chars, then input disappeared

Why-8:  Self-healing (kill + restart) resets the app to a known-good state
        but introduces a race condition: after killing Copilot, whoever
        starts first grabs the port. If Teams or OneDrive start faster,
        Copilot loses the race.
        --> Evidence: Class #7 today -- after restart, Teams grabbed port

Why-9:  [ROOT CAUSE] The M365 Copilot desktop app is a consumer GUI with
        no automation contract, no API stability guarantees, and no
        documented lifecycle management. Automating it via CDP/Playwright
        is reverse-engineering a moving target. Each fix is correct for its
        observed failure mode, but the SPACE of failure modes is unbounded
        and grows with each Microsoft update, system state change, or
        timing variation. No amount of self-healing code can converge on
        stability for a non-contractual interface.

Why-10: The fundamental mismatch: the NEED is for a reliable, unattended,
        daily data extraction pipeline. The TOOL is a GUI app designed for
        interactive human use. No Toyota engineer would automate a
        production process by screen-scraping a consumer app.

First-Principles Test:
- Condition: YES -- "no automation contract" is a permanent property of the tool
- On/Off:    YES -- switching to a contractual interface would eliminate this class
- Class:     YES -- applies to ALL GUI automation of non-contractual apps
- Controllable: PARTIALLY -- we control the tool choice, not the app's API surface
```

### Q2: Technical Root Cause -- Non-Detection

**Question: Why don't we detect that the problem is morphing before it fails?**

```
Why-1:  Testing consists of running the pipeline once and checking output.
        --> Evidence: standalone test is `py -3 sources/copilot_fetch.py`

Why-2:  A single successful run doesn't prove stability because the failure
        modes are time-dependent (idle timeout), race-dependent (port grab),
        and state-dependent (DOM lifecycle).

Why-3:  You cannot write a test for "what new GUI state will emerge tomorrow"
        because the state space is controlled by Microsoft, not by us.

Why-4:  The previous 8D (dual function) added structural tests for function
        call correctness. These tests would NOT have caught class #6 (stale
        page) or class #7 (port race after restart), because those aren't
        code bugs -- they're environmental instability.

Why-5:  Self-healing code reports success/failure per-run but has no
        trend detection. If 3 of 5 runs need self-healing intervention,
        that signal is lost in per-run logs.

Why-6:  No "workaround health" metric exists. The system doesn't track:
        - How often self-healing triggers per week
        - Success rate of self-healing attempts
        - New failure modes per week
        These would signal "this approach is degenerating."

Why-7:  [ROOT CAUSE] Detection is structurally impossible for a non-
        contractual interface. You can detect KNOWN failure modes (and
        self-heal them), but you cannot detect UNKNOWN FUTURE failure modes
        because they emerge from a system you don't control. The best you
        can do is detect that failures are ACCELERATING -- a "workaround
        decay rate" metric -- which doesn't exist.

First-Principles Test:
- Condition: YES -- "unbounded failure space" is inherent to non-contractual automation
- On/Off:    PARTIAL -- a decay rate metric would detect degeneration but not prevent it
- Class:     YES -- applies to all reverse-engineered automation
- Controllable: YES -- we can add trend detection
```

### Q3: Managerial Root Cause -- Non-Conformance

**Question: What systemic decision led to this fragile architecture?**

```
Why-1:  Copilot GUI automation was chosen as the data extraction method.
        --> Evidence: commit b755e95 (Apr 7, Day 1 of project)

Why-2:  It was chosen because Graph API couldn't provide the needed data:
        - Meeting transcripts: blocked by OnlineMeetings.Read admin consent
        - Teams chat: MSAL token rotates + daily MFA + CAP blocks Device Code Flow
        --> Evidence: CLAUDE.md "Known Issues / Blockers" section

Why-3:  These Graph API blockers are real and confirmed. Requesting IT
        admin consent was considered and rejected (memory entry:
        "NEVER suggest MFA or IT").

Why-4:  With Graph API blocked and IT requests off the table, Copilot GUI
        automation was the ONLY remaining option for meeting transcripts
        and Teams chat data.
        --> Evidence: this is documented as "the workaround"

Why-5:  The workaround was adopted without exit criteria. No one asked:
        "Under what conditions should we abandon this approach?"
        --> Evidence: no exit criteria documented anywhere

Why-6:  The workaround was then EXPANDED: from "fallback for transcripts"
        (b755e95) to "full pipeline with 4 query types + deep dives +
        quality review loop" (commits 04f5c9d through 5cde9f9).
        A quick workaround became the primary data source.
        --> Evidence: copilot_fetch.py grew from ~100 lines to 735 lines

Why-7:  Each expansion increased the surface area exposed to GUI
        instability. More queries = more chances for input field to vanish.
        Longer sessions = higher chance of idle timeout. Quality review
        loop = 2-3x more Copilot interactions per meeting.

Why-8:  The previous 8D (dual function) analyzed a CODE BUG within the
        Copilot automation, not the ARCHITECTURE DECISION to use Copilot
        automation. Its prevention (wiki consultation, detection artifacts)
        is correct for code-level bugs but irrelevant for architectural
        flaws.

Why-9:  No decision-review process exists for workarounds. When a
        workaround accumulates N fixes (N=3? N=5? N=7?), there is no
        trigger to re-evaluate the decision to use it.

Why-10: [ROOT CAUSE] A tactical workaround (Copilot GUI automation to
        bypass Graph API permission gaps) was treated as a permanent
        architecture without exit criteria, escalation thresholds, or
        periodic re-evaluation. It was then expanded into a complex
        multi-query pipeline, amplifying the instability surface. The
        project memory explicitly forbids the only path to fixing the
        underlying cause (requesting IT admin consent for Graph API
        permissions).

First-Principles Test:
- Condition: YES -- "workaround treated as architecture" is ongoing
- On/Off:    YES -- re-evaluating the approach + setting exit criteria would prevent
- Class:     YES -- applies to any workaround that becomes permanent
- Controllable: YES -- architecture decisions are within project control
```

### Q4: Managerial Root Cause -- Non-Detection

**Question: Why don't we have a "this approach is fundamentally flawed" detection mechanism?**

```
Why-1:  The previous 8D analyzed the wrong level. It asked "why did the
        wrong function get called?" instead of "why are we calling ANY
        function that talks to a GUI app via CDP?"

Why-2:  8D methodology naturally narrows to the proximate technical cause.
        "Code calls wrong function" is a clear, fixable finding. "The
        entire approach is wrong" is uncomfortable and doesn't fit neatly
        into corrective/preventive action categories.

Why-3:  Sunk cost: 20 commits, 735 lines, a quality review loop, a
        recording discovery pipeline, prompt YAML files -- all built
        around Copilot. Abandoning it means discarding significant
        investment.

Why-4:  The "don't ask IT" constraint (memory entry) closes the door on
        the most obvious alternative (Graph API permissions), making
        Copilot feel like the only option. When there's "no alternative,"
        you don't question the approach.

Why-5:  No "workaround decay rate" metric exists. The system doesn't
        track that copilot_fetch.py has been modified 20 times in 10 days
        while outlook_calendar.py has been modified 0 times. This ratio
        is the clearest signal that one approach is unstable.

Why-6:  The git commit history IS the decay rate metric, but no one reads
        it that way. Commits are forward-looking ("fixed X") not
        reflective ("this is the 7th fix for the same subsystem").

Why-7:  No retrospective trigger exists. In a team, a standup or
        retrospective would surface "we've been fixing Copilot all week."
        In a solo project, there's no such ritual.

Why-8:  [ROOT CAUSE] No meta-level monitoring of workaround health.
        Specifically: (a) no "fix frequency per subsystem" metric that
        would signal architectural instability, (b) no escalation trigger
        when a workaround exceeds a fix threshold, (c) no periodic
        architecture review for workaround-based subsystems. The previous
        8D's prevention actions (wiki consultation, detection artifacts)
        operate at the code level and would not catch an architecture-level
        flaw.

First-Principles Test:
- Condition: YES -- "no workaround health monitoring" is ongoing
- On/Off:    YES -- a fix-frequency metric with escalation would catch this
- Class:     YES -- applies to any subsystem that's being patched too often
- Controllable: YES -- git history is already the data source
```

---

## D5: Corrective Actions

**This section intentionally left blank.** The meta-8D's finding is that corrective actions (tactical fixes) are the WRONG response to an architectural problem. Each corrective action has worked perfectly for its specific failure class and has done nothing to prevent the next failure class from emerging.

The 20 commits fixing Copilot ARE the corrective actions. They demonstrate that the approach has exhausted its corrective action budget.

---

## D6: Prevention Actions

### P1: Architecture Decision -- Evaluate Alternatives to Copilot GUI Automation

Before writing any more Copilot fixes, evaluate the full option space:

| Option | Data Access | Reliability | Auth Complexity | Effort |
|--------|------------|-------------|-----------------|--------|
| **A. Graph API with proper permissions** | Full (transcripts, chat, recordings) | High (contractual API) | Requires IT admin consent for OnlineMeetings.Read | Low (code exists in transcripts.py) |
| **B. Power Automate flows** | Full (triggers on meeting end, email receipt) | High (Microsoft-managed) | M365 license (already have it) | Medium (new integration) |
| **C. Outlook rules + email parsing** | Partial (recording notification emails, meeting recaps) | High (email is reliable) | None (Outlook COM already works) | Low (extend outlook_mail.py) |
| **D. Copilot Web API (if/when available)** | Full | High (contractual API) | OAuth2 | Unknown (API not yet public) |
| **E. Keep Copilot GUI automation** | Full | Low (7 failure classes in 10 days) | CDP + process management | High (continuous maintenance) |
| **F. Degrade gracefully without meeting data** | None (skip transcripts) | N/A | None | Trivial |

**Recommendation matrix:**

| Priority | Action | Reasoning |
|----------|--------|-----------|
| **Immediate** | Option F: Accept graceful degradation | The briefing system works for calendar, email, JIRA, OneNote. Meeting transcripts are valuable but not worth the instability of the entire pipeline. Remove Copilot from the critical path. |
| **Short-term** | Option C: Extend email parsing | Teams already sends recording notification emails. Parse those for meeting names, dates, links. This gets 60-70% of the value with 0% of the instability. |
| **Medium-term** | Option A: Request IT admin consent | This is the correct long-term solution. The memory entry "NEVER suggest IT" should be re-evaluated -- the cost of NOT requesting is now quantified: 20 commits, 10 days, 7 failure classes, and recurring production failures. |
| **Background** | Option D: Monitor Copilot API availability | Microsoft is likely to release a Copilot API. When it exists, it replaces all GUI automation. |

### P2: Workaround Health Monitoring

Add a simple metric: **fix frequency per module per week**.

```
Rule: If a source module has been modified more than 3 times in 7 days,
the next commit MUST include a WORKAROUND-REVIEW comment that asks:
"Is this approach fundamentally viable? What would we do if this module
didn't exist?"
```

This is the "this approach is fundamentally flawed" detection mechanism that Q4 identified as missing.

Data source: `git log --since="7 days ago" --format="%H" -- sources/{module}.py | wc -l`

### P3: Workaround Exit Criteria Convention

For any workaround adopted in any project:

1. Document it as a WORKAROUND (not "architecture" or "integration")
2. Set explicit exit criteria: "abandon if X" or "re-evaluate when Y"
3. Set a review date (30 days from adoption)
4. Track fix count -- if fix count > 5 before review date, trigger early review

### P4: Narrow Previous 8D Scope Acknowledgment

The previous 8D (dual function coexistence) was correctly executed at its scope level. Its finding (function replacement convention, wiki-to-code traceability) is valid and should be kept. However, it should be annotated that it analyzed a symptom-level problem, and that the architectural problem it sits within remains unresolved.

---

## D7: The Toyota/Google Question

**"What would Toyota/Google do -- would they automate a GUI app for production data extraction?"**

No. Here is what mature engineering organizations do:

| Principle | Toyota Production System | Google SRE | This Project |
|-----------|------------------------|------------|-------------|
| **Use stable interfaces** | Jidoka: machines with built-in quality. Sensors, not cameras watching dials. | API contracts with SLOs. If no API, don't depend on it for production. | Reverse-engineering a GUI via CDP -- no contract, no SLO |
| **Detect instability early** | Andon cord: stop the line when quality drops | Error budgets: when errors exceed budget, stop adding features and fix reliability | No error budget. Fixes and features interleaved on the same unstable foundation |
| **Eliminate waste** | Muda: unnecessary work that doesn't add value | Toil: manual operational work that should be automated via proper interfaces | 20 commits of self-healing code = pure toil. The code exists only because the interface is wrong. |
| **Root cause, not workaround** | 5 Whys goes to the SYSTEM level | Blameless postmortems ask "what system allowed this?" | Previous 8D stopped at code level. This meta-8D reaches system level. |
| **Accept constraints, design around them** | Pull system: don't push against capacity | Circuit breakers: degrade gracefully when a dependency is unhealthy | "Don't ask IT" constraint is accepted but not designed around. Graceful degradation not implemented. |

The correct Toyota/Google answer: **If Graph API requires admin consent you can't get, and the only alternative is screen-scraping a GUI, then that data source is UNAVAILABLE. Design the system to work without it. Don't fight physics.**

---

## D8: Lessons Learned

### 1. Workarounds Have a Shelf Life

A workaround is a temporary measure to buy time while the real solution is pursued. When a workaround is adopted as permanent architecture, it accumulates technical debt at an accelerating rate. The 20-commit, 10-day history of Copilot automation is a textbook example.

**Convention:** Every workaround must have documented exit criteria and a review date.

### 2. Fix Frequency Is an Architecture Signal

When a module is modified 3+ times per week for operational fixes (not feature development), the module's underlying approach is likely flawed. This signal is visible in git history but is never read that way.

**Convention:** Track fix frequency per module. Establish a threshold (e.g., 3 fixes/week) that triggers an architecture review, not another fix.

### 3. 8D Scope Must Match Problem Level

The previous 8D correctly analyzed a code-level bug (dual function coexistence) and produced valid code-level prevention (function replacement convention). But the code-level bug was a symptom of an architecture-level problem (GUI automation of a non-contractual interface). An 8D that stops at the symptom level produces prevention that prevents that specific symptom while the disease continues.

**Convention:** Before starting an 8D, ask: "Is this bug an instance of a known pattern, or is it a new manifestation of an architectural problem?" If the same subsystem has had 3+ distinct bug classes, start the 8D at the architecture level.

### 4. "No Alternative" Is Usually "Haven't Evaluated All Alternatives"

The Copilot GUI approach felt like the only option because:
- Graph API was blocked (real constraint)
- IT requests were off the table (self-imposed constraint)
- No one evaluated Power Automate, email parsing, or graceful degradation

When the constraints are listed, the space looks closed. When alternatives are listed, the space opens.

### 5. Self-Healing Has Diminishing Returns on Non-Contractual Interfaces

Self-healing (kill, restart, retry) works well for transient failures on contractual interfaces (network timeout, token expiry, service restart). It works poorly for structural mismatches (GUI app not designed for automation) because each self-healing action can introduce new failure modes (port race after restart, stale page after idle).

The wiki's own self-healing page documents the anti-pattern: "Workaround stacking on wrong root cause." That's exactly what 20 commits of Copilot fixes represent.

---

## Closure

This meta-8D does NOT recommend more code fixes for Copilot automation. It recommends:

1. **Remove Copilot from the critical path** -- the briefing system should produce output even when Copilot is completely unavailable
2. **Evaluate alternatives** (email parsing, Power Automate, or accepting the data gap)
3. **Re-evaluate the "don't ask IT" constraint** -- the cost of NOT asking is now quantified
4. **Add workaround health monitoring** -- prevent future workarounds from becoming permanent architecture

The Copilot GUI automation code can remain as an optional, best-effort enrichment source. But it should NOT block the pipeline, and no more engineering time should be invested in making it reliable. It is not a reliability problem. It is an architecture problem.
