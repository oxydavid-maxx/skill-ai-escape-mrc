---
name: skill-8d-mrc
description: "Use when debugging recurring problems, doing post-mortem analysis, or when a fix didn't prevent recurrence. Triggers on: root cause analysis, 8D, post-mortem, why did this happen again, non-conformance, escape analysis, prevention action, corrective action review, MRC, managerial root cause. Enforces four-quadrant root cause analysis with independent audit scoring."
---

# 8D MRC — Four-Quadrant Root Cause Analysis with Audit Loop

Rigorous 8D problem solving adapted from automotive quality (IATF 16949, VDA, Ford G8D). Forces analysis across four root cause quadrants with independent audit scoring at every step.

**Core principle:** A problem reaching the user means TWO independent failures: something went wrong (occurrence) AND every checkpoint missed it (non-detection). Each failure has a technical cause (event) and a managerial cause (systemic condition). All four must be found, audited, and prevented separately.

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

## The Four Quadrants

```
              │ Occurrence            │ Non-Detection
              │ (WHY it happened)     │ (WHY it wasn't caught)
──────────────┼───────────────────────┼────────────────────────
Technical RC  │ Q1: Direct technical  │ Q2: Detection method
(event)       │ cause of the defect   │ that failed to catch it
──────────────┼───────────────────────┼────────────────────────
Managerial RC │ Q3: Process/system    │ Q4: Control system
(condition)   │ gap that allowed Q1   │ gap that allowed Q2
```

**Q1 → Corrective Action** (fix this instance)
**Q2 → Corrective Action** (fix this detection gap)
**Q3 → Prevention Action** (prevent the CLASS of occurrence)
**Q4 → Prevention Action** (prevent the CLASS of detection gaps)

---

## Orchestration (7 Phases)

```
Phase 1: IS/IS NOT Problem Definition
    ↓
Phase 2: Four-Quadrant Root Cause Analysis (5-Why each)
    ↓
Phase 3: Root Cause Audit (independent agent scores each quadrant)
    ↓  ← loops back to Phase 2 if rejected
Phase 4: Prevention Action Design (one per quadrant)
    ↓
Phase 5: Prevention Action Audit ("Corrective or Preventive?" gate)
    ↓  ← loops back to Phase 4 if rejected
Phase 6: Verification Plan
    ↓
Phase 7: 8D Report Output
```

---

## Phase 1: IS/IS NOT Problem Definition

Before asking "Why?", define WHAT the problem is and ISN'T.

| Dimension | IS (where problem appears) | IS NOT (where problem doesn't appear) | DISTINCTION |
|-----------|---------------------------|---------------------------------------|-------------|
| **WHAT** | What artifact/component has the defect? | What similar artifacts DON'T have it? | What's different? |
| **WHERE** | Which module/file/system? | Which similar modules DON'T? | What's different? |
| **WHEN** | When did it first appear? Which commit/build? | When was it last known-good? | What changed between? |
| **EXTENT** | How severe? How frequent? Deterministic? | What conditions does it NOT appear under? | What varies? |

The DISTINCTION column is the diagnostic tool. Root cause hypotheses MUST explain ALL distinctions.

---

## Phase 2: Four-Quadrant 5-Why Analysis

For EACH quadrant, ask WHY iteratively until reaching a **first-principles stopping point**.

### First-Principles Stopping Criterion

Stop asking WHY when ALL FOUR tests pass:

1. **Condition test**: Describes an ongoing state, not a one-time event
2. **On/Off test**: Introducing the condition reproduces the defect; removing it suppresses it
3. **Class test**: Explains the entire class of similar defects, not just this instance
4. **Controllability test**: The organization can directly act on it

If any test fails, go deeper.

### What is NOT a root cause

| Sounds like root cause | Why it's not | What to ask instead |
|------------------------|--------------|---------------------|
| "The code had a bug" | Symptom, not cause | WHY was this code possible to write? |
| "Developer made a mistake" | Event, not condition | WHY did the process allow this mistake? |
| "I didn't check" | Human action, not systemic | WHY was there no mandatory check? |
| "Human error" | Tautology (humans always err) | WHY didn't the system prevent/catch this error? |
| "Insufficient testing" | Vague | WHICH specific test was missing? WHY wasn't it required? |

### Output per Quadrant

```markdown
## Q[N]: [Technical/Managerial] × [Occurrence/Non-Detection]

Why-1: [statement] → because [explanation]
Why-2: [statement] → because [explanation]
Why-3: [statement] → because [explanation]
...
Why-N: [FIRST-PRINCIPLES ROOT CAUSE]

First-Principles Test:
- Condition: [pass/fail + evidence]
- On/Off: [pass/fail + evidence]
- Class: [pass/fail + evidence]
- Controllability: [pass/fail + evidence]
```

---

## Phase 3: Root Cause Audit

**Launch an independent audit agent** (separate subagent with fresh context) to score each quadrant.

### Audit Agent Instructions

Read `agents/rc_audit_agent.md` for full agent definition.

The audit agent scores each quadrant on 5 dimensions (0-3 scale):

| Dimension | 0 (Reject) | 1 (Weak) | 2 (Adequate) | 3 (Excellent) |
|-----------|-----------|----------|---------------|---------------|
| **Specificity** | Vague ("bad process") | Named but generic | Specific process + owner identified | Specific clause/step/gate with evidence |
| **Depth** | Stopped at symptom | Proximate cause | Systemic condition | Organizational design principle |
| **Verifiability** | No evidence possible | Plausible argument only | One verification method | Reproduction + suppression + IS/IS NOT consistency |
| **Controllability** | "Human nature" | Individual behavior | Team/process level | Organizational/architectural level |
| **Completeness** | Missing quadrants | Partial coverage | All four quadrants addressed | All four verified with cross-quadrant consistency |

**Reject threshold:** ANY dimension = 0, OR more than ONE dimension = 1 → REJECT.

On rejection, the audit agent provides:
- Which dimension(s) failed
- Specific "go deeper" challenge: "You stopped at [X]. Ask WHY [X] is possible. What process/system allows [X] to exist?"
- The analyst must re-do the 5-Why for that quadrant and resubmit

**Loop continues until ALL four quadrants pass ALL five dimensions ≥ 2.**

---

## Phase 4: Prevention Action Design

For each quadrant, propose an action. Q1/Q2 get corrective actions. Q3/Q4 get prevention actions.

### "Corrective or Preventive?" Gate Test

Every proposed action must pass THREE tests to be classified as prevention:

| Test | Question | Corrective (fail) | Preventive (pass) |
|------|----------|--------------------|--------------------|
| **Scope** | Does it prevent only THIS instance or the CLASS? | "Fixed this bug" | "Changed process so this bug class can't be created" |
| **Persistence** | Does it work without individual effort/memory? | "Retrained the developer" | "Static analysis rule blocks the pattern" |
| **Measurability** | Can a third-party auditor verify it's working in 6 months? | "Team is more careful now" | "CI dashboard shows 0 violations of the new rule" |

If ANY test fails → it's corrective, not preventive. Relabel and try again for Q3/Q4.

### Prevention Action Hierarchy (strongest to weakest)

1. **Eliminate**: Architecture makes the error impossible (Rust ownership, HAL enforcement)
2. **Detect at creation**: Tooling catches it at write-time (static analysis, linter rule)
3. **Detect before merge**: Process gate catches it (mandatory review checklist, CI check)
4. **Detect after merge**: Monitoring catches it (regression test, canary deployment)
5. **Mitigate impact**: Limit damage (graceful degradation, rollback mechanism)

Q3/Q4 prevention actions should aim for levels 1-3. Levels 4-5 are detection improvements, not prevention.

---

## Phase 5: Prevention Action Audit

**Launch the same audit agent** to review each prevention action.

The audit agent asks for each Q3/Q4 action:
1. Does it pass the Scope test? (class, not instance)
2. Does it pass the Persistence test? (systemic, not individual)
3. Does it pass the Measurability test? (auditable evidence)
4. Is it at hierarchy level 1-3? (eliminate/detect-at-creation/detect-before-merge)

**Reject if any test fails.** Provide specific feedback on what to change.

Common rejections:
- "Add a test" → corrective (detection improvement), not prevention. Ask: WHY wasn't this test required? Fix THAT.
- "Improve training" → fails persistence + measurability. Ask: what PROCESS CHANGE makes training unnecessary?
- "Be more careful" → fails all three tests. Not an action.
- "Code review" → only preventive if it's a NEW mandatory gate that didn't exist before, with a specific checklist item for this failure mode.

---

## Phase 6: Verification Plan

For each prevention action, define:

| Element | Description |
|---------|-------------|
| **Metric** | What specific measurement proves it's working? (e.g., "0 violations of static analysis rule X in 6 months") |
| **Data source** | Where does the measurement come from? (CI dashboard, audit log, defect database) |
| **Timeframe** | Minimum 6 months of monitoring post-implementation |
| **Success criteria** | Specific threshold (e.g., "0 recurrences of this defect class across all similar modules") |
| **Failure action** | What happens if the metric shows the prevention isn't working? |

---

## Phase 7: 8D Report Output

Use `templates/8d_report_template.md` for the final report format.

The report must include:
- D1: Team composition
- D2: IS/IS NOT problem definition
- D3: Containment actions (what was done immediately)
- D4: Four-quadrant root cause analysis (all 4 quadrants with 5-Why chains)
- D5: Corrective actions (Q1, Q2) with verification evidence
- D6: Prevention actions (Q3, Q4) with gate test results
- D7: Verification plan with metrics
- D8: Lessons learned + horizontal deployment plan

---

## Agent Team

| # | Agent | Role | Phase |
|---|-------|------|-------|
| 1 | Orchestrator (you) | Drive the analysis, ask WHYs, propose actions | All |
| 2 | `rc_audit_agent` | Independent scoring of root causes (5 dimensions, 0-3) | Phase 3, 5 |

### Sub-Agent Prompt Compliance

When launching the audit agent, you MUST:
1. Read `agents/rc_audit_agent.md` first
2. Include full file contents verbatim at top of subagent prompt
3. Provide the four-quadrant analysis as task context
4. Do NOT summarize the agent definition

---

## Common 8D Failures (Anti-Patterns)

| Failure | Why it happens | How this skill prevents it |
|---------|---------------|---------------------------|
| Only Q1 addressed | "Fix the bug and move on" | Audit agent rejects if any quadrant missing |
| Non-detection ignored | "We found it, that's what matters" | Q2/Q4 are mandatory; audit scores non-detection coverage |
| Prevention = corrective | "We added a test" (that's Q2, not Q4) | "Corrective or Preventive?" gate test |
| Root cause too shallow | "Developer made a mistake" | First-principles stopping criterion + audit depth scoring |
| No verification plan | "It's obviously fixed" | Phase 6 is mandatory; audit checks measurability |
| "Improve training" as prevention | Quick answer that avoids process change | Audit explicitly rejects; persistence + measurability tests fail |

---

## Output Language

Match user's language. Technical terms (8D, MRC, IS/IS NOT, FMEA, Kepner-Tregoe) stay in English.
