# 8D Report — Copilot Port 9223: Dual Function Coexistence

**Date**: 2026-04-16
**Team**: 光佑 (Kuang-Yu) + Claude Code
**Status**: Open — awaiting user review

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: No function replacement convention — `_check` coexisted with `_ensure`, no mechanism verified all callers migrated | Q2: Purely functional testing (does output look right?), no structural testing (are right functions called?), no CI/lint |
| **MRC** | Q3: Documentation-based governance without enforcement. Wiki had knowledge but wasn't consulted. No wiki-to-code implementation tracking. | Q4: No post-incident improvement process. Bug fixes don't generate detection artifacts. No feedback loop from failures to tests. |

---

## D1: Team

| Role | Name | Expertise |
|------|------|-----------|
| Problem Owner | 光佑 (Kuang-Yu) | Realtek engineer, daily briefing system |
| Root Cause Analyst | Claude Code (Opus) | Orchestrator + Why analysis |
| RC Auditor | Claude Code (Opus subagent) | Independent adversarial audit |
| Prevention Auditor | Claude Code (Opus subagent) | Independent prevention audit (separate from RC auditor) |

## D2: Problem Definition (IS/IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | `fetch_all_via_copilot` calls `_check_cdp_available()` (passive port check) instead of `_ensure_cdp_has_copilot()` (active restart) | Not a port availability issue — port IS available, just held by wrong process (OneDrive) | The correct function exists but the wrong function is called |
| **WHERE** | `fetch_all_via_copilot()` line 469 + `__main__` test block | NOT in `summarize_meetings_via_copilot()` — that one was correctly updated | Both are Copilot entry points but only one got the fix |
| **WHEN** | After commit 5aed7f6 (April 9) added `_ensure` — old `_check` was left alive | NOT before 5aed7f6 — before that, only `_check` existed | Problem introduced by ADDING code without removing obsolete version |
| **EXTENT** | 2 of 3 call sites used wrong function | NOT all callers — `summarize_meetings` was correctly updated | Partial migration: new function added but old not retired |

## D3: Containment (Immediate Actions)

| # | Action | Owner | Date | Status |
|---|--------|-------|------|--------|
| 1 | Changed `fetch_all_via_copilot` to call `_ensure_cdp_has_copilot()` | Claude Code | 2026-04-16 | Done (ffc517e) |
| 2 | Changed `__main__` test block to call `_ensure_cdp_has_copilot()` | Claude Code | 2026-04-16 | Done (9bf62c9) |

## D4: Root Cause Analysis (Four Quadrants)

### Phase 0: Resources Consulted

| Source | Pages/Entries | Findings |
|--------|--------------|----------|
| Wiki: self-healing-automation.md | Layer 2: Port/Service Reclaim | Prescribes `_ensure` pattern. Documents anti-pattern "workaround stacking on wrong root cause" |
| Wiki: silent-staleness.md | Silent degradation | Warns: silent failure worse than crash; data freshness from content not metadata |
| Wiki: msal-token-theft.md | MSAL token lifecycle | Scope gaps, token rotation behavior |
| Memory: feedback_debug_root_cause.md | "Inspect actual data before assuming cause" | Directly applicable — developer assumed port issue without verifying code path |
| Memory: project_auth_and_copilot.md | "Meeting transcripts always via Copilot" | Copilot is critical path, not optional |

### Q1: Technical Root Cause — Non-Conformance

**Question: Why did `fetch_all_via_copilot` fail when OneDrive held port 9223?**

```
Why-1:  fetch_all_via_copilot() called _check_cdp_available() which only checked
        if port responded, not whether Copilot held it.
        → Evidence: git diff ffc517e

Why-2:  _check_cdp_available() was a passive boolean check (GET /json/version,
        status==200). Couldn't distinguish Copilot from OneDrive.
        → Evidence: deleted function body was 4 lines

Why-3:  _ensure_cdp_has_copilot() existed but was only connected to
        summarize_meetings_via_copilot(), not fetch_all_via_copilot().
        → Evidence: git diff 5aed7f6

Why-4:  Change was narrow-scoped to one call site without searching for all
        callers. A grep would have found 3 call sites.
        → Evidence: commit 5aed7f6 only touches summarize_meetings path

Why-5:  Both functions coexisted 7 days with no signal that one was obsolete.
        No deprecation marker (warnings.warn, adapter redirect, or deletion).
        → Evidence: both existed from 5aed7f6 to 9bf62c9

Why-6:  No deprecation action applied. DeprecationWarning would be silenced by
        default in library context (Python 3.2+). No adapter redirect. No deletion.
        → Evidence: no warnings.warn() in code

Why-7:  No convention for function replacement existed (retire-old, mark
        deprecated, or search all callers before adding replacement).
        → Evidence: no CLAUDE.md rule

Why-8:  [ROOT CAUSE] No development rule requires searching all call sites when
        adding a replacement function. For a solo project, a CLAUDE.md rule is
        the appropriate-scale mechanism.

First-Principles Test:
- Condition: ✅ "No function replacement convention" is ongoing state
- On/Off:    ✅ Adding convention would prevent this class
- Class:     ✅ Applies to ANY function replacement
- Controllability: ✅ Within project's control (one CLAUDE.md line)
```

### Q2: Technical Root Cause — Non-Detection

**Question: Why wasn't the wrong function call detected before it caused failures?**

```
Why-1:  No automated test verified which function fetch_all_via_copilot calls.
        → Evidence: no test file for copilot_fetch.py

Why-2:  Manual testing only verified functional behavior (does Copilot work?),
        not structural behavior (is the right function called?).
        → Evidence: testing was py -3 sources/copilot_fetch.py → check output

Why-3:  Bug only triggers when OneDrive grabs port 9223 first — race condition
        absent in happy-path manual testing.
        → Evidence: works when Copilot is already running

Why-4:  No test infrastructure for CDP-level testing (mocking, test servers).
        → Evidence: no test infrastructure in repo

Why-5:  Python scripting culture favors "run and check output." Structural
        testing (call-site verification) is library/framework territory.
        → Evidence: project identity is "a script that runs daily"

Why-6:  No static analysis (linter, grep check) configured to detect obsolete
        function calls.
        → Evidence: no .flake8, ruff.toml, or custom lint rules

Why-7:  No CI pipeline or pre-commit hooks run any automated verification.
        → Evidence: no .pre-commit-config.yaml, no GitHub Actions

Why-8:  Without automated tooling, detection relies on developer memory — no
        reliability guarantee.

Why-9:  Error manifested silently: _check returned False, function printed a
        [WARN] and returned empty data. Pipeline continued with missing data.
        → Evidence: warning buried in log output

Why-10: [ROOT CAUSE] No architectural distinction between "source unavailable"
        and "source returned empty." Pipeline can't distinguish failure from
        legitimate emptiness (e.g., no meetings on weekends).
        → Evidence: output schema returns empty dict for both cases

First-Principles Test:
- Condition: ✅ "No structural testing + silent failure architecture" is ongoing
- On/Off:    ✅ Adding structural tests + status enums would catch this class
- Class:     ✅ Applies to ANY internal function call correctness
- Controllability: ✅ Within project's control
```

### Q3: Managerial Root Cause — Non-Conformance

**Question: What systemic condition allowed the technical root cause to exist?**

```
Why-1:  Developer didn't search for all callers when adding replacement.
        → Individual behavior, not systemic. Ask WHY process allowed this.

Why-2:  No development process requires "search for all callers before adding
        a replacement function."
        → Evidence: no CLAUDE.md rule, no checklist

Why-3:  Quality governance is documentation-based (wiki, CLAUDE.md) but not
        enforcement-based (hooks, linters, automated checks).

Why-4:  Wiki was NOT consulted during the April 9 debug session. Self-healing
        page explicitly documents Layer 2 (port reclaim) but developer didn't
        read it before implementing.
        → Evidence: fix matched wiki prescription but arrived by trial-and-error

Why-5:  No process gate requires "consult wiki before implementing a fix in a
        known problem domain." Wiki consultation is optional.
        → Evidence: CLAUDE.md says "check wiki" as guideline, not gate

Why-6:  Wiki-to-code path is one-directional: knowledge goes INTO wiki but no
        mechanism verifies knowledge FROM wiki is implemented in code.
        → Evidence: wiki prescribes 4-layer self-healing, code had 2 layers

Why-7:  No implementation tracking for wiki prescriptions. No checklist of
        "implemented / pending / rejected" for wiki recommendations.

Why-8:  Wiki treated as reference material (read when you think of it) rather
        than specification (must be followed and verified).

Why-9:  Governance model is trust-based in a solo project — the same person who
        skips a step is the same person who would catch it.
        → Evidence: all commits single-author

Why-10: [ROOT CAUSE] Project has not implemented automated compensating controls
        (pre-commit hooks, linting, CI) to substitute for the peer review that
        a solo project inherently lacks. The controllable action is automation,
        not adding team members.

First-Principles Test:
- Condition: ✅ "Unenforced documentation-based governance" is ongoing
- On/Off:    ✅ Enforcement mechanisms would prevent this class
- Class:     ✅ Applies to ANY wiki knowledge that should be in code
- Controllability: ✅ Within project's control
```

### Q4: Managerial Root Cause — Non-Detection

**Question: What systemic condition allowed the detection gap to persist?**

```
Why-1:  No automated test exists for copilot_fetch.py.
        → Evidence: no test file

Why-2:  No testing policy — no rule saying "every module must have tests" or
        "every bug fix must include a regression test."
        → Evidence: no CLAUDE.md testing rule

Why-3:  Testing culture is "test by running" — developer runs main.py --dry-run
        and visually inspects. Catches functional failures, not structural.
        → Evidence: CLAUDE.md documents --dry-run as primary test

Why-4:  Solo project — no code review to ask "where are the tests?"
        → Evidence: no PR reviews

Why-5:  No CI pipeline to enforce test coverage or run regression tests.
        → Evidence: no CI config

Why-6:  No process document (wiki or CLAUDE.md) addresses change verification
        or code change completeness.

Why-7:  No wiki page about development verification methodology.

Why-8:  No feedback loop from production failures to test requirements. When bug
        found, fix committed WITHOUT adding test to prevent regression.
        → Evidence: commits ffc517e/9bf62c9 fix bug but add no tests

Why-9:  Failure response is one-step (fix code) instead of two-step (fix code +
        add detection). "Fix-and-move-on" culture.

Why-10: [ROOT CAUSE] No standing post-incident improvement process. Bug fixes
        don't generate detection artifacts (tests, assertions, checks). This
        8D is the first structured incident response in the project.
        → Evidence: no prior 8D reports or post-mortems

First-Principles Test:
- Condition: ✅ "No post-incident improvement process" is ongoing
- On/Off:    ✅ Mandatory detection artifacts would prevent this class
- Class:     ✅ Applies to ANY bug fix without detection
- Controllability: ✅ Within project's control
```

### RC Audit Score (Phase 3)

| Dimension | Score | Notes |
|-----------|:-----:|-------|
| Specificity | 2/3 | Q1/Q3 excellent with git evidence; Q2/Q4 some generic cultural characterizations |
| Depth | 3/3 | All quadrants reach systemic/organizational level |
| Verifiability | 2/3 | Q1 fully evidence-backed; Q2-Q4 have some inferred claims about mental models |
| Controllability | 3/3 | All root causes within project's control |
| Completeness | 3/3 | All 4 quadrants, ND parity achieved, cross-quadrant consistency |
| MRC Level | 3/3 | Both Q3 and Q4 genuinely management-system level |
| Wiki/Memory | 3/3 | 3 wiki pages + 2 memory entries consulted; findings shaped Q3 analysis |

**Total: 19/21 — PASS**

---

## D5: Corrective Actions (Q1, Q2)

| # | Quadrant | Action | Owner | Date | Evidence |
|---|----------|--------|-------|------|----------|
| 1 | Q1 | Changed `fetch_all_via_copilot` to call `_ensure_cdp_has_copilot()` | Claude Code | 2026-04-16 | Commit ffc517e |
| 2 | Q1 | Deleted `_check_cdp_available()` — NameError enforces correct usage | Claude Code | 2026-04-16 | Commit 9bf62c9 |
| 3 | Q2 | Added Copilot fallback when Graph API returns 0 messages with clear logging | Claude Code | 2026-04-16 | Commit 72c2c4a |
| 4 | Q2 | Improved warning messages from generic `[WARN]` to specific path indicators | Claude Code | 2026-04-16 | Commit a2e7a5d |

## D6: Prevention Actions (Q3, Q4)

### Q3 Prevention (MRC-NC): Wiki Consultation Enforcement

**Proposed action:** Pre-commit hook as hard gate requiring wiki consultation evidence or explicit exemption. CLAUDE.md lists key wiki pages for discovery.

**Gate Test:**

| Test | Verdict | Evidence |
|------|---------|----------|
| Scope | PASS | Prevents the CLASS of "wiki knowledge not consulted during implementation" — any wiki prescription, any module |
| Persistence | PASS | Pre-commit hook runs automatically. CLAUDE.md auto-loaded. No individual memory needed. |
| Measurability | PASS | `grep -r "WIKI-CONSULTED\|WIKI-EXEMPT" sources/` cross-referenced with wiki/index.md. Quarterly audit. |

**Prevention Why Chain:**

```
Why-1:  Why this action? → Root cause is documentation-based governance without
        enforcement. Wiki knowledge existed (self-healing Layer 2) but was never
        consulted during April 9 fix. This action adds a hard gate with auditable
        evidence.

Why-2:  Is there a STRONGER action? → Level 3 (detect before merge via pre-commit
        hook). Level 1 (auto-generate code from wiki) not feasible — wiki prescribes
        patterns requiring judgment. Level 2 (session hook surfacing wiki) not feasible
        — Claude Code hooks can't inspect session state. Level 3 is the strongest
        achievable.

Why-3:  Why not eliminate entirely? → Wiki-to-code gap cannot be eliminated because
        wiki knowledge is conceptual (patterns, principles) not mechanical (exact code).
        Constraint is REAL — cannot be removed without reducing wiki to code templates.

Why-4:  Does this prevent the CLASS or just this instance? → CLASS: Triple marker
        (CONSULTED/FINDING/ACTION) applies to ANY wiki-informed code change. CLAUDE.md
        lists key wiki pages for discovery (addresses "didn't know to check wiki").
        Hook enforces evidence (addresses "knew but didn't bother").

Why-5:  Will this work without individual effort? → Pre-commit hook is the enforcement
        layer — it's a HARD GATE, not an instruction. Materially different from the
        existing debug checklist memory entry which says "Step 1: Check wiki" but has
        NO enforcement and was ignored 4+ times.

Why-6:  Can a third-party auditor verify this in 6 months? → Yes: (1) Check CLAUDE.md
        contains wiki page list. (2) grep for WIKI-CONSULTED/WIKI-EXEMPT markers.
        (3) Cross-reference with wiki/index.md. (4) Spot-check 5 commits for quality.

Why-7:  Does this conflict with existing mechanisms? → SYNERGY: Builds on existing wiki
        and CLAUDE.md. Creates bidirectional link between wiki and code that didn't exist.
        WIKI-EXEMPT path prevents hook fatigue for trivial changes.

Why-8:  Failure mode of this prevention? → (1) WIKI-EXEMPT overuse → quarterly audit.
        (2) Perfunctory markers → quarterly spot-check. (3) Hook bypass via --no-verify
        → no CI backup, accepted as solo-project constraint. (4) Wiki page rename →
        stable slugs, periodic grep for orphans.

Why-9:  Has this been tried before? → "Check wiki" instructions (memory entry) have
        FAILED 4+ times. This prevention is different: hard gate (hook) + evidence
        requirement (triple marker). Analogous to ASPICE requirements traceability matrix,
        scaled for solo project.

Why-10: Is this the most fundamental prevention? → Yes. Bridges the gap between
        "knowledge exists in wiki" and "knowledge is consulted during development."
        Hook forces a decision point: consult or declare exemption. Both leave an
        auditable trail.
```

**Prevention Hierarchy Level:** 3 (detect before merge)
**Failure Mode:** WIKI-EXEMPT overuse (mitigated by quarterly audit). Perfunctory markers (mitigated by spot-check). Hook bypass (accepted constraint — no CI).

**Deployment Scope: PRINCIPLE GLOBAL, ENFORCEMENT PROJECT-SCOPED**

Auditor challenged full-global scope: wiki content is 80% daily_brief-specific; 6 of 8 repos would need permanent WIKI-EXEMPT on every commit = compliance theater. Split:
- `~/.claude/CLAUDE.md`: principle (2 sentences) — "Before fixing bugs in known problem domains, consult wiki/index.md. Check for existing patterns before re-deriving solutions."
- `daily_brief/CLAUDE.md`: enforcement — triple markers, key wiki pages, pre-commit hook config
- Graduation: extend enforcement to any project reaching production status (scheduled execution + external dependencies)

**Deliverables:**
1. `~/.claude/CLAUDE.md`: wiki consultation principle (2 sentences)
2. `daily_brief/CLAUDE.md`: key wiki pages list + triple marker convention + exemption rules
3. `daily_brief/.git/hooks/pre-commit`: source file changes require `WIKI-CONSULTED`/`WIKI-FINDING`/`WIKI-ACTION` markers OR `WIKI-EXEMPT: <reason>`
4. Quarterly audit procedure documented

---

### Q4 Prevention (MRC-ND): Post-Incident Detection Artifact Requirement

**Proposed action:** Pre-commit hook requiring detection artifact alongside source changes. Test infrastructure seeded with initial tests. Five acceptable artifact types (not limited to pytest). CLAUDE.md defines testing philosophy and exemption criteria.

**Gate Test:**

| Test | Verdict | Evidence |
|------|---------|----------|
| Scope | PASS | Prevents the CLASS of "bug fixes without detection artifacts" — any module, any bug |
| Persistence | PASS | Test infrastructure permanent. Pre-commit hook automatic. CLAUDE.md auto-loaded. |
| Measurability | PASS | % of source-changing commits with detection artifacts. Test count growth. NO-TEST-REASON rate. |

**Prevention Why Chain:**

```
Why-1:  Why this action? → Root cause is "fix-and-move-on culture" — bug fixes are
        one-step (fix code) not two-step (fix + add detection). This action makes
        the second step mandatory with a hard gate.

Why-2:  Is there a STRONGER action? → Level 2-3 (detect at creation/before merge).
        Level 1 (prevent all bugs) not feasible for a pipeline with external deps
        (COM, CDP, Graph API). Five artifact types expand beyond just pytest to
        include runtime assertions, structural greps, self-healing checks, and
        output validation.

Why-3:  Why not eliminate entirely? → Bug space is unbounded. Each new bug type
        needs its own detection. Constraint is REAL. What you CAN do is ensure
        every KNOWN bug generates detection infrastructure.

Why-4:  Does this prevent the CLASS or just this instance? → CLASS: "If you change
        source code, you must also add/update detection." Applies to ANY module, ANY
        change. `.detection-rules` file for structural grep patterns extends coverage
        to implementation-wiring bugs (the original bug class).

Why-5:  Will this work without individual effort? → Pre-commit hook checks: source
        Python file changed → requires `tests/` change OR `# DETECTION:` comment in
        code. Simple string match. NO-TEST-REASON exemption for non-logic changes.
        HOTFIX-NO-DETECTION for emergencies (1-week follow-up required).

Why-6:  Can a third-party auditor verify this in 6 months? → Yes:
        git log grep for NO-TEST-REASON count. pytest --co for test count.
        .detection-rules file for structural patterns. All measurable in <10 min.

Why-7:  Does this conflict with existing mechanisms? → SYNERGY: Complements existing
        --dry-run testing. Synergizes with Q3 prevention (wiki-prescribed patterns
        implemented as tests). pytest is standard, lightweight dependency.

Why-8:  Failure mode? → (1) NO-TEST-REASON overuse → quarterly git log grep.
        (2) Trivial detection artifacts → quarterly audit spot-check.
        (3) Hook bypass → no CI backup (accepted constraint).
        (4) Structural grep rules go stale → .detection-rules has dates,
        >12 month rules cleaned quarterly.

Why-9:  Has this been tried before? → No prior test infrastructure in this project.
        "Every bug fix needs a regression test" is universal TDD principle. Wiki's
        self-healing page emphasizes "detect before escalate" — same principle at
        runtime level.

Why-10: Is this the most fundamental prevention? → Yes. The feedback loop
        bug → fix → detection artifact → future bugs caught is the core mechanism.
        Five artifact types ensure this works even for architecturally untestable
        code (CDP, COM). The test file seeds infrastructure. The hook enforces
        discipline.
```

**Prevention Hierarchy Level:** 2-3 (detect at creation + before merge)
**Failure Mode:** NO-TEST-REASON overuse (mitigated by quarterly audit). Trivial artifacts (mitigated by spot-check). Hook bypass (accepted constraint). Stale .detection-rules (mitigated by quarterly cleanup).

**Deployment Scope: PRINCIPLE GLOBAL, ENFORCEMENT PROJECT-SCOPED**

Auditor challenged full-global scope: 7 of 8 repos have no test infrastructure and no testable runtime code. Global enforcement = compliance theater. Split:
- `~/.claude/CLAUDE.md`: principle (2 sentences) — "Every bug fix should include evidence that the same bug would be caught in the future. This can be a test, a structural assertion, a validation check, or a documented detection mechanism."
- `daily_brief/CLAUDE.md`: enforcement — detection artifact types, testing philosophy, exemption criteria, pre-commit hook config
- `.detection-rules` is per-project (each project's structural grep patterns differ)
- Graduation: extend enforcement to any project reaching production status

**Deliverables:**
1. `~/.claude/CLAUDE.md`: detection artifact principle (2 sentences)
2. `daily_brief/CLAUDE.md`: testing philosophy + 5 detection artifact types + exemption rules
3. `daily_brief/tests/test_regression.py` — 3 initial pure-logic tests
4. `daily_brief/tests/__init__.py`
5. `daily_brief/.git/hooks/pre-commit`: source changes require `tests/` change OR `# DETECTION:` comment
6. `daily_brief/.detection-rules` — initial structural grep patterns from this incident
7. `daily_brief/requirements.txt` — add pytest
8. Quarterly audit procedure documented

---

### Prevention Audit Results (Phase 5)

**Audit process:** 3 challenge rounds (orchestrator ↔ independent prevention_audit_agent) + 1 scoring round. Analyst and auditor were SEPARATE roles throughout — auditor challenged, orchestrator responded, revised why chains sent back for next round.

#### Round 1 Key Challenges:
- Q3: CLAUDE.md "check wiki" rule duplicates `feedback_debug_checklist.md` memory entry that ALREADY FAILED 4+ times. WIKI-REQ marker checks presence not quality.
- Q4: Most bug-prone code (CDP/COM) is architecturally untestable. "Test behavior not implementation" conflicts with original bug class (incorrect function binding).
- Both: Overly complex tracking mechanisms (per-module databases, assertion regex scanning).

#### Analyst Response → Round 2:
- Q3: Dropped CLAUDE.md "check wiki" instruction (duplicates failed memory). Replaced single marker with triple marker (CONSULTED/FINDING/ACTION). Added WIKI-EXEMPT path.
- Q4: Expanded detection artifacts to 5 types beyond just pytest. Nuanced testing philosophy for behavior vs wiring. Per-module tracking → simpler commit message markers.

#### Round 2 Key Challenges:
- Q3: Triple marker creates friction for small commits. Boilerplate markers still possible. Wiki staleness mechanism is instruction-based (same failure class).
- Q4: NO-TEST tracking threshold is arbitrary. Hook detection regex fragile. Emergency bypass undefined.
- Cross-cutting: "The strongest elements are the simplest ones." Too many maintenance obligations.

#### Analyst Response → Round 3:
- Simplified both: dropped complex tracking, arbitrary thresholds. Kept hard gates + simple markers + quarterly audit.
- Q4: Added HOTFIX-NO-DETECTION emergency path. Simplified hook to string match only.

#### Round 3: PROCEED TO SCORING — all challenges adequately addressed.

#### Scoring:

| Dimension | Q3 | Q4 | Notes |
|-----------|:--:|:--:|-------|
| Specificity | 2/3 | 3/3 | Q4 has 7 concrete deliverables with acceptance criteria |
| Strength | 2/3 | 2/3 | Both Level 2-3; Level 1 not feasible |
| Scope | 2/3 | 2/3 | Full class in this project; not horizontal deployment |
| Persistence | 2/3 | 2/3 | Embedded in tooling; bypassable with --no-verify (no CI) |
| Measurability | 2/3 | 2/3 | Metric + data source defined; threshold/failure action need detail |
| MRC Level | 2/3 | 2/3 | Specific process with clear artifacts |
| Conflict Check | 2/3 | 2/3 | No conflicts; synergy not maximized |

**Q3 Total: 14/21 — PASS** (no 0s, no more than one 1)
**Q4 Total: 15/21 — PASS** (no 0s, no more than one 1)

**Implementation order (auditor recommendation):** Q4 first (higher value, compounds), Q3 second.

---

## D7: Verification Plan

| # | Prevention Action | Metric | Data Source | Timeframe | Success Criteria | Failure Action |
|---|------------------|--------|-------------|-----------|------------------|----------------|
| 1 | Q3: Wiki consultation | WIKI-EXEMPT ratio vs WIKI-CONSULTED | `git log --grep` for both markers | 6 months | <30% WIKI-EXEMPT across commits | Review exemption patterns, tighten criteria |
| 2 | Q3: Wiki consultation | Spot-check quality of WIKI-FINDING lines | Sample 5 commits per quarter | 6 months | >80% cite actual wiki page with substantive finding | Escalate to mandatory tool-assisted consultation |
| 3 | Q3: Wiki consultation | Recurrence of "wiki had answer but wasn't consulted" | 8D reports / incident log | 6 months | 0 recurrences | Review hook effectiveness |
| 4 | Q4: Detection artifacts | % of source-changing commits with detection artifacts | `git log` + diff for `tests/` or `DETECTION:` | 6 months | >70% include detection artifact | Review NO-TEST-REASON patterns |
| 5 | Q4: Detection artifacts | Test count growth | `py -3 -m pytest --co -q \| wc -l` | 6 months | Monotonically increasing (≥1 new test per bug fix) | Investigate barriers to testing |
| 6 | Q4: Detection artifacts | NO-TEST-REASON rate | `git log --grep="NO-TEST-REASON"` | 6 months | <25% of source-changing commits | Review exemption culture, tighten criteria |
| 7 | Q4: .detection-rules | Rule count and staleness | `.detection-rules` file review | 6 months | Rules present for each bug fix; >12 month rules cleaned | Quarterly cleanup pass |

---

## D8: Lessons Learned & Horizontal Deployment

### Lessons Learned

1. **Function replacement requires retirement:** When adding a replacement function, the old function must be immediately deleted, deprecated, or adapter-redirected. Coexistence = latent bug.
2. **Wiki knowledge is useless without consultation discipline:** The wiki had the exact answer (Layer 2 self-healing) but wasn't checked. A knowledge base is only as good as the process that makes developers use it.
3. **Solo projects need automated enforcement:** Without peer review, every quality gate must be automated. Trust-based governance fails when there's only one person to trust.
4. **Fix-and-move-on creates technical debt:** Every bug fix without a test is a missed opportunity to build detection infrastructure. Two-step response (fix + detect) is essential.
5. **Silent failure is worse than loud failure:** Empty output that could be either "no data today" or "fetch failed" is an architectural flaw. Status enums make failure visible.

### Horizontal Deployment

**Scope decision (auditor-challenged):** Principle global, enforcement project-scoped. Graduation criteria: extend enforcement to projects reaching production status (scheduled execution + external dependencies).

| Target | Action | Scope | Status |
|--------|--------|-------|--------|
| `~/.claude/CLAUDE.md` | Add wiki consultation principle (2 sentences) + detection artifact principle (2 sentences) | GLOBAL | Pending |
| `daily_brief/` all source modules | Apply WIKI-CONSULTED markers + add tests + .detection-rules | PROJECT (enforcement) | Pending |
| Other D-claude projects | Principle applies via global CLAUDE.md; enforcement only when graduated to production | GRADUATED | N/A — none currently qualify |

### Documents to Update

- [ ] CLAUDE.md — key wiki pages list, testing philosophy, detection artifact types, exemption criteria
- [ ] Pre-commit hook — WIKI-CONSULTED/WIKI-EXEMPT check + tests/DETECTION check + pytest execution
- [ ] tests/test_regression.py — 3 initial pure-logic tests
- [ ] tests/__init__.py
- [ ] .detection-rules — initial structural grep patterns from this incident
- [ ] requirements.txt — add pytest

### Wiki Ingest Recommended

| Topic | Content | Priority |
|-------|---------|----------|
| Wiki-to-Code Traceability Pattern | Triple marker convention (CONSULTED/FINDING/ACTION), pre-commit enforcement, WIKI-EXEMPT path | High |
| Function Replacement Convention | Delete-before-adding, deprecation strategies, caller search checklist | Medium |

### Memory Update Recommended

| Entry | Type | Content |
|-------|------|---------|
| Prevention audit: instructions vs gates | feedback | CLAUDE.md/memory instructions without enforcement gates have failed 4+ times in this project. Always pair text instructions with a hard gate (pre-commit hook). The gate catches what instructions miss. |
| Prevention audit: detection artifacts | feedback | Detection artifacts are not limited to pytest tests. Five types: unit test, runtime assertion, self-healing check, output validation, structural grep. For untestable code (CDP, COM), use structural greps or runtime assertions instead of forcing pytest. |

---

## Closure Audit

| Check | Status | Notes |
|-------|--------|-------|
| Summary table complete | ✅ | All 4 cells filled |
| ND prevention equal depth | ✅ | Q4 (15/21) ≥ Q3 (14/21) |
| MRC at management level | ✅ | Both Q3/Q4 are process/governance level |
| Prevention ≠ corrective | ✅ | Both pass gate test; auditor confirmed TRULY PREVENTIVE after 3 rounds |
| Hierarchy level 1-3 | ✅ | Q3: Level 3, Q4: Level 2-3; Level 1 not feasible, justified |
| Wiki consulted (Phase 0) | ✅ | Pages: self-healing-automation, silent-staleness, msal-token-theft |
| Wiki ingest recommended | ✅ | Topics: Wiki-to-Code Traceability, Function Replacement Convention |
| Memory update recommended | ✅ | Entries: instructions-vs-gates, detection-artifact-types |
| Phase 4-5 flow compliance | ✅ | Orchestrator designed why chains → separate audit agent challenged → 3 rounds → scoring |

### Overall: READY FOR USER REVIEW

---

## ⚠️ STOP — Awaiting User Approval

This report is the output of the 8D analysis. **No code changes have been made for prevention actions.**

Corrective actions (D5) are already implemented (commits ffc517e, 9bf62c9, 72c2c4a, a2e7a5d).

Prevention actions (D6) require user approval before implementation:
1. CLAUDE.md updates (wiki consultation rule, testing philosophy, WIKI-REQ convention)
2. `tests/test_regression.py` creation
3. Pre-commit hook setup
4. requirements.txt update (pytest)
5. Wiki ingest (2 topics)
6. Memory update (1 entry)
