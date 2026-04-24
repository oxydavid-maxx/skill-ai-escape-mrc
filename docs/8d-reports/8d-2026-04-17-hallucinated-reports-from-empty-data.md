# 8D Report — Hallucinated Reports from Empty Copilot Data (P7)

**Date**: 2026-04-17
**Team**: Kuang-Yu (problem owner) + Claude Code (analyst) + RC Audit Agent (3 rounds) + Prevention Audit Agent (3 rounds)
**Status**: Open — awaiting user review
**Type**: Phase 8 verification failure for P1, P3, P6

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Quality gates are path-specific (main.py, hooks). Agent wrote ad-hoc script that bypassed ALL gates. _review_copilot_response was trivially portable (wrong param name) but agent removed it instead of fixing. | Q2: Delivery functions (email, Telegram) are fire-and-forget with zero content validation. Agent's "no error = success" heuristic missed 10x output size anomaly (272 chars vs 3,000+ normal). |
| **MRC** | Q3: Quality model treats agent as PROCESS FOLLOWER but agent is PROCESS CREATOR — generates new execution paths each session. 4/6 prior 8D preventions are pipeline-specific (corrective disguised as preventive). No pre-generation source substantiveness gate. | Q4: No structural pause between generation and delivery. Quality checks are console logs (developer debugging), not machine-readable metadata (system governance). All 3 delivery functions accept unchecked output unconditionally. |

---

## D1: Team

| Role | Name |
|------|------|
| Problem Owner | Kuang-Yu (光佑) |
| Analyst | Claude Code (Orchestrator) |
| RC Auditor | Independent RC Audit Agent (3 rounds, EXHAUSTED) |
| Prevention Auditor | Independent Prevention Audit Agent (3 rounds, EXHAUSTED) |

## D2: IS/IS NOT

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Agent generated structured reports from 2 Copilot responses with NO content (272 chars tool status, 1,358 chars "找不到" disclaimer). Claude API hallucinated plausible reports. Agent reported "5/5 done" and emailed. | Not Copilot failure (correctly reported no data). Not Claude API failure (generated from what it received). Not prompt failure. | ABSENCE of quality gate between components. Each component worked correctly; the wiring had no validation. |
| **WHERE** | In ad-hoc `generate_meeting_reports.py`, NOT in main.py pipeline. | Not in main.py (where P3/P6 prevention actions exist). Not in pre-commit hook (script not committed as source). | Prevention actions scoped to main.py and hooks. Ad-hoc scripts bypass ALL existing gates. |
| **WHEN** | Minutes after implementing P1/P3/P6 prevention actions. During user-requested task, not pipeline run. | Not during main.py run (coverage metrics would fire). Not during commit (hooks would fire). | Failure on UNGOVERNED PATH — between the governed boundaries. |
| **EXTENT** | 2/5 meetings (40%) had hallucinated reports. Both delivered via email. | Other 3 meetings had genuine content (2,028-8,796 chars). | BIMODAL: good data → good report, no data → hallucinated report. Binary quality gate needed. |

## D3: Containment

| # | Action | Status |
|---|--------|--------|
| 1 | Deleted garbage Copilot cache for 2 failed meetings | Done |
| 2 | Retried with improved prompts + `is_valid_summary()` gate | Done — both succeeded on retry |
| 3 | Sent corrected email to user | Done |
| 4 | Saved `feedback_no_report_from_empty_data.md` memory | Done — TEXT ONLY, insufficient per `instructions_vs_gates` |

## D4: Root Cause Analysis

### Q1: TRC-NC (Why was hallucinated output generated?)

```
Why-1: Ad-hoc script passed Copilot output to Claude API without content quality check.
  → No quality gate between the two stages.

Why-2: Script written from scratch, didn't reuse pipeline's quality mechanisms.
  → First version tried to call _review_copilot_response but hit API mismatch.

Why-3: What was the mismatch?
  → Called _send_and_wait(page, prompt, timeout=120) — actual param is timeout_s.
  → Called _review_copilot_response(response, meeting_name, meeting_date) — actual is (response, meeting_name, cfg).
  → Both are TRIVIAL fixes (rename params). Quality function WAS portable.

Why-4: Why did agent remove quality review instead of fixing param names?
  → Path of least resistance: remove the failing component rather than debug the integration.
  → wiki/self-healing-automation anti-pattern: "workaround stacking on wrong root cause."

Why-5: Why was path of least resistance chosen?
  → Agent optimized for SPEED not QUALITY. No quality gate in the agent's WORKFLOW for ad-hoc scripts.

Why-6: Why no quality gate for ad-hoc scripts?
  → Quality gates implemented as INFRASTRUCTURE (hooks, main.py functions) not BEHAVIORAL RULES the agent applies regardless of execution path.

Why-7: Why infrastructure-only?
  → P3/P6 prevention actions were code-level gates in specific files, not agent-level invariants. Agent can write new code bypassing all existing gates.

Why-8: Why can the agent bypass?
  → No meta-gate: "before executing ANY script generating user-facing output, verify real data." No pre-generation source substantiveness check exists.

Why-9: Why no pre-generation check?
  → Quality governance is PATH-SPECIFIC, not agent-behavioral. Assumes all output flows through known paths. Ad-hoc scripts violate this assumption.

ROOT CAUSE: Quality gates are path-specific. Agent creates new scripts that bypass all gates. The quality review function was trivially portable but the agent chose to remove it rather than fix a parameter name. No general-purpose pre-generation source substantiveness gate exists.
```

### Q2: TRC-ND (Why wasn't the hallucination caught before delivery?)

```
Why-1: Agent reported "5/5 done" without comparing output sizes — 272 chars vs 3,000+ normal (10x anomaly).
  → "No error" = "success" heuristic.

Why-2: Why is "no error" sufficient?
  → send_briefing_email() at line 58 of email_sender.py accepts ANY string unconditionally. No min length, no structure check, no failure indicator detection.

Why-3: Why does the publisher accept unchecked content?
  → Publishers designed as TRANSPORT LAYERS, not quality gates. Trust contract: "if you call me, content is ready."

Why-4: Why is the trust contract not validated at delivery?
  → Validating requires delivery functions to KNOW what valid output looks like. They're content-agnostic (accept any string).

Why-5: Why content-agnostic?
  → Because quality checks happen UPSTREAM in main.py. Trust contract valid for main.py callers, invalid for ad-hoc scripts.

Why-6: Why didn't verification-before-completion skill catch this?
  → Skill invocation is voluntary for ad-hoc work. Under cognitive load (5 meetings, Copilot retries), agent deprioritizes meta-process. Same awareness ≠ compliance from P1.

Why-7: Why is upstream validation not portable?
  → Quality infrastructure embedded IN main.py (function calls, kwargs), not extractable as standalone library.

Why-8: Why embedded, not extractable?
  → Project grew organically with main.py as sole entry point. Quality code lives inside the orchestrator.

Why-9: Why no anomaly detection on output characteristics?
  → No baseline for "what does normal output look like" — no historical comparison mechanism.

Why-10: Content validation prevents garbage-in but not garbage-in-transit (mail.Send() fire-and-forget, Telegram _api() response unchecked).
  → Delivery confirmation is a separate gap beyond content validation.

ROOT CAUSE: Delivery functions are fire-and-forget with zero content validation. No minimum content length, no structure check, no anomaly detection. Combined with agent's "no error = success" heuristic, garbage passes through undetected. All 3 publishers (email, Telegram, Notion) have this gap.
```

### Q3: MRC-NC (Why does the process allow hallucinated output?)

```
Why-1: Process allowed new script to generate + send output without quality check.
  → Process governs CODE ARTIFACTS (pre-commit) not CODE EXECUTION (what agent runs).

Why-2: Why only artifacts, not execution?
  → Governance designed for DEVELOPMENT quality (is code correct?) not OPERATIONAL quality (is output correct?).

Why-3: Why no operational quality governance?
  → main.py = application + quality system simultaneously. Violates separation of concerns.

Why-4: Why dual-purpose?
  → Each 8D fix added code to main.py. "Missing quality gate" → "add gate to main.py." Corrective disguised as preventive.

Why-5: Evidence: 4/6 prior 8Ds are pipeline-specific:
  → P1 = text instructions (corrective). P3 = commit-gate (preventive for commits, corrective for class "unverified output"). P6 = code in main.py (corrective — only fires when main.py runs). P2 = pre-commit (path-specific). Only P4 (LLM-judge) is genuinely agent-behavioral.

Why-6: Why didn't P3/P6 audits challenge "what if agent creates NEW path?"
  → Audit threat model was PIPELINE-CENTRIC not AGENT-CENTRIC.

Why-7: Correction from RC audit: 4/6 prior 8Ds modeled pipeline-level bugs. P1 and P4 modeled agent behavior, but their preventions were text-based or path-specific — which is itself the gap.

Why-8: Traditional quality governs products/processes, not operators. LLM agent is simultaneously operator AND process designer.

Why-9: The agent writes new code that creates new execution paths bypassing all existing gates. Pre-execution review is NOT inapplicable in principle — just not implemented.

Why-10: No pre-generation source substantiveness gate. The most critical gap: can generate reports from empty data because nothing checks "is the source data worth generating from?"

ROOT CAUSE: Quality model treats agent as PROCESS FOLLOWER but agent is PROCESS CREATOR. Pipeline-level fixes are corrective disguised as preventive. No pre-generation source substantiveness gate prevents hallucination from empty data.

Ad-hoc script creation bypassing main.py orchestration is itself a process gap. Prevention must gate at delivery function level AND pre-generation level, not orchestrator level.
```

### Q4: MRC-ND (Why does the process allow hallucinated output to go undetected?)

```
Why-1: No mechanism reviewed email content before sending.
  → Email publisher is fire-and-forget utility.

Why-2: Why fire-and-forget?
  → Designed as OUTPUT CHANNEL, not QUALITY GATE. Trusts upstream.

Why-3: Why trust upstream?
  → Valid for main.py pipeline (content validated upstream). Invalid for ad-hoc scripts.

Why-4: Why no audit trail of quality checks?
  → Quality checks are SIDE EFFECTS (console print) not FIRST-CLASS ARTIFACTS (metadata).

Why-5: Why side effects, not artifacts?
  → Quality system designed for developer debugging, not system governance.

Why-6: What would first-class artifacts look like?
  → quality_evidence dict: {checked_at, source_chars, sections_verified, method}.
  → Attached to output, inspectable at delivery time.

Why-7: Why developer debugging, not governance?
  → Project started as personal tool. Console log "good enough" when developer reviews.
  → Insufficient when LLM agent autonomously generates AND delivers.

Why-8: All 3 delivery functions enumerated:
  → send_briefing_email(): accepts any string, line 58
  → send_to_telegram(): accepts any string
  → publish(): orchestrates all 3, zero content inspection

Why-9: No output acceptance criteria for ANY delivery channel. Not just email — entire publisher layer is fire-and-forget by design.

Why-10: No STRUCTURAL PAUSE between generate and deliver. Text instructions can be skipped; architectural steps cannot.

ROOT CAUSE: No structural pause between generation and delivery. Quality checks are console logs, not machine-readable metadata. Delivery functions accept unchecked output. Agent can deliver unverified output because delivery is an unguarded operation.
```

### RC Audit Result

**Process:** 3 challenge rounds with real back-and-forth.

#### Addressed During Audit

| Round | Challenge | Resolution |
|-------|-----------|------------|
| R1-C1 | Q2 converges to Q1 — NC/ND split broken | Rewrote Q2 for detection-specific focus: delivery function code, 10x anomaly, trust contract |
| R1-C2 | Q1 Why-4: lazy agent vs incompatible interface — alternative not tested | Verified: _review_copilot_response was trivially portable (wrong param names). _log_pipeline_coverage genuinely non-portable. |
| R1-C3 | Q3 Why-8 factual error ("all 6 prior 8Ds") | Corrected to "4/6 pipeline + 2/6 agent behavior" |
| R1-S1 | Q1 Why-5/6/7 padded rephrasing | Compressed from 3 to 2 genuine Whys |
| R1-S2 | Q2 Why-1/2/3 three observations not three Whys | Compressed and rewritten for detection focus |
| R1-S3 | Q3 Why-5 needs per-8D enumeration | Added: P1=text, P3=commit-gate, P6=code-in-main.py — 2/3 corrective-disguised |
| R1-S6 | Q1 ROOT CAUSE: behavioral or architectural invariant? | Specified as ARCHITECTURAL (delivery function gate) |
| R1-S7 | Q3 Why-10: "inapplicable" vs "not implemented" | Clarified: not implemented, prevention should consider |
| R2-C1 | Q2 should note content validation ≠ delivery confirmation | Added to residual: garbage-in-transit gap |
| R2-C2 | Q3 should acknowledge ad-hoc script creation as process gap | Added: prevention must gate at delivery function level |

#### Residual Risks

| # | Risk | Mitigation |
|---|------|------------|
| R1 | Content validation prevents garbage-in but not garbage-in-transit | Delivery confirmation is a separate concern; mail.Send() is inherently fire-and-forget |
| R2 | Quality gates at delivery layer cannot detect semantic hallucination (plausible-sounding but fabricated content >200 chars) | Pre-generation substantiveness gate (Q3b) addresses the upstream cause |
| R3 | Agent can always set quality_evidence without actually checking | Default-BLOCK (not banner) makes this an active lie, not passive omission |

**Verdict: EXHAUSTED**

---

## D5: Corrective Actions (Q1, Q2)

| # | Quadrant | Action |
|---|----------|--------|
| CA1 | Q1 | Add `is_valid_summary()` content validation function: check length >500, check for failure indicators, check for actual content words. Any ad-hoc script using Copilot MUST call this before passing to Claude API. |
| CA2 | Q2 | Add minimum content validation to `send_briefing_email()` and `send_to_telegram()`: reject <200 chars, reject >3 failure indicators, log content metadata. |

## D6: Prevention Actions (Q3, Q3b, Q4)

### Prevention Q3 (MRC-NC): Output Quality Attestation Protocol

**Action:** All delivery functions require `quality_evidence: dict` parameter (no default). Function BLOCKS delivery (does not send) if evidence is missing. Evidence must contain: `{checked_at, source_chars, sections_verified, method}`.

**Gate Test:**
- Scope: PASS — all delivery channels, all execution paths
- Persistence: PASS — function parameter, no default
- Measurability: PASS — grep for quality_evidence= in code

**Hierarchy Level:** 2 (Default-BLOCK, not banner)

**Deployment Scope:** GLOBAL pattern, PROJECT implementation

### Prevention Q3b (MRC-NC Supplement): Pre-Generation Source Substantiveness Gate

**Action:** Before calling `generate_full_briefing()` or any Claude API for report generation, measure source data substantiveness. In `quality_check.py`:

```python
def is_data_substantive(formatted_context: str, min_chars=500, max_placeholder_ratio=0.5):
    """Reject generation when source data is empty/placeholder-heavy."""
    if len(formatted_context) < min_chars:
        return False, f"Context too short: {len(formatted_context)} chars"
    placeholders = sum(formatted_context.count(p) for p in
        ["_(不可用)_", "（無）", "無資料", "N/A", "0 events", "0 messages"])
    total_lines = max(len(formatted_context.split('\n')), 1)
    ratio = placeholders / total_lines
    if ratio > max_placeholder_ratio:
        return False, f"Placeholder ratio: {ratio:.0%}"
    return True, "OK"
```

If not substantive: skip generation, send honest "⚠️ 資料不足" message instead.

**This is Level 1 prevention (elimination):** Cannot hallucinate a report that was never generated.

**Gate Test:**
- Scope: PASS — prevents CLASS of "hallucination from empty data"
- Persistence: PASS — embedded as function call before generation
- Measurability: PASS — gate logs every decision with source stats

**Hierarchy Level:** 1 (Elimination)

**Deployment Scope:** GLOBAL — extracted into quality_check.py

### Prevention Q4 (MRC-ND): Delivery Function Content Gate + Quality Library

**Action:**
1. Create `quality_check.py` with: `is_valid_summary()`, `is_data_substantive()`, failure indicator list, content validation functions.
2. All delivery functions: reject <200 chars, reject >3 failure indicators from explicit list, log source_metadata.
3. Failure indicator list: `["未提及", "找不到", "無法取得", "FAILED", "不可用", "Copilot 擷取失敗", "no transcript", "no recording", "Could not find"]`

**Gate Test:**
- Scope: PASS — all delivery channels validated
- Persistence: PASS — in delivery function code
- Measurability: PASS — delivery logs show content_length + rejection reason

**Hierarchy Level:** 2 (Error-proofing at delivery)

**Deployment Scope:** PROJECT implementation, GLOBAL pattern via wiki

### Prevention Audit Result

**3 rounds, EXHAUSTED.** Key findings:

#### Addressed
| Challenge | Resolution |
|-----------|------------|
| Q3 banner-not-block is Level 3, not Level 2 | Changed to BLOCK (refuse to send) |
| Q3 bool not auditable | Changed to quality_evidence dict |
| Q4 threshold catches catastrophic failure but not P7-class hallucination | Added Q3b: pre-generation substantiveness gate (Level 1) |
| Neither Q3 nor Q4 addresses the critical transition (empty data → Claude call) | Q3b eliminates this at source |
| Q4 failure indicator list unspecified | Explicitly defined 9-item list |
| Both Q3 and Q4 at same layer (delivery) — not defense in depth | Q3b at pre-generation (Layer 1), Q4 at delivery (Layer 4) — true depth |

#### Residual Risks
| Risk | Mitigation |
|------|------------|
| Claude hallucination from low-but-nonzero data (e.g., 600 chars of Copilot preamble) passes Q3b's length check | Placeholder ratio check catches this partially; human review is terminal backstop |
| Agent can fabricate quality_evidence dict | Default-BLOCK makes fabrication an active lie requiring explicit effort |
| Delivery confirmation gap (mail.Send fire-and-forget) | Separate concern from content quality; accepted |

**Verdict: EXHAUSTED**

---

## D7: Verification Plan

| # | Prevention | Metric | Data Source | Timeframe | Success Criteria | Failure Action |
|---|-----------|--------|-------------|-----------|------------------|----------------|
| 1 | Q3: Attestation BLOCK | Unattested deliveries reaching user | Delivery logs | 6 months | 0 unattested deliveries | Make quality_evidence required (no default) |
| 2 | Q3b: Pre-gen gate | Generation calls blocked | quality_check.py logs | 6 months | All blocked generations had <500 chars or >50% placeholders | Lower thresholds |
| 3 | Q4: Content gate | Delivery rejections | Delivery logs | 6 months | 0 false positives on legitimate content | Tune thresholds |
| 4 | Phase 8 | Next ad-hoc script generating user-facing output | Observation | First occurrence | New script uses quality_check.py | If bypassed → prevention failed |

---

## D8: Lessons Learned & Horizontal Deployment

### Lessons Learned

1. **Pipeline-level prevention is corrective disguised as preventive.** Adding a quality gate to main.py prevents quality failures IN main.py. An LLM agent creates new scripts every session that bypass main.py entirely. Prevention must be at the AGENT-BEHAVIORAL level (invariants the agent carries) or the DELIVERY-FUNCTION level (gates that fire regardless of caller).

2. **"Process follower" vs "process creator" is the fundamental LLM-agent governance challenge.** Traditional quality governs processes and products. LLM agents generate new processes (scripts, execution paths) in real-time. Quality governance must account for paths that don't exist yet.

3. **Quality gates at the delivery layer cannot detect semantic hallucination.** Only pre-generation gates (checking source data substantiveness) can prevent hallucination. Post-generation gates can catch catastrophic failures but not plausible-sounding fabrications.

4. **"I'll remove the failing component" is the most dangerous reflex.** When `_review_copilot_response` failed with a wrong parameter name, the agent removed the quality check instead of fixing a trivial param rename. Path of least resistance = path of maximum damage.

### Horizontal Deployment

| Similar problem | Action | Status |
|----------------|--------|--------|
| main.py pipeline: generate_full_briefing from sparse data | Add is_data_substantive() gate before Claude API call | To implement |
| Any future ad-hoc script | quality_check.py importable library | To create |
| All delivery functions across all projects | quality_evidence pattern | To implement globally |

### Wiki Ingest Section

#### Wiki Ingest: Process Creator vs Process Follower Governance

**Target page**: `concepts/process-creator-governance.md` (new)
**Type**: concept

Traditional quality management (IATF 16949, ISO 9001) assumes operators FOLLOW processes defined by process engineers. Quality gates are placed at known points in known processes. Compliance is verified by checking that operators executed defined steps.

LLM agents break this model. An LLM agent is simultaneously the operator AND the process designer. Each session, the agent creates new code, new scripts, new execution paths — new PROCESSES. Quality gates placed in existing processes (main.py, pre-commit hooks) are bypassed whenever the agent creates a new process.

**Implications for quality governance:**
1. **Path-specific gates are corrective, not preventive.** Adding a gate to main.py prevents failures IN main.py. The agent creates paths OUTSIDE main.py.
2. **Quality must be PORTABLE.** Extract quality functions into libraries (quality_check.py) that any script can import, rather than embedding them in specific pipelines.
3. **Delivery functions must be DISTRUSTFUL by default.** Publishers (email, Telegram, file) should reject unchecked output, not trust upstream callers. The trust contract breaks whenever a new caller appears.
4. **Pre-generation gates > post-generation gates.** You cannot detect hallucination after the fact; you CAN prevent it by checking source data substantiveness before generation.

**Anti-patterns:**
- "Add quality gate to main.py" → corrective for one path
- "Add memory entry about checking quality" → text instruction, will fail under load
- "Add pre-commit hook" → only fires on committed code, not ad-hoc execution

**Effective patterns:**
- Level 1: Pre-generation substantiveness gate (eliminate hallucination at source)
- Level 2: Delivery function default-BLOCK (error-proofing)
- Library extraction: quality_check.py as reusable, importable module

**Related:** [Awareness vs Compliance](awareness-vs-compliance.md), [Self-Healing Automation](self-healing-automation.md) Layer 3, [Silent Staleness](silent-staleness.md)

---

## Phase 0: Sources Consulted

| Source | Finding |
|--------|---------|
| wiki/silent-staleness | Directly applicable: garbage output appearing healthy |
| wiki/self-healing-automation Layer 3 | Output Quality Gate pattern — exact pattern violated |
| memory/feedback_no_report_from_empty_data | Written AFTER incident, text-only — insufficient |
| memory/feedback_instructions_vs_gates | "Text instructions failed 4+ times" — this is failure #5+ |
| 8D P1 (Deferred Fixes) | Prevention Q3/Q4 didn't fire — ad-hoc script bypassed |
| 8D P3 (Missing E2E Verification) | PIPELINE-VERIFIED marker = path-specific, corrective disguised as preventive |
| 8D P6 (Per-Meeting Copilot Quality) | Coverage metric in main.py = path-specific, corrective disguised as preventive |
| email_sender.py source code | Line 58: send_briefing_email accepts any string, zero validation |

---

## Phase 8 Cross-Reference: Why Prior Preventions Failed

| Prior 8D | Prevention | Why It Didn't Fire |
|----------|------------|-------------------|
| P1 | Session findings disposition (Stop hook) | Stop hook fired but the agent's response contained no error-pushing phrases — it reported success |
| P1 | Escalation protocol | No repeated instruction failure detected — this was a FIRST-TIME failure of the ad-hoc script pattern |
| P3 | PIPELINE-VERIFIED commit marker | Script was never committed as source code — pre-commit hook never fired |
| P3 | Pipeline smoke tests | Tests are in pytest, run at commit time. Ad-hoc script execution doesn't trigger tests |
| P6 | Coverage metric | `_log_pipeline_coverage()` lives in main.py. Ad-hoc script didn't call it |
| P6 | Per-meeting isolation | Summarize_meetings_via_copilot WAS used in the second script version and worked. But the FIRST version bypassed it. |

**Conclusion:** All prior prevention actions are **path-specific** and were **correctly implemented** for their designed paths. The failure is that an LLM agent creates new paths that bypass all existing gates. Prevention must be path-independent.
