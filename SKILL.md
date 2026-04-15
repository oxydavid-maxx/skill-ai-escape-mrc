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
Phase 3: Root Cause Audit (3 challenge rounds + scoring rounds, max 7 total)
    ↓  ← loops back to Phase 2 if rejected
Phase 4: Prevention Action Design (one per quadrant)
    ↓
Phase 5: Prevention Action Audit (3 challenge rounds + scoring rounds)
    ↓  ← loops back to Phase 4 if rejected
Phase 6: Verification Plan
    ↓
Phase 7: 8D Report Output → FILE ONLY → await user review
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

## Phase 4: Prevention Action Design

For each quadrant, propose an action.
- Q1/Q2 → Corrective Actions
- Q3/Q4 → Prevention Actions

### Prevention Action Hierarchy (strongest to weakest)

1. **Eliminate**: Architecture makes error impossible
2. **Detect at creation**: Tooling catches at write-time
3. **Detect before merge**: Process gate catches it
4. **Detect after merge**: Monitoring catches it
5. **Mitigate impact**: Limit damage

Q3/Q4 should aim for levels 1-3.

### "Corrective or Preventive?" Gate

| Test | Corrective (fail) | Preventive (pass) |
|------|--------------------|--------------------|
| **Scope** | Prevents THIS instance | Prevents the CLASS |
| **Persistence** | Needs individual effort | Embedded in process/tooling |
| **Measurability** | "Team is more careful" | Auditor can verify in 6 months |

ALL THREE must pass for Q3/Q4 actions.

---

## Phase 5: Prevention Action Audit

Same three-phase audit as Phase 3:

**Rounds 1-3: Challenge (no scoring)**
- Round 1: "Is this corrective or preventive?" — analyst must justify
- Round 2: "Is this the BEST prevention? What alternatives exist? Search online?"
- Round 3: "Side effects? Conflicts with existing mechanisms? Does wiki mention pitfalls?"

**Rounds 4-7: Score on Scope/Persistence/Measurability**

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

### Closure Audit

Before declaring 8D complete, audit agent checks:
1. Is the four-quadrant summary table complete? All 4 cells filled?
2. Are all ND quadrants as deep as NC quadrants?
3. Are all MRC root causes at management-system level (not code level)?
4. Are all Q3/Q4 actions truly preventive (pass gate test)?
5. Is there new knowledge to ingest into wiki?
6. Is there new feedback to save to project memory?
7. Were wiki and project memory consulted in Phase 0?

### ⚠️ STOP HERE

**Do NOT implement any changes. Present the report to the user for review.**

The user will:
1. Review the report
2. Approve, reject, or request changes
3. If approved → use `superpowers:executing-plans` to implement

---

## Agent Team

| # | Agent | Role | Phase |
|---|-------|------|-------|
| 1 | Orchestrator (you) | Drive analysis, ask Whys, propose actions | All |
| 2 | `rc_audit_agent` | Independent multi-round challenge + scoring | Phase 3, 5, 7 |

### Sub-Agent Compliance

When launching audit agent:
1. Read `agents/rc_audit_agent.md` first
2. Include full contents verbatim at top of subagent prompt
3. Provide the four-quadrant analysis as task context
4. Do NOT summarize the agent definition

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
| 8D report → direct execution | Output = report only gate |
| "Improve training" as prevention | Persistence + Measurability tests fail |
| Why chain is rephrasing | Per-Why-step audit in challenge rounds |

---

## Output Language

Match user's language. Technical terms (8D, MRC, TRC, NC, ND, IS/IS NOT, FMEA) stay in English.
