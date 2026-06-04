# MRC Proportionality: Stop the Over-Engineered "Garbage" Output

Date: 2026-06-04
Status: DRAFT — design direction approved (the ☆ points + why); garbage-fix half of the two-spec MRC repair
Scope: skill-ai-escape-mrc (phase_1/2 router + phase_4/5 + prompts + schemas)

<!-- # WIKI-CONSULTED: degraded-emission-with-warning -->
<!-- WIKI-FINDING: the "每三個月檢查一次" prevention is a degraded/theater artifact the producer
     shipped anyway; the report even documented its own ineffectiveness. Fix at the producer. -->
<!-- # WIKI-CONSULTED: instruction-failure-escalation-ladder -->
<!-- WIKI-FINDING: a scheduled-review/administrative control is a Rung-1/2 decaying control; the
     hierarchy-of-controls maps onto the prevention_hierarchy 1-5 — penalize weak controls. -->

---

## 1. Problem & Context

The `tty/100%` run produced a headline MRC prevention of **"charter a quarterly Policy-Engine Completeness Review (每三個月檢查一次)"** — bureaucratic theater for a one-off behavioral miscalibration. The report's own `failure_mode_of_prevention` admitted it wouldn't work (ritual-as-theater, owner-without-teeth). Three coupled root causes generate and preserve this garbage:

- **G1 — Forced 4-quadrant fill.** `phase_2` and `phase_4` always produce MRC-NC and MRC-ND (management-system) root causes + preventions, even for a purely local incident. Research: **forced mandatory template fields cause LLM confabulation** — the model invents grand governance theory to fill a slot that has no real content.
- **G2 — No proportionality axis.** `PREVENTION_ACTION.gate_test` rewards only `{scope, persistence, measurability}`. A quarterly-review ritual scores PASS on all three (class-level, embedded-in-YAML, auditable), so the gate's gradient points *toward* bureaucracy. Nothing checks whether the control's cost/permanence is proportionate to the incident, or whether it's a weak (administrative) control where a strong (eliminating) one fits.
- **G3 — Phase-5 audit only adds.** `_apply_fixes` appends `audit_notes`; the audit verdict enum is `{CONTINUE, EXHAUSTED, REWORK}`. There is no path to say "this is over-scoped — cut it." The one quality-control phase can only inflate.

## 2. Design (defense-in-depth; conservative by default)

Three changes. The router is the root fix (don't force-fill); the proportionality axis + OVER_SCOPED verdict are the back-stop (prune what still gets generated).

### 2a. Incident-class router (front valve) — **default is ANALYZE**

A classification step (extend `phase_1` IS/IS-NOT, emit into state) decides MRC applicability:

- Emit `mrc_applicable: bool` + `mrc_applicability_justification: str`.
- **Default `True`** (fail-safe toward full analysis). The router may set it `False` **only** when it can positively justify that the incident has no plausible management-system contributory gap — i.e. a **local, non-recurring, technical/behavioral one-off** (research: systemic root cause is for *recurring* issues; local one-offs warrant limited scope). Recurrence, cross-surface pattern, or any prior same-class escape ⇒ `True`.
- When `False`: `phase_2` skips the MRC quadrants (q3_mrc_nc, q4_mrc_nd) and `phase_4` runs **corrective-only** (Q1/Q2). The report records "MRC quadrants: N/A — <justification>" (an explicit, honest N/A, not a confabulated root cause).

Mechanism: derive the run's **active quadrants** from `mrc_applicable` instead of the hardcoded `QUADRANTS` / `PREVENTION_QUADRANTS`. `phase_2`, `phase_3` (RC audit), `phase_4`, `phase_5` all read the active set.

### 2b. Proportionality axis (gate) — 4th `gate_test` key

Add `proportionality: PASS|FAIL` + `proportionality_evidence` to `PREVENTION_ACTION.gate_test`. `prevention_action.txt` gains the rule:

> **proportionality:** the control's cost and permanence must match the incident's severity × recurrence, and it must sit as high on the prevention hierarchy as feasible. A **Rung-4/5 administrative control** (scheduled review, periodic audit, "check every N months", a new standing role/ritual) for a **one-off / low-severity** incident is **FAIL** — prefer elimination / detect-at-creation / detect-before-merge (Rung 1-3). A control whose own failure mode is "nobody actually does it" (human-compliance-dependent) is FAIL when a structural control is available.

Grounded in hierarchy-of-controls (administrative = weakest, compliance-dependent, "backup") and risk-based-corrective-action (proportional to actual threat). `gate_test.required` becomes `[scope, persistence, measurability, proportionality]`.

### 2c. Phase-5 OVER_SCOPED verdict (audit can cut)

Add `OVER_SCOPED` to `PREVENTION_AUDIT.verdict` enum and a new weakness `classification: "OVER_SCOPED"`. `phase_5._apply_fixes` gains a branch: on an `OVER_SCOPED` weakness for a quadrant, **replace** that prevention's control with the auditor's proportionate alternative (or mark it `downscoped` with the cut recorded), instead of only appending a note. The audit prompt (`prevention_audit.txt`) is told to emit `OVER_SCOPED` when a control fails the proportionality axis — e.g. a quarterly ritual where a one-line structural gate would do.

## 3. Why this kills the `三個月檢查一次` garbage

- The quarterly-review prevention only existed because **MRC-NC/ND were force-filled** for a local incident → with the router, a one-off behavioral miscalibration runs **corrective-only**; no management-root-cause slot to confabulate into. (Removes G1, the generator.)
- Even if MRC runs, a scheduled-review control now **FAILs the proportionality axis** (Rung-5 administrative, compliance-dependent) → the gate stops rewarding it. (Removes G2, the gradient.)
- And Phase-5 can now return **OVER_SCOPED** and **cut** the bloated control down to the proportionate one, instead of only adding more. (Removes G3, the ratchet.)

## 4. Files & changes

| # | File : symbol | Change |
|---|---|---|
| 1 | `ai_escape_mrc/state.py` | helper `active_quadrants(state)` + `active_prevention_quadrants(state)` deriving from `mrc_applicable` (default all 4) |
| 2 | `phases/phase_1_is_isnt.py` | emit `mrc_applicable` + `mrc_applicability_justification` (LLM classification; default True; False only with positive local/one-off justification) |
| 3 | `phases/phase_2_why_analysis.py` | iterate `active_quadrants(state)` not `QUADRANTS` |
| 4 | `phases/phase_3_rc_audit.py` | audit only active quadrants |
| 5 | `phases/phase_4_actions.py` | `PREVENTION_QUADRANTS` → `active_prevention_quadrants(state)`; corrective-only when MRC N/A |
| 6 | `phases/phase_5_prevention_audit.py` | handle `OVER_SCOPED`: cut/replace the control, not just append |
| 7 | `schemas.py` | `PREVENTION_ACTION.gate_test` += `proportionality` (+required); `PREVENTION_AUDIT.verdict` += `OVER_SCOPED`; weakness classification += `OVER_SCOPED` |
| 8 | `prompts/prevention_action.txt` | add the proportionality rule (hierarchy-of-controls grounding) |
| 9 | `prompts/prevention_audit.txt` | instruct emitting `OVER_SCOPED` on proportionality failure + a proportionate alternative |
| 10 | `phases/phase_7_report.py` / render | render "MRC quadrants: N/A — <justification>" honestly when not applicable |

## 5. Error handling / safety

- Router defaults to `mrc_applicable=True` on any classifier uncertainty or LLM failure (fail-safe to full analysis — never silently under-analyze).
- The proportionality axis is additive; existing 3 axes unchanged.
- `OVER_SCOPED` cut must record what was cut + the replacement in the action (auditable; no silent deletion).

## 6. Testing

1. **Router default:** a recurring/cross-surface incident → `mrc_applicable=True`; all 4 quadrants run (regression: no behavior change for systemic incidents).
2. **Router N/A:** a local one-off (synthetic problem statement) → `mrc_applicable=False` with justification; phase_4 produces corrective-only; report shows "MRC: N/A — <reason>".
3. **Router fail-safe:** classifier exception → `mrc_applicable=True` (analyze).
4. **Proportionality FAIL:** a prevention action that is a quarterly-review ritual for a one-off → `gate_test.proportionality == FAIL`.
5. **Proportionality PASS:** a structural Rung-1/2 control proportionate to a recurring incident → PASS.
6. **OVER_SCOPED cut:** phase_5 audit returns `OVER_SCOPED` → the prevention's control is replaced/downscoped (recorded), not just annotated.
7. **Anti-regression of the witnessed garbage:** drive the tty/100%-style local-behavioral problem end-to-end (stubbed LLM) → assert the emitted prevention set contains NO standing-ritual/"every N months" control surviving the gate.

## 7. Research citations

- RCA depth scales to severity; triage-first (coarse → "good enough"): PagerDuty, Splunk incident severity; arxiv goal-driven RCA survey.
- Systemic root cause for *recurring* issues; local one-offs limited scope: NetSuite/SixSigma RCA.
- Hierarchy of controls — administrative (scheduled review) weakest, compliance-dependent, "backup": CDC NIOSH, OSHA.
- Risk-based corrective action proportional to threat; over-control → bureaucracy maze: APM, sustainability-directory risk-based-corrective-action.
- Forced mandatory template fields → LLM confabulation (the G1 mechanism): arxiv 2511.07722, Prodigy template-filling guidance.
- CAPA effectiveness / decaying control / periodic-review weakness: thefdagroup, pharmaceuticalonline.
