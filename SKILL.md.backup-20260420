---
name: skill-8d-mrc
description: "Use when debugging recurring problems, doing post-mortem analysis, or when a fix didn't prevent recurrence. Triggers on: root cause analysis, 8D, post-mortem, why did this happen again, non-conformance, escape analysis, prevention action, corrective action review, MRC, managerial root cause. Enforces four-quadrant root cause analysis with independent multi-round audit."
---

# 8D MRC — Four-Quadrant Root Cause Analysis with Multi-Round Audit

Rigorous 8D problem solving adapted from automotive quality (IATF 16949, VDA, Ford G8D). Forces analysis across four root cause quadrants with independent multi-round audit at every step.

**Core principle:** A problem reaching the user means TWO independent failures: something went wrong (occurrence/non-conformance) AND every checkpoint missed it (non-detection/escape). Each failure has a technical cause (event) and a managerial cause (systemic condition). All four must be found, audited to exhaustion, and prevented separately.

**Reference study notes:** `D:/D-artifacts/studies/automotive-8d-mrc/automotive-8d-mrc_study.md`

---

## When to Use

- Recurring bug that was supposedly "fixed" before
- Post-mortem / retrospective on an escaped defect
- User says "why did this happen again" or "why wasn't this caught"
- Review of a proposed fix — is it corrective or truly preventive?
- Any problem where the fix was "add a check" or "be more careful"

## When NOT to Use

- First-time simple bug with obvious fix and no recurrence risk
- Feature request or design discussion
- Performance optimization (use profiling, not 8D)

---

## CRITICAL: 8D Output = Report Only

**The 8D skill produces a REPORT. It does NOT execute any code changes, commits, or fixes.**

After Phase 7 completes, the report is written to a file and presented to the user. The user reviews and approves before any implementation begins. Implementation uses `superpowers:executing-plans`, not this skill.

**Gate:** If you find yourself editing source code during 8D analysis → STOP. You are violating the skill boundary.

---

## The Four Quadrants

```
              │ Non-Conformance (NC)  │ Non-Detection (ND)
              │ WHY it happened       │ WHY it wasn't caught
──────────────┼───────────────────────┼────────────────────────
Technical RC  │ Q1 (TRC-NC):          │ Q2 (TRC-ND):
(event)       │ Direct technical      │ Detection method
              │ cause of the defect   │ that failed to catch it
──────────────┼───────────────────────┼────────────────────────
Managerial RC │ Q3 (MRC-NC):          │ Q4 (MRC-ND):
(condition)   │ Process/system gap    │ Control system gap
              │ that allowed Q1       │ that allowed Q2
```

**Q1 (TRC-NC) → Corrective Action** (fix this instance)
**Q2 (TRC-ND) → Corrective Action** (fix this detection gap)
**Q3 (MRC-NC) → Prevention Action** (prevent the CLASS of occurrence)
**Q4 (MRC-ND) → Prevention Action** (prevent the CLASS of detection gaps)

### MRC Level Check (MANDATORY)

If a root cause labeled "Managerial" involves a code change, function deletion, or technical fix → it is NOT managerial. It is technical. Relabel it as TRC and dig deeper for the true MRC.

**MRC must be at management system level**: process definition, governance, organizational structure, policy, review gate, training curriculum design, tooling investment decision. NOT: "delete this function" or "add this check."

### ND Equal Depth Rule

Non-Detection (Q2, Q4) must receive the SAME depth of analysis as Non-Conformance (Q1, Q3). The audit agent explicitly checks: "Is the ND analysis as deep as the NC analysis?" If not → reject.

---

## Orchestration (7 Phases)

```
Phase 0: Pre-Analysis (wiki + memory + references)
    ↓
Phase 1: IS/IS NOT Problem Definition
    ↓
Phase 2: Four-Quadrant Why Analysis (10 Whys each, 4 quadrants)
    ↓
Phase 3: Root Cause Audit (challenge until exhaustion + residual risk register)
    ↓  ← loops back to Phase 2 if addressable weaknesses remain
Phase 4: Prevention Action Design (one per quadrant)
    ↓
Phase 5: Prevention Action Audit (challenge until exhaustion, NO rubber-stamp scoring)
    ↓  ← loops back to Phase 4 if addressable weaknesses remain
Phase 6: Verification Plan
    ↓
Phase 7: 8D Report Output → RENDER IN CONVERSATION → await user review
    ↓  ← user approves → implement prevention actions
Phase 8: Verification of Prevention Effectiveness (post-implementation, at first real test)
    ↓  ← if prevention failed → re-open 8D, MRC analysis was too shallow
```

---

## Phase 0: Pre-Analysis (MANDATORY — before any Why analysis)

Before starting Phase 2, you MUST:

1. **Read wiki index** (`D:/D-claude/personal-wiki/wiki/index.md`) — list ALL pages that might be relevant
2. **Read project memory** (`~/.claude/projects/*/memory/MEMORY.md`) — list ALL entries that relate to this problem
3. **Read relevant wiki pages** — for each relevant index entry, read the page and extract applicable anti-patterns/lessons
4. **Check available skills** — is there a skill that addresses this type of problem?
5. **Document what you found** — in the 8D report, list all consulted sources with what you learned from each

If wiki or memory contains knowledge directly about this problem (e.g., "don't stack workarounds", "check if self-healing code is called") → this knowledge MUST appear in the Why analysis. Ignoring known knowledge = audit rejection.

---

## Phase 1: IS/IS NOT Problem Definition

Before asking "Why?", define WHAT the problem is and ISN'T.

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | | | |
| **WHERE** | | | |
| **WHEN** | | | |
| **EXTENT** | | | |

The DISTINCTION column is the diagnostic tool. Root cause hypotheses MUST explain ALL distinctions.

---

## Phase 2: Four-Quadrant Why Analysis

For EACH of the 4 quadrants, ask WHY iteratively.

### Depth Requirement: Minimum 10 Whys

- Ask at least 10 Whys per quadrant
- Each Why MUST be a genuinely new insight, not a rephrasing of the previous one
- Stop ONLY when: "Further why enters tautology, law of physics, or organizational boundary that cannot be changed"
- The ANALYST proposes stopping. The AUDITOR decides if stopping is justified.
- If auditor says "go deeper" → analyst must continue

### What counts as a valid Why

- ✅ New causal insight: reveals a mechanism, condition, or decision not previously stated
- ❌ Rephrasing: same idea in different words
- ❌ Jumping: skipping intermediate causes
- ❌ Circular: "Why A? Because B. Why B? Because A."

### First-Principles Stopping Criterion

A Why chain stops when ALL FOUR tests pass:

1. **Condition test**: Describes ongoing state, not one-time event
2. **On/Off test**: Introducing condition reproduces defect; removing suppresses it
3. **Class test**: Explains the entire class, not just this instance
4. **Controllability test**: Organization can directly act on it

### What is NOT a root cause

| Sounds like root cause | Why it's not | Ask instead |
|------------------------|--------------|-------------|
| "The code had a bug" | Symptom | WHY was this code possible to write? |
| "Developer made a mistake" | Event | WHY did the process allow this mistake? |
| "I didn't check" | Human action | WHY was there no mandatory check? |
| "Human error" | Tautology | WHY didn't the system prevent/catch? |
| "Insufficient testing" | Vague | WHICH test missing? WHY wasn't it required? |

### For each Why, analyst must consider:

- Is there a wiki page about this pattern?
- Is there a project memory entry about this?
- Should I search online for how others solve this?
- Is there a skill that addresses this?
- Is this truly the BEST explanation, or am I taking the easy path?

---

## Phase 3: Root Cause Audit

**Launch an independent audit agent** (subagent). Read `agents/rc_audit_agent.md` for full definition.

### Three-Phase Audit Process

**Rounds 1-3: Challenge & Deepen (NO scoring)**

Each round, the auditor reviews ALL four quadrants and for EACH Why step:
1. Is this logic valid? Is it a real WHY or a restatement?
2. Is this the best explanation? What alternatives were considered?
3. Did you search wiki for this? Project memory? Online?
4. Is there a skill that addresses this pattern?
5. Can you go one more Why deeper?
6. Is there a completely different framing of this problem?
7. Is the ND analysis as deep as the NC analysis?

After each round, analyst must respond to ALL challenges before next round.

**Rounds 4-7: Scoring (only after 3 challenge rounds)**

Score 7 dimensions × 0-3:
1. Specificity
2. Depth
3. Verifiability
4. Controllability
5. Completeness
6. MRC Level Check (is MRC truly management-system level?)
7. Wiki/Memory Consultation (were known resources consulted and cited?)

**Reject threshold**: ANY dimension = 0, OR more than ONE dimension = 1 → REJECT.

**Maximum 7 total rounds** (3 challenge + 4 scoring attempts). If still not passing after 7 → escalate to user with current state.

---

## Phase 4: Prevention Action Design — 10-Why Chain

For each quadrant, propose an action:
- Q1/Q2 → Corrective Actions (fix this instance/detection gap)
- Q3/Q4 → Prevention Actions (prevent the CLASS)

### Prevention Action Hierarchy (strongest to weakest)

1. **Eliminate**: Architecture makes error impossible
2. **Detect at creation**: Tooling catches at write-time
3. **Detect before merge**: Process gate catches it
4. **Detect after merge**: Monitoring catches it
5. **Mitigate impact**: Limit damage

Q3/Q4 should aim for levels 1-3.

### Prevention 10-Why Chain (MANDATORY for Q3/Q4)

For each Q3/Q4 prevention action, ask WHY iteratively — **same depth as root cause analysis**.

Direction is OPPOSITE to root cause: instead of "why did it happen?" → "why is this the BEST prevention?"

```
Why-1:  Why this action? → because it addresses [root cause]
Why-2:  Is there a STRONGER action? → consider hierarchy: eliminate > detect > mitigate
Why-3:  Why not eliminate entirely? → because [constraint] → can we remove the constraint?
Why-4:  Does this prevent the CLASS or just this instance? → verify scope
Why-5:  Will this work without individual effort? → verify persistence
Why-6:  Can a third-party auditor verify this in 6 months? → verify measurability
Why-7:  Does this conflict with existing mechanisms? → check wiki, memory, existing code
Why-8:  What's the failure mode of this prevention? Can IT fail silently?
Why-9:  Has this type of prevention been tried before? Did it work? → check history
Why-10: Is this the most fundamental prevention possible within our control?
```

Each Why must be a genuinely new insight. The analyst proposes stopping; the auditor decides.

### Deployment Scope Decision (MANDATORY for Q3/Q4)

After the 10-Why chain, the analyst MUST determine: is this prevention **project-scoped** or **global-scoped**?

| Scope | Meaning | Where it lives | Example |
|-------|---------|----------------|---------|
| **Project** | Prevents this class only within this project | Project CLAUDE.md, project hooks, project tests | "Add pre-commit hook to daily_brief" |
| **Global** | Prevents this class across ALL projects | Global `~/.claude/CLAUDE.md`, global hooks, wiki | "All projects must have detection artifacts for bug fixes" |

**Decision criteria:**
1. Is the root cause specific to this project's architecture/domain? → Project
2. Is the root cause a general development practice gap? → Global
3. Could this same class of failure occur in other projects? → Global
4. Does the prevention mechanism require project-specific knowledge? → Project
5. Is the prevention a universal principle (e.g., "always test", "always consult knowledge base")? → Global

**Both answers are valid.** The auditor challenges the choice:
- If project-scoped: "Why not global? Could other projects benefit?"
- If global-scoped: "Is this too broad? Will it create noise in projects where it doesn't apply?"

**Output:**
```
Deployment Scope: [PROJECT / GLOBAL]
Justification: [why this scope, not the other]
If PROJECT: horizontal deployment candidates in D8
If GLOBAL: which global config file gets the rule
```

### "Corrective or Preventive?" Gate (applied BEFORE the 10-Why)

| Test | Corrective (fail) | Preventive (pass) |
|------|--------------------|--------------------|
| **Scope** | Prevents THIS instance | Prevents the CLASS |
| **Persistence** | Needs individual effort | Embedded in process/tooling |
| **Measurability** | "Team is more careful" | Auditor can verify in 6 months |

ALL THREE must pass for Q3/Q4 actions. If any fails → it's corrective, not prevention. Relabel and redesign before starting the 10-Why chain.

### Output per Prevention Action

```markdown
## Prevention Q[3/4]: [MRC-NC/MRC-ND]

Proposed action: [description]

Gate Test:
- Scope: [PASS/FAIL — evidence]
- Persistence: [PASS/FAIL — evidence]
- Measurability: [PASS/FAIL — evidence]

Prevention Why Chain:
Why-1: [Why this action?] → [because...]
Why-2: [Is there a stronger action?] → [because...]
...
Why-N: [This is the most fundamental prevention within our control]

Prevention Hierarchy Level: [1-5]
Failure Mode of Prevention: [how could this prevention itself fail?]
Deployment Scope: [PROJECT / GLOBAL — justification]
```

---

## Phase 5: Prevention Action Audit

**Launch a SEPARATE audit agent** — `prevention_audit_agent.md` (NOT the same as `rc_audit_agent`).

Why separate: RC auditor who approved the root cause has confirmation bias toward prevention that matches. Prevention auditor sees it with fresh eyes.

### Three-Phase Audit Process (same structure as Phase 3)

**Rounds 1-3: Challenge & Deepen (NO scoring)**

Each round, for each Q3/Q4 prevention, the auditor reviews EVERY prevention-why step:
1. Is the logic valid? Is this a real improvement or a restatement?
2. Is this truly prevention or corrective in disguise?
3. Is there a STRONGER prevention? Search wiki, online, skills
4. Does this conflict with existing mechanisms?
5. Has this been tried before? Did it work?
6. What's the failure mode? Can THIS prevention fail silently?
7. MRC Level Check: management-system level? Or code change disguised as management?

After each round, analyst must respond to ALL challenges.

**After 3 challenge rounds: Continuous Improvement (NO rubber-stamp scoring)**

The old model (score 0-3, pass at threshold) created false confidence — 3 rounds of self-challenge always led to passing scores. This is bureaucratic, not quality-improving.

**New model: Challenge Until Exhaustion + Residual Risk Register**

After 3 challenge rounds, the auditor does NOT score pass/fail. Instead:

1. **List ALL remaining weaknesses** — even minor ones. Nothing is "good enough to pass."
2. **For each weakness**: classify as ADDRESSABLE (analyst can fix now) or RESIDUAL (inherent limitation, accepted with eyes open).
3. **ADDRESSABLE weaknesses → analyst must fix** → re-submit to auditor → continue challenging.
4. **RESIDUAL weaknesses → Residual Risk Register** — documented explicitly in the report. Not hidden by a passing score.
5. **Auditor declares EXHAUSTED** when: (a) no more ADDRESSABLE weaknesses remain, AND (b) all residual risks are documented with mitigation or acceptance rationale.

The output is NOT a score. It is:
```
## Prevention Audit Result

### Addressed (fixed during audit)
- [list of weaknesses that were fixed through challenge rounds]

### Residual Risks (inherent, accepted)
- [weakness]: [why it can't be fixed] → [mitigation or acceptance rationale]

### Verdict: EXHAUSTED / STILL HAS ADDRESSABLE WEAKNESSES
```

**Why this is better:** No dimension ever gets a "2 = adequate, move on." Every weakness is either fixed or explicitly documented as a known risk. The audit drives actual improvement, not bureaucratic pass/fail.

**Maximum rounds: no cap.** Continue until exhausted. If analyst and auditor loop without progress → escalate to user with the current state.

---

## Phase 6: Verification Plan

For each prevention action:

| Element | Description |
|---------|-------------|
| **Metric** | What measurement proves it's working? |
| **Data source** | Where does measurement come from? |
| **Timeframe** | Minimum 6 months |
| **Success criteria** | Specific threshold |
| **Failure action** | What if metric shows it's not working? |

---

## Phase 7: 8D Report Output

### Mandatory Summary Table (TOP of report)

```
| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: [one-line summary] | Q2: [one-line summary] |
| **MRC** | Q3: [one-line summary] | Q4: [one-line summary] |
```

This table MUST be filled. Any empty cell = report is incomplete.

### Report File

Write to: `docs/8d-reports/8d-YYYY-MM-DD-[problem-slug].md`

Use `templates/8d_report_template.md` for structure.

### Wiki Ingest Section (MANDATORY if recommended)

If the closure audit recommends wiki ingest, the report MUST include **draft content** for each topic — not just a title. The draft content should be ready to save to `personal-wiki/raw/notes/` for ingest.

```markdown
### Wiki Ingest: [Topic Title]

**Target page**: [new page slug or existing page to update]
**Type**: [concept / source / comparison]

[Full draft content — 200-500 words with:]
- What the pattern/concept is
- When to apply it
- Common mistakes / anti-patterns
- Connection to existing wiki pages
```

**Why:** A topic title without content is a TODO that never gets done. The 8D analysis already produced the knowledge — extracting it into wiki format costs 5 minutes during report writing but saves hours of re-discovery later.

### Closure Audit

Before declaring 8D complete, audit agent checks:
1. Is the four-quadrant summary table complete? All 4 cells filled?
2. Are all ND quadrants as deep as NC quadrants?
3. Are all MRC root causes at management-system level (not code level)?
4. Are all Q3/Q4 actions truly preventive (pass gate test)?
5. Is there new knowledge to ingest into wiki? **If yes → draft content must be in report**
6. Is there new feedback to save to project memory?
7. Were wiki and project memory consulted in Phase 0?

### ⚠️ USER REVIEW GATE

**Do NOT implement any changes. Present the FULL RENDERED report to the user.**

The orchestrator must:
1. Output the complete 8D report content in the conversation (rendered markdown, not just a file path)
2. If the report is too long, output section by section with explicit "continue?" prompts
3. The user sees EVERYTHING — the why chains, audit rounds, prevention actions, residual risks
4. The user approves, rejects, or requests changes
5. If approved → implement prevention actions
6. After implementation → proceed to Phase 8

---

## Phase 8: Verification of Prevention Effectiveness (Post-Implementation)

**This phase happens AFTER prevention actions are implemented, at the FIRST REAL INCIDENT that tests the prevention.**

### When to Trigger Phase 8

Phase 8 is triggered when:
1. A problem occurs in the same domain as the 8D
2. Or a similar class of problem occurs in any domain
3. Or the scheduled verification timeframe is reached (from Phase 6)

### What Phase 8 Checks

For each prevention action (Q3/Q4):

| Check | Question | Evidence Required |
|-------|----------|-------------------|
| **Activated** | Did the prevention mechanism actually fire? | Log output, hook output, grep results |
| **Effective** | Did it prevent the recurrence, or did the problem morph around it? | Was the problem caught before reaching user? |
| **Not bypassed** | Was the prevention used as intended, or worked around? | Check for exemption abuse, hook bypass |
| **No false alarms** | Did it flag things that weren't actually problems? | False positive rate |
| **Still relevant** | Is the prevention still needed, or has the environment changed? | Is the root cause still present? |

### Verification Output

```markdown
## Phase 8: Prevention Verification — [date]

### Trigger: [what incident triggered this check]

| Prevention | Activated? | Effective? | Bypassed? | False alarms? | Still relevant? |
|-----------|-----------|-----------|----------|--------------|----------------|
| Q3: [name] | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |
| Q4: [name] | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |

### Findings
- [what worked]
- [what failed — why — what to change]

### Action
- [KEEP / MODIFY / REPLACE / REMOVE] each prevention
- If MODIFY/REPLACE → new 8D or amendment to existing report
```

### Anti-Pattern: "Prevention Worked on Paper"

The most dangerous Phase 8 finding is: prevention was implemented (hooks installed, rules written) but when the REAL test came, it didn't fire or was ignored. This means the prevention is corrective in disguise — it changed artifacts but not behavior.

If Phase 8 finds this → the original 8D's MRC analysis was too shallow. Re-open the 8D.

---

## Agent Team

| # | Agent | Role | Phase |
|---|-------|------|-------|
| 1 | Orchestrator (you) | Drive analysis, ask Whys, propose actions | All |
| 2 | `rc_audit_agent` | Independent audit of root cause analysis | Phase 3 |
| 3 | `prevention_audit_agent` | Independent audit of prevention actions (SEPARATE from RC auditor) | Phase 5, 7 |

**Why two separate auditors:** The RC auditor who approved the root cause has confirmation bias toward prevention actions that match "their" root cause. The prevention auditor sees the prevention with fresh eyes and different expertise (systemic design vs causal logic).

### Sub-Agent Compliance

When launching EITHER audit agent:
1. Read the corresponding agent `.md` file first
2. Include full file contents verbatim at top of subagent prompt
3. Provide the analysis as task context
4. Do NOT summarize the agent definition
5. Do NOT reuse the same subagent for both RC and prevention audit

---

## Common 8D Failures (Anti-Patterns)

| Failure | How this skill prevents it |
|---------|---------------------------|
| Only Q1 addressed | Audit rejects if any quadrant missing |
| ND ignored | ND Equal Depth Rule + audit checks |
| MRC = code fix | MRC Level Check (must be management system) |
| Prevention = corrective | Three-round challenge + gate test |
| Root cause too shallow | 10-Why minimum + auditor decides when to stop |
| Wiki knowledge ignored | Phase 0 mandatory + audit checks consultation |
| 8D report → direct execution | Output = report only gate + user review gate |
| "Improve training" as prevention | Persistence + Measurability tests fail |
| Why chain is rephrasing | Per-Why-step audit in challenge rounds |
| Audit always passes (rubber stamp) | No scoring — exhaustion model with residual risk register |
| Prevention works on paper but fails in reality | Phase 8 verification at first real incident |
| User doesn't see the analysis | Phase 7 renders full report in conversation |
| Prevention not verified post-implementation | Phase 8 mandatory, re-opens 8D if prevention failed |

---

## Output Language

Match user's language. Technical terms (8D, MRC, TRC, NC, ND, IS/IS NOT, FMEA) stay in English.
