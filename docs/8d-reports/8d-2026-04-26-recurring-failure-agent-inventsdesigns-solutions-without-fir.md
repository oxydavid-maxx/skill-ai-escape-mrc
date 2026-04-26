# 8D Report: Recurring Inventing-Instead-of-Researching (Managed Agents Migration Brainstorm)

**Date**: 2026-04-26T09:54:19.211580
**Problem**: Recurring failure: agent invents/designs solutions without first researching how others solve the same problem (CLAUDE.md "Always search online first" rule). Today 2026-04-26: agent presented full Managed Agents migration design (12 sections, full architecture diagram, risks table) WITHOUT doing any web research on how the migration is actually done. User had to call this out: "is this how people do this? did you do web search? if not, why?" Agent then did 2 searches and discovered 4 major design errors (artifacts location, migration pattern, network egress, session model) — all of which would have been caught upfront with research. This is the THIRD instance of the same generative class within one session (other two: degraded-emission-with-warning and the .next-session-primer 作秀), all caught by user not gate.
**Run ID**: run-1777167372-ba8cf6d8
**Model**: Claude Sonnet (skill-8d-mrc orchestration)
**Generative Class (registered post-hoc)**: gate-enforcement-boundary-downstream-of-failure-mode

---

## Pipeline Timeline

| Phase | Activity | Outcome |
|-------|----------|---------|
| Phase 0 | Dual-tier research: SoA scan for upstream-vs-downstream gate patterns; meta-domains: aviation pre-flight, patent prior-art, clinical trial IRB | Identified 3 meta-categories and 3 meta-domains anchoring the structural argument |
| Phase 1 | IS / IS NOT 4-dimensional scoping (what / where / when / extent) | Narrowed enforcement surface to UserPromptSubmit→Skill-PreToolUse→Stop-regex chain; eliminated Write-tool boundary as a viable surface |
| Phase 2 | Why chains, all 4 quadrants, depth ≥10 | q1_trc_nc reached Why 12 (no shared per-turn state primitive); q2_trc_nd reached Why 12 (unowned closed-loop predicate-narrowness telemetry); q3_mrc_nc reached Why 10 (open-loop rule-lifecycle governance); q4_mrc_nd reached Why 13 (single-ritual governance covers consolidation but not coverage/recurrence) |
| Phase 3 | RC audit, 3 rounds | Round 1 verdict CONTINUE; Round 2 CONTINUE; Round 3 CONTINUE; chain converged on the upstream event-vocabulary inheritance and open-loop governance roots |
| Phase 4 | Corrective + Prevention authoring per quadrant | Corrective q1+q2 shipped (PreToolUse Skill hook + Stop-hook regex denylist); Prevention q3+q4 (rule-lifecycle gate + class-recurrence pipeline) |
| Phase 5 | Prevention audit, 3 rounds | Round 1 CONTINUE; Round 2 CONTINUE; Round 3 EXHAUSTED. Strengthened: failure_cost evidence-binding, multi-rule receipt pairing, hierarchy_level relabel to 3 (hard gate), ticket reader-binding, bootstrap fail-closed semantics, recurrence threshold tier-indexed |
| Phase 6 | Verification plan + Proof-of-Action per quadrant | Per-quadrant metrics, baselines, schedules, failure-response defined; Phase 8 trigger conditions enumerated |
| Phase 7 | SoA citation deduplication | Three meta-domain anchors retained as governance precedent |
| Phase 8 | Closure audit | Pending — closure conditional on regression test 2026-04-28 and shadow-mode review 2026-05-03 |

**LLM call summary**: Phase 0 research (2 SoA passes); Phase 2 (4 quadrant chain generations); Phase 3 (3 audit rounds × 4 quadrants); Phase 4 (4 quadrants × 2 action-types); Phase 5 (3 audit rounds × 2 prevention quadrants); Phase 6 (4 verification plans). Loop-backs: Phase 3 R2 surfaced layer-mixing in q1 (Whys 9, 10) → relocated to q3; Phase 5 R2 surfaced multi-rule-commit loophole → fixed in R3; Phase 5 R3 surfaced hierarchy-level mislabel → relabeled to 3.

**SoA queries that yielded useful results**: "policy-as-code SLSA in-toto attestation severity binding" → fed Q3 failure_cost evidence-binding fix. "Long-running progress heartbeat governance ritual" → fed Q3 escalator heartbeat sub-control. "OPA Conftest author-supplied severity untrusted" → fed Q3 garbage-in mitigation. "Aviation pre-flight checklist gate placement" → fed structural argument that gate must be upstream of damage. **Empty queries**: "harness streaming-content hook event LLM agent" (no first-party Anthropic hook event for mid-stream inspection — confirms residual at q1 Why 12).

---

## Section A: Root Cause Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                       | Non-Detection (ND)                                                                                                                                                                                                   |
|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: No shared per-turn precondition-state primitive in the hook architecture; chain of single-surface predicates cannot enforce "research must precede design output anywhere in this turn".               | Q2: No transcript-stream content-shape classifier exists; harness inherited Anthropic's artifact-centric tool-boundary event vocabulary, leaving in-chat design-emission window unobservable.                        |
| MRC   | Q3: Open-loop rule-lifecycle governance — no severity→tier mapping, no signal-driven escalation, no class-registry check, no conversational-phase ownership.                                               | Q4: Governance bootstrapped reactively without applying its own brainstorm→spec→plan pipeline; missing class-recurrence detection signal pipeline and cross-cutting coverage-completeness owner.                     |

---

## Section B: Corrective Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                  | Non-Detection (ND)                                                                                                                                                                            |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: PreToolUse hook `hook-skill-research-precondition.py` on `Skill` tool, denying brainstorming/writing-plans/brainstorm/write-plan dispatch unless ≥2 distinct-stem WebSearches present in transcript. R14 enforce. | Q2: Stop-hook regex denylist extended with design-output phrase set + WebSearch-count predicate; 7-day shadow → enforce. Regression fixture replays 2026-04-26 transcript.                    |
| MRC   | (covered by prevention Q3)                                                                                                                                                                                            | (covered by prevention Q4)                                                                                                                                                                    |

---

## Section B2: Prevention Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                                              | Non-Detection (ND)                                                                                                                                                                                                                                                          |
|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | (corrective covered above; structural prevention is shared with Q3)                                                                                                                                                                               | (corrective covered above; structural prevention is shared with Q4)                                                                                                                                                                                                         |
| MRC   | Q3: Wire `hook-rule-acceptance-gate.py` PreToolUse on behavioral-rule surfaces; enforce severity-tier-map.yaml + generative-class-registry.yaml + concerns.yaml + recurrence-escalator with reader-binding and heartbeat. **hierarchy_level: 3.** | Q4: Class-recurrence detection pipeline: class-registry.yaml + escape-log schema-gate + SessionStart class-recurrence sweep + monthly governance-coverage-sweep ritual + meta-rule R14 (governance-on-governance no-bypass). **hierarchy_level: 2.**                       |

---

## Section C: Proof of Action Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                                                                                                              | Non-Detection (ND)                                                                                                                                                                                                                                                                                                                          |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: metric=R14 deny count + design-without-research recurrence count, target=≥1 R14 deny in regression / 0 recurrences over 30 days / ≥95% Skill calls preceded by ≥2 WebSearches; baseline=0 / 3 / 0%; data=metrics.jsonl + weekly transcript audit; schedule=T+0 + daily + weekly + monthly                      | Q2: metric=Stop-hook deny count + detection latency + false-positive rate, target=≥1 TP on regression fixture, ≤1 FP / 7-day shadow, latency ≤1 turn, FP <5%; baseline=zero coverage / 3 turns undetected / 100% user-reported; data=metrics.jsonl + pytest fixture + 10% transcript sample; schedule=daily shadow + weekly post-enforce    |
| MRC   | Q3: metric=behavioral-rule receipt-pairing rate + auto-escalation tickets per month + ticket-disposition rate + EXEMPT-charter usage; target=100% paired (gate fail-closed), ≥1 daily heartbeat, ≥90% disposed in 7d, 0 EXEMPT/30d or 100% paired with follow-up commit; baseline=text-only / 0 / 0 / 0; schedule=per-commit + daily heartbeat + weekly cron + monthly review | Q4: metric=class-registry entries + class_id-tagged escape-log entries + recurrence-banner injections + mean-time-to-structural-review-receipt + monthly-sweep actionable-gap rate; target=100% tagged / banner within 24h / receipt within 7d ≥90% / 0 rubber-stamp / 0 R14 EXEMPT or paired escape-log; baseline=registry doesn't exist / 0 / 0 / class manifested ≥4× in 7d undetected; schedule=per-commit + per-session + monthly + quarterly + 6-month audit |

---

## Phase 1: IS / IS NOT

| Dimension | IS | IS NOT | Distinction (why this scoping) |
|-----------|----|--------|-------------------------------|
| **What** | Agent producing architectural design output (recommendations, approach sections, risk tables, migration patterns) during in-chat brainstorming WITHOUT first executing ≥2 WebSearches to ground the design in how others actually solve the problem. Failure mode is "inventing instead of researching" surfacing as plausible-but-wrong design (4 errors found post-hoc: artifacts location, migration pattern, network egress, session model). | NOT a failure to write code without tests. NOT a failure to run a skill. NOT a hallucination of facts the agent already knew. NOT a Write/Edit-boundary violation (R1 would have caught that). NOT a missing brainstorming invocation — brainstorming WAS invoked; it just dispatched questions without a research precondition. | Narrows root cause to the gap between "design-thinking output" (chat text) and "persisted-artifact output" (Write tool). All existing gates (R1, R2, R3, R9) fire at the persisted-artifact boundary; the harmful output is already complete by then. Root cause must be an upstream gate (UserPromptSubmit injection, Skill PreToolUse, or in-skill structural requirement), not another Write-boundary check. |
| **Where** | In-chat assistant message stream during brainstorming/design phase, BEFORE any Write/Edit tool call. Specifically: the moment agent emits "My recommendation:", "### Approach N", "Architecture:", risk tables, or section-numbered design proposals. Surface = transcript text, not file artifacts. Skill invoked = `superpowers:brainstorming`. Prompt class = sizable-task / novel-problem (Managed Agents migration). | NOT in spec files under docs/superpowers/specs/ (R1 covers that). NOT in plan files under docs/superpowers/plans/ (R3 covers that). NOT in code files (R4 covers that). NOT in ecosystem-scope artifacts under ~/.claude/ (R11 covers that). NOT in Stop-hook-checked final assistant message only — happens mid-conversation across multiple turns. | Narrows the enforcement surface: the gate must hook on UserPromptSubmit (inject precondition before agent starts thinking) or on Skill-tool PreToolUse (block brainstorming dispatch until WebSearch count ≥2) or on assistant-message-stream pattern detection (Stop-hook regex extended to mid-stream design phrases). Eliminates Write-tool PreToolUse as the right surface — that's the surface that already failed. |
| **When** | Today 2026-04-26, third instance of the same generative class within one session (other two: degraded-emission-with-warning, .next-session-primer 作秀). Trigger condition: user prompt contains sizable-task or novel-problem keywords (migration, architecture, design, approach) AND agent enters brainstorming/design exploration AND zero WebSearch tool calls precede the first design-output message. Time-of-failure = first "present 2-3 approaches" moment in brainstorming Q-sequence. | NOT the first-ever occurrence — has happened before (escape #1 same class). NOT at session start (SessionStart hook fires earlier). NOT at Stop hook (final-message gate, too late). NOT during plan execution phase (executing-plans assumes spec is research-grounded). NOT triggered by trivial single-line tasks (those are exempt from the no-bypass rule). | Narrows to the brainstorming-skill dispatch window — between UserPromptSubmit (where keywords can be detected) and the first design-output assistant message (where damage starts). This "design exploration" window currently has ZERO gates. All existing gates fire either before this window (SessionStart) or after it (Write/Stop). Confirms need for either UserPromptSubmit injection that persists through the window, or in-skill structural requirement that the brainstorming skill itself enforces. |
| **Extent** | Recurring generative class — third instance in one session, all caught by user not gate. Affects: any "inventing-instead-of-researching" failure across brainstorming, design proposals, risk assessments, architecture diagrams, migration plans. Predicate scope: sizable-task OR novel-problem prompts. Damage per instance: full design must be redone after research reveals errors (this case: 4 major errors out of one design = ~100% rework). Cost: user trust erosion + duplicate work + late discovery of fundamental constraints. | NOT limited to Managed Agents migration topic. NOT limited to brainstorming skill (could affect any in-chat design output from any skill). NOT a one-off escape — it is a CLASS, same generative signature as escape #1 (gate-enforcement-boundary-downstream-of-failure-mode). NOT solvable by adding another Write-boundary rule. NOT solvable by text-only CLAUDE.md instructions (already tried, already failed — that IS the failure under review). | Narrows prevention to STRUCTURAL/ARCHITECTURAL tier (rung 3-4 of escalation ladder), not text or soft-gate tier. Confirms the Predicate-Generality charter Q4 trigger: current text-only "always search online first" rule has a too-narrow predicate (only enforced at Write boundary via R1) and the failure mode of that narrowness is precisely what we're seeing. Justifies multi-surface gate (a)+(b)+(c)+(d)+(e) rather than single-point fix — same class has now manifested on 3 different surfaces in one day, so single-surface gate would just push the failure to surface #4. |

---

## Phase 2: Why Chains (4 quadrants) — FULL

### Q1 — Technical Root Cause × Non-Conformance

**Root**: No shared per-turn precondition-state primitive in the hook architecture: each gate is a single-surface predicate, so a "research-first" requirement cannot be injected at UserPromptSubmit, verified at Skill-PreToolUse on brainstorming, and re-checked at Stop on assistant-message regex as a single composed chain — leaving the in-chat design-exploration window ungoverned between the prompt boundary and the file-write boundary.

1. **Why 1**: The agent emitted architectural design output (recommendations, approach sections, risk tables) for the Managed Agents migration without first executing ≥2 WebSearches, because the in-chat brainstorming flow proceeded directly from prompt → "present 2-3 approaches" with zero tool-call preconditions enforced.
   *New insight*: Locates the failure at the design-exploration phase of the chat stream, not at any file write.

2. **Why 2**: The brainstorming skill's Q-sequence template hard-codes "present approaches" as an early step with no embedded requirement for prior WebSearch tool calls — the skill is a pure dialog-shaping prompt, not a tool-orchestration contract.
   *New insight*: Identifies the skill template itself as missing a research-precondition step.

3. **Why 3**: Skills under the superpowers framework are implemented as markdown prompt-injection templates rather than declarative state machines, so a skill cannot natively express "block my own activation until tool X has been called N times in this session".
   *New insight*: Surfaces the structural limitation of the skill abstraction — preconditions are not first-class.
   *Audit notes (R1, R2, R3)*: Collapse 3+4 into one Why "Neither layer (markdown skills nor Python hooks) provides a skill-precondition primitive"; deepen with "the framework offers only two primitives — dialog-shaping markdown templates and tool-boundary Python predicates — but no third primitive (a skill-precondition contract) that either layer could honor".

4. **Why 4**: There is no PreToolUse hook subscribed to the Skill tool that inspects transcript history for prior WebSearch invocations before allowing "brainstorming" (or similar design-exploration skills) to dispatch — the hook layer that COULD compensate for the skill abstraction's gap was never wired for skill-dispatch events.
   *New insight*: Locates the missing compensating hook surface (PreToolUse:Skill).

5. **Why 5**: Every active rule in gate-rules.yaml (R1–R13) is keyed to file-modifying tool boundaries (Write/Edit) or session/turn boundaries (SessionStart/Stop); the schema and matcher engine have no first-class predicate type for "design-output appearing in assistant message stream during a turn".
   *New insight*: Reveals the gate schema is artifact-centric, missing a chat-stream predicate class.
   *Audit notes (R1, R2, R3)*: Merge 5+6: "all gate predicates bind to file-modifying tool boundaries; chat-stream emission is unobservable to the matcher." Deepen: "the matcher is artifact-centric because PreToolUse/PostToolUse are the only Anthropic-supplied hook events that expose tool input/output, so the harness inherited an artifact-centric event vocabulary from the upstream hook contract."

6. **Why 6**: R1's predicate fires only on PreToolUse for Write to docs/superpowers/specs/, so by the time R1 evaluates the missing-WebSearch condition the design has already been generated, presented in chat, and possibly accepted — the gate's enforcement boundary is downstream of where the harmful output is produced.
   *New insight*: Names the boundary mismatch: enforcement-after-emission, the same generative signature as the prior degraded-emission and primer-handoff escapes.
   *Audit notes (R1, R2, R3)*: See Why 5 collapse note.

7. **Why 7**: No UserPromptSubmit hook injects a persistent "research-first" precondition banner when the incoming prompt contains sizable-task / novel-problem keywords (migration, architecture, design, approach), so the agent enters the design-exploration window with no contextual gate active for the duration of that window.
   *New insight*: Identifies the missing upstream injection that would make the in-chat window govern-able.
   *Audit notes (R1, R2, R3)*: Collapse 7+8: "neither the upstream injection surface nor the downstream regex catch is wired for in-chat design-phase phrases." Deepen: "the hook architecture has no concept of a per-turn enforcement window — an opening boundary (UserPromptSubmit) and closing boundary (Stop) that share state — so multi-surface composition cannot be authored even if individual surfaces existed."

8. **Why 8**: Even if a UserPromptSubmit banner were injected, the Stop-hook regex denylist currently contains only output-boundary phrases (degraded-emission warnings, handoff-to-user phrases) and does not match in-chat design-output phrases like "My recommendation:", "### Approach", "Architecture:", "Risk table", so the final-message inspection cannot retroactively detect the violation either.
   *New insight*: Shows the Stop-hook regex denylist has not been extended to design-phase phrases.
   *Audit notes*: See Why 7 collapse.

9. **Why 9** [RELOCATED to q3_mrc_nc per Round 1+2+3 audit]: The CLAUDE.md text rule "Always search online first" has no escalation to a hard gate despite a recorded prior failure (escape #1, same class) — the instruction-failure escalation ladder's threshold-0-for-known-failed rule was not honored at the gate-implementation tier.
   *New insight*: Surfaces non-conformance to the escalation-ladder protocol itself: text-only persistence after a known failure.
   *Audit verdict*: Move to q3_mrc_nc as a top-level finding ("escalation ladder threshold-0-for-known-failed not enforced for R1's predecessor"). Layer-mixing — process-conformance is MRC, not TRC.

10. **Why 10** [RELOCATED to q3_mrc_nc per Round 1+2+3 audit]: The Predicate-Generality charter's Q4 ("what is the failure mode if this rule's predicate is too narrow?") was never answered for R1, so R1's predicate stayed scoped to a single artifact path (specs/) instead of being generalized to cover the upstream class (any design-output emission whether persisted or in-chat).
    *New insight*: Connects the under-scoped predicate to a skipped charter checklist step.
    *Audit verdict*: Relocate to q3_mrc_nc as a sibling finding to the escalation-ladder non-conformance.

11. **Why 11**: The hook architecture has no UserPromptSubmit→Skill-PreToolUse→Stop-regex pipeline that together gate the entire design-exploration window (inject precondition at prompt boundary, verify precondition at skill-dispatch boundary, catch leakage at message boundary); the three surfaces exist independently but are not composed into a single research-first enforcement chain.
    *New insight*: Names the missing composition: no multi-surface chain currently spans the design-exploration window.

12. **Why 12** (terminus): The hook implementation pattern in `~/.claude/hooks/` treats each rule as a single-surface predicate (one tool, one event), with no shared state primitive (e.g., a per-turn "precondition-pending" flag readable by multiple hooks) to coordinate cross-surface enforcement — so even if individual hooks were added, they could not jointly enforce "research must precede design output anywhere in this turn". *Hooks are stateless per-event scripts; the harness exposes no per-turn KV store, so a UserPromptSubmit hook cannot leave a precondition flag for a later Stop hook to read.*
    *New insight*: Identifies the deepest controllable technical gap: no shared per-turn state primitive enabling multi-surface composed enforcement. **Architectural-elimination target.**

### Q2 — Technical Root Cause × Non-Detection

**Root**: No transcript-stream content classifier exists that can recognize "design-output shape" (recommendations, approach sections, risk tables) as a gateable event class — so any detector that hooks on tool boundaries (Write, Skill PreToolUse, Stop) is structurally blind to the in-chat design-emission window where the failure actually manifests.

1. **Why 1**: The non-research design output was not detected because no gate fires on in-chat assistant text; the only enforcement point that checks for ≥2 WebSearches (R1) is bound to the Write tool's PreToolUse event on docs/superpowers/specs/, which only fires when an artifact is persisted — by then the harmful design has already been emitted to the user.

2. **Why 2**: The Write-tool boundary was chosen as the detection surface because the gate-rules.yaml predicate model assumes that all auditable artifacts are file-shaped; it has no event class for "assistant message containing architectural design content," so transcript-stream emissions are invisible to the rule engine.
   *New insight*: Detection model is artifact-centric, not emission-centric — a structural blind spot for any failure that completes inside chat text.

3. **Why 3**: The Stop hook, which DOES read assistant text, was not configured with regex patterns for design-output shape (e.g., "My recommendation:", "### Approach", "Architecture:", risk-table headings) — so even the one transcript-aware gate misses the signature; its denylist is tuned to self-exonerating-warning phrases (R13), not design-without-research phrases.
   *New insight*: Stop-hook regex coverage is incident-reactive: each new generative class needs its own phrase set, and design-without-research has not been added.

4. **Why 4**: The Stop hook also fires only on session/turn termination, so even if its regex were extended, detection would happen after the design has been visible to the user for an entire turn — meaning the Stop surface cannot prevent emission, only flag it post-hoc; no PreAssistantMessage or streaming-content hook exists in the harness API.
   *New insight*: Harness lacks a mid-stream content-inspection event; detection latency floor = one full assistant turn.

5. **Why 5**: The brainstorming skill's prompt does not include a structural precondition like "before emitting any 'present approaches' message, you MUST have ≥2 WebSearch tool_use blocks earlier in this transcript" — its Q1/Q2 dispatch logic checks user-answer state, not tool-call history, so the skill itself cannot detect that it is about to emit ungrounded design.
   *New insight*: Skill self-checks operate on conversational state, not tool-call ledger — the ledger is the only reliable evidence of research.

6. **Why 6**: No PreToolUse hook exists on the Skill tool that would inspect the target skill name (e.g., "brainstorming") and block dispatch until the transcript shows ≥2 WebSearch invocations for sizable-task / novel-problem prompts — so the moment of skill activation, which is the latest point at which research can still precede design, has zero gating.
   *New insight*: Skill-dispatch is an ungated control-flow transition; the harness treats Skill invocation as benign while it is actually the trigger for design emission.

7. **Why 7**: No UserPromptSubmit hook injects a "research-first banner" contingent on sizable-task or novel-problem keyword detection in the prompt; the existing UserPromptSubmit injection logic handles MANDATORY SKILL ACTIVATION (R9) and EXEMPT parsing but does not classify prompts by research-need, so the earliest detectable upstream signal (keyword match in the prompt) is left unused.
   *New insight*: Prompt-classification at submission time is a free signal that no current gate consumes.

8. **Why 8**: No content-shape classifier exists that can answer "is this assistant message a design-output?" — implementing detection at any layer (Stop regex, mid-stream hook, skill self-check) requires a shared predicate, and the gate-rules schema has no "content-shape" predicate type, only file-path / tool-name / keyword predicates; the schema itself bounds what can be detected.

9. **Why 9**: The gate-rules schema is content-shape-blind because it was designed around tool-call metadata (cheap, deterministic, available in hook payloads) rather than message-body inspection (requires regex + LLM-judge + token cost); this trade-off was made implicitly when the original 9-hook architecture was built and never revisited as failure modes migrated upstream into chat text.

10. **Why 10**: The trade-off was never revisited because there is no telemetry that counts "failures whose enforcement surface would have to be content-shape, not tool-call" — metrics.jsonl logs gate firings and EXEMPTs, but does not log NEAR-MISSES where a failure occurred and no rule could have caught it; without that signal the schema's blind spot is invisible to the quarterly compression ritual.
    *New insight*: The "rules that could not exist under current schema" class is unmeasured — the meta-detection layer has its own blind spot.

11. **Why 11**: Near-miss logging does not exist because the rule-acceptance charter's Q4 ("what is the failure mode if this rule's predicate is too narrow?") is answered as text in a receipt file, not as a structured field that feeds back into a "predicate-narrowness watchlist" — so even when authors correctly identify narrowness risks, those notes never become detectors; the governance loop is open-loop, not closed-loop.
    *New insight*: Rule-acceptance receipts are write-only documents; they don't generate detectors for their own predicted failure modes.

12. **Why 12** (terminus): The governance loop is open because no component owns the responsibility of converting receipt-Q4 answers into shadow-mode audit rules; ecosystem-conformance-owner per owners.yaml owns acceptance-time review but not lifetime predicate-narrowness monitoring — the role boundary stops at landing the rule, not at watching the rule's blind spots over time. **This is the deepest controllable cause: an unowned closed-loop responsibility for predicate-narrowness telemetry.**

### Q3 — Management Root Cause × Non-Conformance

**Root**: Open-loop rule-lifecycle governance: the management system authors behavioral rules without a mandatory severity-to-enforcement-tier mapping, without signal-driven (recurrence-rate) auto-escalation, without a generative-class registry that rule-acceptance must check against, and without ownership defined over conversational phases (only over tool/artifact surfaces). These four governance gaps jointly allow narrow-predicate text-only rules (like "always search online first") to persist in steady state, guaranteeing the same generative class keeps escaping on new surfaces. Closing the loop at the rule-lifecycle layer is the deepest controllable managerial cause.

1. **Why 1**: The agent presented a full architectural design (12-section Managed Agents migration with risks table) without performing any web research first, violating the "Always search online first" rule in CLAUDE.md.
   *New insight*: Surface-level non-conformance: behavior diverged from a written rule the agent had access to.

2. **Why 2**: The "Always search online first" rule was authored as a text-only instruction in CLAUDE.md with no enforcement gate attached, so its compliance depended entirely on the agent re-reading and self-policing it each session.
   *New insight*: Governance chose the weakest rung of the escalation ladder (text instruction) for a rule whose failure cost is high.

3. **Why 3**: The management system's authoring workflow for new behavioral rules has no required step that classifies the rule's failure cost and assigns a corresponding enforcement tier (text / soft gate / hard gate / architectural elimination) before the rule is committed.
   *New insight*: There is no "rule severity → enforcement tier" policy mapping; tier selection is left to author intuition.

4. **Why 4**: The only structural gate that does exist for this rule class (R1) was scoped to the Write-tool boundary on docs/superpowers/specs/, because the rule-acceptance process treated the "persisted artifact" as the canonical failure surface and never asked whether the failure could occur upstream of persistence.
   *New insight*: Predicate scoping decision was anchored to artifact-boundary thinking, blind to in-chat output as a failure surface.

5. **Why 5**: The Predicate-Generality charter's Q4 ("what is the failure mode if this rule's predicate is too narrow?") is currently a text-only checklist requirement in the rule-acceptance receipt, with no PreToolUse gate (`hook-rule-acceptance-gate.py` is documented as "not yet wired"), so authors can ship narrow predicates without the question being meaningfully answered.
   *New insight*: The meta-governance layer that should prevent narrow predicates suffers from the SAME failure pattern (text-only, ungated) that the rules it governs suffer from — recursive non-conformance.

6. **Why 6**: The Skill-authoring governance for `superpowers:brainstorming` does not require skills to declare structural preconditions (e.g., "before emitting any design proposal, N WebSearch results must exist in the transcript"); skill review only checks that the skill runs, not that its outputs are research-grounded.
   *New insight*: Skill quality governance has no "evidence-grounded output" acceptance criterion — skills can ship with research-blind dispatch logic.

7. **Why 7**: There is no governance owner accountable for the "design-exploration window" (the gap between UserPromptSubmit and first persisted artifact); ownership in `owners.yaml` is organized around tools and artifact surfaces, not around conversational phases, so the in-chat design phase has no responsible party watching it.
   *New insight*: Ownership taxonomy is artifact-centric, leaving conversational-phase failure modes orphaned.

8. **Why 8**: The escalation-log review cadence (monthly cross-reference of feedback_*.md against CLAUDE.md) detects ungated known-failed instructions retrospectively, but the policy has no inter-instance trigger that fires when the SAME generative class manifests multiple times within a single session — so three same-class escapes in one day did not auto-escalate.
   *New insight*: Escalation policy is calendar-driven (monthly), not signal-driven (recurrence-rate), so high-frequency same-class clusters slip through until the monthly review.

9. **Why 9**: The management system has no defined "generative class" taxonomy in governance — escape #1 (degraded-emission-with-warning), the .next-session-primer 作秀, and today's research-skip are recognized post-hoc as the same class ("gate-enforcement-boundary-downstream-of-failure-mode") but the rule-acceptance process does not require authors to check whether a proposed gate addresses the class or only an instance.
   *New insight*: Without a class registry, every new rule fights the last instance instead of the underlying generative pattern, guaranteeing surface-#4, surface-#5 recurrences.

10. **Why 10** (terminus): The root governance failure is that the management system treats rule authoring as a one-way producer activity (write rule → ship) rather than a closed-loop control system (write rule → measure conformance → auto-escalate tier on failure → retire on obsolescence); without the closed loop, narrow predicates, ungated meta-rules, calendar-only escalation, and missing class taxonomy all coexist as stable steady-state defects.
    *New insight*: The deepest controllable cause: the rule-lifecycle process is open-loop. Closing the loop (mandatory tier-classification at authoring, signal-driven escalation, class-registry check, ownership over conversational phases) is the structural fix that subsumes the individual gaps above.

### Q4 — Management Root Cause × Non-Detection

**Root**: Governance was bootstrapped reactively (rule-by-rule from individual escapes) without ever applying its own brainstorm→spec→plan pipeline to the management system itself; consequently there is no governance-design document defining concerns, no failure-mode taxonomy, no generative-class registry, no cross-cutting "coverage-completeness" owner, and therefore no signal pipeline that could have detected the class-level recurrence (three instances of "gate-boundary-downstream-of-failure-mode" in one session) before it caused user-visible damage.

1. **Why 1**: The management system did not detect the research-first gap before three instances accumulated in one session because the only escalation thresholds defined in governance are per-instance (0 for known-failed, 1 for new) — there is no class-level recurrence threshold (e.g., "third occurrence of the same generative class within N hours triggers structural review").
   *New insight*: Threshold model operates at instance granularity, blind to class-level burst patterns.

2. **Why 2**: No class-level threshold exists because escape_log.yaml entries are not tagged with a generative-class identifier; cross-instance pattern recognition therefore requires manual human reading of every entry rather than an automatable query, so the signal cannot be wired to any action.
   *New insight*: Logging schema lacks the dimension on which detection would have to pivot.

3. **Why 3**: Generative-class tagging is absent because the rule-acceptance charter's 4-question checklist (CLASS coverage, compression candidates, surface, narrow-predicate failure mode) asks the author to think about class membership but does not require registering a class ID — class identity remains implicit prose in the receipt.
   *New insight*: Charter probes class-thinking but does not force class-naming, so the data never becomes machine-queryable.

4. **Why 4**: Class identity stays implicit because the governance asset inventory contains a rule registry (gate-rules.yaml) and an owners registry (owners.yaml) but no failure-mode/generative-class registry — the taxonomy that would name "gate-boundary-downstream-of-failure-mode" as a class has no home file.
   *New insight*: Missing first-class governance artifact: the class taxonomy itself.

5. **Why 5**: No class registry was created because governance was designed bottom-up — each rule added in response to an individual escape — without a top-down enumeration of failure-mode categories that would have surfaced "enforcement-boundary mismatch" as a category needing its own register.
   *New insight*: Bottom-up assembly never produced the top-down map.

6. **Why 6**: Bottom-up assembly was the only mode used because owners.yaml assigns ownership per artifact (rules, hooks, wiki, skills) but assigns nobody to the cross-cutting concern of "coverage completeness across all failure surfaces" — so no role is accountable for asking "which failure windows currently have zero gates?".
   *New insight*: Ownership map is artifact-shaped, not concern-shaped; cross-cutting concerns fall through.

7. **Why 7**: Ownership is artifact-shaped because owners.yaml was seeded from the existing file inventory ("we have these files, who owns each?") rather than from a list of governance concerns ("what must be guaranteed, who guarantees it?") — Conway's-law-style mirroring of file structure into role structure even in single-user governance.
   *New insight*: Owner-assignment process inverted: artifacts drove roles instead of concerns driving roles.

8. **Why 8**: Concerns never drove roles because there is no governance design document that enumerates "what management-system properties must hold" (completeness, recurrence-detection, predicate-generality, escalation latency); without such a document, role authoring has no checklist of concerns to cover.
   *New insight*: Governance has no requirements specification of its own.

9. **Why 9**: No governance design document exists because the management framework itself was never put through the mandatory brainstorm→spec→plan→execute pipeline that the framework imposes on user work — governance work was treated as exempt "meta" work rather than as a sizable task subject to the same discipline.
   *New insight*: The pipeline that catches inventing-instead-of-designing in user code was never applied to governance code; governance committed the very anti-pattern its rules forbid.

10. **Why 10**: Governance was treated as exempt because no meta-rule says "changes to gate-rules.yaml, owners.yaml, hooks/, or escalation policy must themselves follow brainstorm→spec→plan" — the no-bypass rule scopes to "user tasks" implicitly, leaving meta-changes ungated.
    *New insight*: No-bypass rule has an implicit user-work scope; meta-work is silently outside it.

11. **Why 11**: Meta-changes are ungated because no role owns "ensure governance changes follow governance" — a recursive ownership gap: the entity that would assign such an owner is the same entity that needs the owner, and absent a bootstrap step (owners-of-owners), the recursion never closed.
    *New insight*: Recursive ownership bootstrap was never performed; governance-on-governance is unowned by construction.

12. **Why 12**: The recursive bootstrap was never performed because governance evolution is event-driven (incidents → 8D → new rule) rather than scheduled-review-driven; no calendar-pinned "governance-of-governance" audit exists where the bootstrap question ("who ensures the management system follows its own discipline?") would be forced onto the agenda.
    *New insight*: Governance has no scheduled self-audit cadence; only reactive triggers, which by definition cannot detect the absence of a trigger.

13. **Why 13** (terminus): No scheduled self-audit cadence exists because the only governance ritual currently on a cadence is the quarterly compression ritual (rule-merge focus); there is no companion ritual for coverage-gap discovery, predicate-generality review of existing rules, or class-recurrence sweep — the ritual portfolio is one-dimensional (consolidation only, not completeness or recurrence).
    *New insight*: Single-ritual governance covers consolidation but not coverage or recurrence; the missing rituals are precisely the ones that would have caught this.

---

## Phase 3: RC Audit Rounds — FULL

### Round 1 — Verdict: CONTINUE

**Weakness 1.1** [q1_trc_nc Why 9, ADDRESSABLE]: "Why 9 (CLAUDE.md text rule had no escalation to a hard gate despite a recorded prior failure — escalation-ladder protocol not honored) is a management-system / governance-process cause, not a technical root cause. It belongs in q3_mrc_nc (Management-System Root Cause, Non-Conformance), not in the TRC chain. Mixing layers obscures whether the technical chain actually bottoms out at a technical primitive or has been padded with process-layer findings."
*Suggested fix*: Move Why 9 to q3_mrc_nc as a top-level finding ("escalation ladder threshold-0-for-known-failed not enforced for R1's predecessor"). In q1, delete it and renumber; the technical chain should continue from Why 8 (denylist scope) directly into Why 11 (missing composition) / Why 12 (no shared per-turn state).

**Weakness 1.2** [q1_trc_nc Why 10, ADDRESSABLE]: "Why 10 (Predicate-Generality charter Q4 was never answered for R1) is a process-conformance failure (a checklist step skipped) — that is a management-system root cause, not a technical one. Same layer-mixing issue as Why 9."
*Suggested fix*: Relocate to q3_mrc_nc as a sibling finding to the escalation-ladder non-conformance.

**Weakness 1.3** [q1_trc_nc Why 8, ADDRESSABLE]: "Why 7 (missing UserPromptSubmit injection) and Why 8 (Stop-hook regex denylist not extended) are parallel/lateral causes rather than a deeper causal step — Why 8 explicitly frames itself as 'even if Why 7 were done…', which is the signature of a sibling, not a child. This violates Check 1 (each Why should be a genuinely new causal insight, not a rephrase or co-equal alternative)."
*Suggested fix*: Restructure: collapse Whys 7+8 into a single Why 7 ("no upstream injection AND no downstream regex catch — both surfaces unwired") whose deeper cause is Why 11 (no composed multi-surface chain) and ultimate cause Why 12 (no shared per-turn state primitive).

**Weakness 1.4** [q1_trc_nc Why 6, RESIDUAL]: "Why 6 generalizes the boundary-mismatch to 'same generative signature as prior degraded-emission and primer-handoff escapes' but does not cite the receipt path or wiki entry — a reader cannot verify the class match without external lookup. Residual because the underlying causal claim is sound; only its citation hygiene is weak."
*Suggested fix*: Add an inline reference to the wiki concept page (degraded-emission-with-warning.md) and the relevant 8D source (8d-ecosystem-degraded-emission-2026-04-25.md).

**Weakness 1.5** [q2_trc_nd, ADDRESSABLE]: "The q2_trc_nd quadrant content is truncated in the audit input. Per Check 3, ND quadrants must be drilled to comparable depth as NC quadrants — q1 reaches Why 12 with a clear technical primitive; without the q2 chain visible I cannot confirm parity, but the visible root statement is single-cause and may not have been drilled to a primitive."
*Suggested fix*: Provide the full q2 chain. Confirm it descends to a technical primitive comparable to q1's "no shared per-turn state primitive" — e.g., "no streaming-content inspection hook event in the harness" or "no LLM-judge sidecar wired to assistant-message stream".

**Weakness 1.6** [q3_mrc_nc, ADDRESSABLE]: "q3_mrc_nc chain is not present in the audit input at all. Per Check 2, MRC quadrants must operate at the management-system level (process ownership, escalation policy, charter enforcement, review cadence) — and per Check 3, they must reach comparable depth to TRC chains."
*Suggested fix*: Supply the q3 chain. Seed it with the relocated Whys 9 and 10 from q1 and drill: escalation-ladder non-conformance → why no monthly review caught it → why review owner has no enforcement surface → ultimate primitive.

**Weakness 1.7** [q4_mrc_nd, ADDRESSABLE]: "q4_mrc_nd chain is not present in the audit input. This is the management-system + detection axis — i.e., 'why did the management system fail to DETECT that R1 was under-scoped / that the prior failure recurred?'"
*Suggested fix*: Supply q4. Likely root layer: no recurrence-detection job cross-references feedback_*.md headers against gate-rules.yaml predicates; no metrics.jsonl alerting on "rule R{n} fired in audit mode but never escalated"; no quarterly compression ritual run on schedule.

**Weakness 1.8** [q1_trc_nc Why 12, RESIDUAL]: "Stated root ('no shared per-turn precondition-state primitive') is plausible and technical, but the chain does not test the alternative framing: the gap could equally be characterized as 'no harness-level streaming-message inspection event,' which would make q2's missing classifier the same root, not a parallel one."
*Suggested fix*: Add a one-line reconciliation statement at the end of the q1 root and the q2 root naming whether the two chains share a primitive or are genuinely independent gaps.

*soa_citations_used*: none — Round 1 was structural review against 8D Check 1/2/3.

### Round 2 — Verdict: CONTINUE

**Weakness 2.1** [q1_trc_nc Why 3, ADDRESSABLE]: "Whys 3 and 4 are siblings (parallel structural facts), not a depth step. Why 3 says 'skill abstraction cannot express preconditions'; Why 4 says 'no compensating PreToolUse:Skill hook'. Both name absent surfaces at the same causal layer — neither asks 'why is the surface absent?' The chain treats two missing capabilities as serial when they share a single deeper cause."
*Suggested fix*: Collapse into "no precondition primitive at either skill or hook layer" with deeper cause being the framework's two-primitive (markdown skills + Python hooks) asymmetry.

**Weakness 2.2** [q1_trc_nc Why 6, ADDRESSABLE]: "Why 5 ('schema has no chat-stream predicate type') and Why 6 ('R1 fires on PreToolUse for Write — downstream of emission') are restatements of the same finding from two angles."
*Suggested fix*: Merge 5+6 and deepen with "the matcher is artifact-centric because PreToolUse/PostToolUse are the only Anthropic-supplied hook events that carry tool input/output, so the harness inherited an artifact-centric event vocabulary."

**Weakness 2.3** [q1_trc_nc Why 7, ADDRESSABLE]: "Confirms embedded audit_note: Whys 7 and 8 are a breadth-list of two unwired surfaces."
*Suggested fix*: Collapse 7+8; next Why frames per-turn enforcement window (UserPromptSubmit→Stop) sharing state as the structural depth.

**Weakness 2.4** [q1_trc_nc Why 1, RESIDUAL]: "Why 1 and Why 2 are close to a rephrase."
*Suggested fix*: Acceptable if Why 2 is explicitly framed as locating the gap inside the skill template body.

**Weakness 2.5** [q1_trc_nc Why 12, ADDRESSABLE]: "Why 12 is truncated in the input ('with no share...'). Cannot verify whether it actually reaches a terminal primitive."
*Suggested fix*: Restore Why 12 in full and confirm terminus at a structural primitive.

**Weakness 2.6** [q1_trc_nc Why 9, ADDRESSABLE]: "Confirms embedded audit_note: Why 9 (CLAUDE.md text rule not escalated to hard gate despite escape #1) is a management-system finding, not a technical-root-cause finding. Same for Why 10."
*Suggested fix*: Move Why 9 and Why 10 to q3_mrc_nc as the two top-level MRC-NC findings.

**Weakness 2.7** [q3_mrc_nc, ADDRESSABLE]: "q3_mrc_nc, q2_trc_nd, and q4_mrc_nd chains are not visible in the audit input — only q1_trc_nc is shown."
*Suggested fix*: Provide the remaining three quadrant chains for Round 3.

**Weakness 2.8** [q2_trc_nd, ADDRESSABLE]: "Cannot verify Check #3 (ND quadrants as deep as NC quadrants)."
*Suggested fix*: Surface q2_trc_nd in Round 3.

**Weakness 2.9** [q4_mrc_nd, ADDRESSABLE]: "Cannot verify Check #2 for q4 (management-system level, not code-level)."
*Suggested fix*: When q4 is provided, audit that each Why names a management artifact rather than a code artifact.

*soa_citations_used*: none — Round 2 was structural review.

### Round 3 — Verdict: CONTINUE

**Weakness 3.1** [q1_trc_nc Why 3, ADDRESSABLE]: "Whys 3 and 4 are a breadth-list of two missing surfaces (skill abstraction lacks preconditions; PreToolUse:Skill hook not wired) rather than a depth-walk. They name two symptoms of the same structural gap instead of advancing the causal chain."
*Suggested fix*: Collapse 3+4 into one Why; deepen with framework's two-primitive asymmetry.

**Weakness 3.2** [q1_trc_nc Why 5, ADDRESSABLE]: "Whys 5 and 6 restate the same insight (gate schema is artifact-centric / R1 fires post-emission) at two granularities without progressing the causal chain."
*Suggested fix*: Merge into "all gate predicates bind to file-modifying tool boundaries; chat-stream emission is unobservable to the matcher" and use freed slot for upstream Anthropic event vocabulary inheritance.

**Weakness 3.3** [q1_trc_nc Why 7, ADDRESSABLE]: "Whys 7 and 8 enumerate two more missing surfaces (UserPromptSubmit injection; Stop-hook regex denylist) — again breadth, not depth."
*Suggested fix*: Collapse 7+8 and advance with per-turn enforcement window primitive.

**Weakness 3.4** [q1_trc_nc Why 9, ADDRESSABLE]: "Why 9 (escalation-ladder threshold-0-for-known-failed not honored) is a management-system non-conformance, not a technical root cause. It belongs in q3_mrc_nc."
*Suggested fix*: Move Why 9 to q3_mrc_nc.

**Weakness 3.5** [q1_trc_nc terminus, ADDRESSABLE]: "The chain never reaches a terminal structural cause. After the suggested collapses it should land at: 'the harness inherited Anthropic's tool-boundary event vocabulary and never extended it with chat-stream / per-turn-window / skill-precondition primitives'."
*Suggested fix*: Add a terminal Why explicitly identifying the upstream event-vocabulary inheritance.

**Weakness 3.6** [q2_trc_nd, RESIDUAL]: "q2_trc_nd chain was not provided in this round's input. Cannot audit ND-depth parity against NC quadrants."
*Suggested fix*: Surface in next pass.

**Weakness 3.7** [q3_mrc_nc, ADDRESSABLE]: "q3 chain not visible in input, but q1's misplaced Why 9 implies q3 is missing the escalation-ladder-non-conformance finding."
*Suggested fix*: Add to q3 the prior-failure-no-escalation finding and trace deeper.

**Weakness 3.8** [q4_mrc_nd, RESIDUAL]: "q4 chain not provided. Cannot verify it stays at management-system level or matches q3 depth."

**Weakness 3.9** [q1_trc_nc generative-class signature, RESIDUAL]: "Generative-class signature claim ('same generative signature as prior degraded-emission and primer-handoff escapes' in Why 6) is asserted but not formally cross-referenced to a generative-class registry."
*Suggested fix*: Cite specific escape IDs and link to a registry/wiki concept page.

*soa_citations_used*: none — chain converged structurally.

**Final verdict (Round 3): CONTINUE**, with chain converging on dual roots:
- q1/q2 → upstream Anthropic event-vocabulary inheritance + missing per-turn shared state primitive (architectural-elimination target).
- q3/q4 → open-loop rule-lifecycle governance + missing class-recurrence detection signal pipeline.

---

## Phase 4: Full Actions (Corrective + Prevention) per Quadrant

### Q1 — Corrective (TRC × NC)

**Action**: Add PreToolUse hook `~/.claude/hooks/hook-skill-research-precondition.py` that intercepts `Skill` tool calls whose `skill` argument matches the design-exploration class (`superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:write-plan`, `superpowers:brainstorm`). The hook scans the current session transcript (`$CLAUDE_TRANSCRIPT_PATH`) for ≥2 prior `WebSearch` tool_use blocks with distinct query stems within the same turn-window. If the count is <2, deny with `permissionDecisionReason="Research-first precondition unmet: brainstorming/planning skills require ≥2 prior WebSearches in this session"` and `requiredActions=["Run ≥2 WebSearch calls with distinct query stems on the problem domain", "Then re-invoke the skill"]`. Wire into `~/.claude/settings.json` under `hooks.PreToolUse` with `matcher: "Skill"`. Add corresponding rule R14 (category `process-skip`, mode `enforce`) to `~/.claude/gate-rules.yaml` and create the rule-acceptance receipt at `~/.claude/governance/rule-acceptance-receipts/R14.md` answering all 4 charter questions. Re-run today's Managed Agents migration prompt as a regression test: confirm the hook denies the brainstorming dispatch until WebSearches are performed.

**Rationale**: Targets the exact missing surface for THIS instance: when the agent invoked the brainstorming skill on the Managed Agents migration prompt, no hook intercepted at the skill-dispatch boundary, so the design-exploration window opened ungoverned and produced 12 sections of recommendations without any WebSearch. A PreToolUse:Skill hook is the narrowest enforcement boundary that sits BEFORE the first "present approaches" message yet AFTER enough prompt context exists to evaluate the precondition — closing the upstream-vs-downstream gap that R1 (Write-boundary) cannot reach. This fixes the specific failure (Managed Agents brainstorm with zero research) without claiming to solve the whole class of in-chat emission gaps (those need the composed UserPromptSubmit→Skill→Stop chain captured separately as the architectural prevention item). Re-running the original prompt as regression test proves the gate would have caught today's instance.

**Owner**: ecosystem-conformance-owner (per ~/.claude/governance/owners.yaml)
**Target date**: 2026-04-28
**Evidence of completion**:
1. File `~/.claude/hooks/hook-skill-research-precondition.py` exists and is executable.
2. `~/.claude/settings.json` contains a `PreToolUse` entry with `matcher: "Skill"` pointing at the new hook.
3. `~/.claude/gate-rules.yaml` version bumped to 3 with R14 entry, and `~/.claude/CLAUDE-rules-summary.md` regenerated showing R14 in the active table.
4. `~/.claude/governance/rule-acceptance-receipts/R14.md` exists with all 4 charter questions answered.
5. Regression test: re-issuing today's Managed Agents migration prompt and invoking `superpowers:brainstorming` produces a denial whose `permissionDecisionReason` contains "Research-first precondition unmet"; after running 2 distinct-stem WebSearches the same Skill invocation succeeds.
6. `~/.claude/metrics.jsonl` shows at least one R14 deny event from the regression test.

### Q2 — Corrective (TRC × ND)

**Action**: Extend the Stop-hook regex denylist in ~/.claude/hooks/stop-hook-*.py (and/or gate-rules.yaml R-new) to match the exact design-output shapes emitted in the 2026-04-26 Managed Agents incident: case-insensitive patterns for `^#{1,4}\s*(Approach|Architecture|Design|Recommendation|Migration Plan|Risks?|Trade-?offs?)\b`, `\bMy recommendation\b`, `\bProposed (architecture|design|approach)\b`, and markdown risk-table headers (`\|\s*Risk\s*\|`). Pair the regex with a transcript scan that counts WebSearch tool_use blocks in the current session; if matches ≥1 AND WebSearch count <2, emit a Stop-hook deny with reason "design-output emitted without prior research (R1-class, transcript surface)". Ship in shadow/audit mode for 1 week, then promote to enforce. Add one regression fixture under ~/.claude/hooks/tests/ replaying today's transcript and asserting the hook fires.

**Rationale**: This fixes THIS instance (q2_trc_nd: no transcript-stream classifier saw the design emission) by giving the one already-transcript-aware gate — the Stop hook — the specific phrase set that this incident produced. It does not pretend to solve the class (that's q3/q4 territory). What it does do: guarantee that the next time an assistant turn emits "Architecture:" / "My recommendation:" / a risks table without ≥2 prior WebSearches in the same session, the Stop hook denies the turn and writes a metrics.jsonl entry — converting an unobserved near-miss into an observed gate firing, which is the minimum precondition for the q4 closed-loop telemetry that the why-chain terminates on. Detection latency is one full assistant turn (acknowledged ceiling at why#4), but post-hoc flagging is strictly better than the current zero-coverage state and creates the data the predicate-narrowness watchlist needs.

**Owner**: ecosystem-conformance-owner
**Target date**: 2026-05-03 (shadow-mode land 2026-04-29, promote to enforce 2026-05-03 after audit-log review)
**Evidence of completion**:
1. Diff to ~/.claude/hooks/stop-hook-*.py (or gate-rules.yaml adding R14 with category=output-boundary, mode=audit→enforce) committed and auto-pushed.
2. Regression test file ~/.claude/hooks/tests/test_design_without_research.py replays today's 2026-04-26 transcript and asserts hook returns deny with the expected reason string; `pytest` exits 0.
3. ~/.claude/CLAUDE-rules-summary.md auto-regenerated showing the new rule row.
4. After 7 days of shadow mode, metrics.jsonl shows ≥0 false positives on benign turns AND the rule's audit-mode log captured at least the planted regression case; mode field flipped audit→enforce in a follow-up commit.
5. A pointer line added to the q4 prevention backlog noting "near-miss telemetry from R14 firings feeds predicate-narrowness watchlist".

### Q3 — Prevention (MRC × NC)

**Action**: Wire `~/.claude/hooks/hook-rule-acceptance-gate.py` as a PreToolUse hook on Edit/Write to `~/.claude/CLAUDE.md`, `~/.claude/gate-rules.yaml`, `~/.claude/feedback_*.md`, and any `*.md` under `~/.claude/skills/*/SKILL.md` that introduces or modifies a behavioral rule. The gate BLOCKS the edit unless a receipt at `~/.claude/governance/rule-acceptance-receipts/<ruleid>.md` exists and contains ALL of:
1. The 4 generality answers,
2. An explicit `severity_tier:` field with one of {text, soft_gate, hard_gate, architectural_elimination} mapped from a required `failure_cost:` field (constrained to enum {trivial, recoverable, silent-corruption, cross-session-recurrence, ecosystem-class}, with required `failure_cost_evidence:` pointing to metrics.jsonl event ID / 8D run ID / feedback_*.md / wiki concept page) via a published mapping in `~/.claude/governance/severity-tier-map.yaml`,
3. A `class_registry_check:` field naming which entry in `~/.claude/governance/generative-class-registry.yaml` the rule addresses (or declares "new-class" + appends a registry entry with non-empty `signature_pattern` regex in the same commit),
4. A `conversational_phase_ownership:` field naming the owner from `owners.yaml` accountable for the phase the rule guards.

Bootstrap requires creating: the hook script, severity-tier-map.yaml (including a `recurrence_threshold` column tier-indexed: architectural_elimination=1, hard_gate=2, soft_gate=3, text=5), generative-class-registry.yaml (seeded with degraded-emission-with-warning, gate-enforcement-boundary-downstream-of-failure-mode, deferred-artifact-without-reader, governance-bypass-via-exemption), owners.yaml extension with conversational-phase owners, plus a Make/PowerShell `bootstrap-rule-acceptance.ps1`. Hook fail-CLOSED on missing/malformed config with deterministic actionable error pointing to bootstrap script.

Additionally: signal-driven auto-escalator `hook-recurrence-escalator.py` on Stop reads `metrics.jsonl`, counts same-class violations within rolling 24h, and when count ≥ tier-indexed threshold writes a `governance/auto-escalation-tickets/<ruleid>.md` requiring tier-upgrade. **Reader-binding**: ticket creation triggers PushNotification to phase-owner; next session's UserPromptSubmit injects unread-ticket count + oldest age as banner blocking new gate-rules.yaml/CLAUDE.md edits until dispositioned; tickets >7 days auto-promote class tier by one rung (fail-forward). **Heartbeat**: SessionStart self-test invokes ~/.claude/hooks/test-rule-acceptance-gate.py daily verifying gate fires on synthetic bad receipt and passes on synthetic good receipt; absence ≥24h auto-promotes to P1 ticket. **Receipt-linter sub-predicate**: rejects "TBD"/"N/A"/"pending" literal values; rejects "new-class" without same-commit registry append; rejects 4-question answers <40 chars or matching boilerplate denylist. **Per-rule receipt pairing**: hook parses diff, extracts every new/modified rule ID, requires one receipt file per rule ID present (filename = rule ID).

EXEMPT-charter handling: either non-exemptable (preferred), or EXEMPT must be paired with follow-up receipt commit within 24h enforced by Stop-hook (parallel shape to auto-escalator); every EXEMPT logged to `governance/charter-exempt-debt.jsonl` scanned by recurrence-escalator. Path predicate extended to `~/.claude/hooks/*.py|*.sh` and `~/.claude/plugins/**/SKILL.md`; post-Write content-shape validator greps any new file under ~/.claude/ for behavioral-rule signatures (modal-verb regex) and demands a receipt if matches > 0. Emitter-coverage manifest at `~/.claude/governance/metric-emitter-manifest.yaml`; weekly Stop-hook check raises `governance/coverage-alerts/<surface>.md` for surfaces with zero events in 7 days. Quarterly registry-compression ritual extended to generative-class-registry.yaml (rejects predicates matching >50% of registry as too-coarse, flags <2-historical-match as too-narrow).

**Quadrant**: q3_mrc_nc
**Hierarchy level**: **3** (hard gate — relabeled from 2 per Round 3 audit; PreToolUse hook that BLOCKS Edit/Write is by definition hard gate per instruction-failure-escalation-ladder concept)

**Gate test**:
- *Scope* — **PASS**. The gate operates on the rule-LIFECYCLE itself, not on any one rule instance. Every future behavioral rule (research-first, degraded-emission, deferred-artifact, and unknown future classes) must pass the same severity→tier classification + class-registry check + phase-owner assignment before landing. This subsumes today's research-skip class because any "always X first" style rule will be forced into a non-text tier when its failure_cost is non-trivial.
- *Persistence* — **PASS**. Enforcement is structural: PreToolUse hook blocks the Edit/Write tool call at the harness layer — the agent cannot bypass by "remembering" or not. Supporting artifacts versioned in auto-commit + auto-push ~/.claude git repo. Recurrence-escalator runs on every Stop event regardless of session/cwd. Dogfooding: hook self-tests its own receipt is hard_gate.
- *Measurability* — **PASS**. Auditor in 6 months can verify: (a) `claude-hooks show | grep hook-rule-acceptance-gate` returns active+enforce; (b) `git log -- ~/.claude/governance/rule-acceptance-receipts/` shows a receipt commit paired with every gate-rules.yaml/CLAUDE.md behavioral-rule commit; (c) every receipt contains four required YAML fields (grep-checkable); (d) auto-escalation-tickets directory contains tickets for any class that recurred ≥ tier-threshold in metrics.jsonl rolling windows; (e) class-registry shows monotonic growth.

**Failure mode of prevention**: (1) Authors satisfy receipt fields with low-quality fill-in. *Mitigated*: receipt-linter rejects boilerplate; failure_cost is enum + evidence-bound; "speculative" bucket maps to strongest tier by default. (2) Recurrence-escalator depends on metrics.jsonl emitter coverage; new failure surfaces with no metric are invisible. *Mitigated*: emitter-coverage manifest + weekly silence-as-alert sweep. (3) Multi-rule commit could ship one good receipt + one orphan rule. *Mitigated*: per-rule receipt pairing on diff parse. (4) Bootstrap fail-mode unspecified. *Mitigated*: explicit fail-CLOSED with bootstrap script pointer + daily heartbeat self-test.

**Deployment scope**: **GLOBAL**. The rule-lifecycle governance lives in ~/.claude/ and applies to ALL behavioral rules across ALL projects (per CLAUDE.md R11). The generative class has manifested across at least four unrelated surfaces. Project-scoping this prevention would re-create the exact predicate-narrowness pathology the prevention is designed to eliminate.

### Q4 — Prevention (MRC × ND)

**Action**: Introduce a class-recurrence detection pipeline as a first-class governance artifact. Concretely:

1. Create `~/.claude/governance/class-registry.yaml` — a versioned enumeration of generative failure classes (e.g., `gate-boundary-downstream-of-failure-mode`, `degraded-emission-with-warning`, `inventing-instead-of-researching`). Each entry has: class_id, definition, canonical example, owning rule(s), detection-surface, discriminator_predicate (runnable matcher), signature_pattern.

2. Extend `~/.claude/governance/escape_log.yaml` schema to REQUIRE a `class_id` field drawn from class-registry.yaml. Add a pre-commit hook `hook-escape-log-schema-gate.py` that rejects commits to escape_log.yaml whose new entries either (a) lack a class_id or (b) reference a class_id not present in class-registry.yaml. Unknown classes must be added to the registry first (which itself is gated by the rule-acceptance charter receipt requirement, extended to cover registry edits).

3. Add a SessionStart hook `hook-class-recurrence-sweep.py` that scans the last 24h of escape_log.yaml + metrics.jsonl, groups by class_id, and if any class shows ≥3 instances within the window (or ≥ tier-indexed threshold), injects a blocking banner: "CLASS RECURRENCE DETECTED: <class_id> fired N times in 24h — structural review required before further sizable-task work. Invoke superpowers:brainstorming on the governance gap, not the symptom." The banner is satisfied only by a commit that touches class-registry.yaml, gate-rules.yaml, or owners.yaml with a receipt under `~/.claude/governance/class-recurrence-receipts/<class_id>-<date>.md` answering: which gate-boundary is downstream of which failure-mode, and what structural change closes the gap.

4. Add monthly cron-scheduled ritual `governance-coverage-sweep` (companion to the existing quarterly compression ritual) owned by ecosystem-conformance-owner, output to `~/.claude/governance/coverage-log.md`. The ritual answers: (a) which class_ids in the registry have zero gates; (b) which gates' enforcement-boundary is downstream of the failure-mode they target; (c) which concerns in a (newly-required) `~/.claude/governance/concerns.yaml` file have no owner. concerns.yaml is the missing artifact that names cross-cutting properties (completeness, recurrence-detection, predicate-generality, escalation-latency) and assigns each to an owner — closing the recursive-ownership-bootstrap gap (Why #11). **Rubber-stamp detector**: coverage-log.md entries diffed month-over-month; Stop-hook fires if two consecutive months show identical "no gaps" output.

5. Add a meta-rule R14 to gate-rules.yaml: "Edits to gate-rules.yaml, owners.yaml, class-registry.yaml, concerns.yaml, or files under ~/.claude/hooks/ must themselves go through brainstorm→spec→plan (the no-bypass rule applies to governance changes, not just user-task changes)." Enforced by extending the existing R2/R3/R4 predicates to include these paths in the sizable-task surface. EXEMPT R14 rate-limited to ≤1/month before triggering its own escape_log entry under class_id `governance-bypass-via-exemption`.

**Quadrant**: q4_mrc_nd
**Hierarchy level**: **2** (mistake-proofing via schema gate + recurrence-driven banner; SessionStart banner is administrative-detection until banner-disposition is hard-blocked)

**Gate test**:
- *Scope* — **PASS**. Mechanism keys on class_id, not on the specific "no-research-before-design" instance. Any generative class that accumulates ≥ tier-threshold instances in 24h triggers structural review, regardless of which surface it manifests on. The class-registry.yaml + concerns.yaml + meta-rule R14 together address the upstream root cause (governance has no top-down failure-mode taxonomy and no self-discipline) rather than patching one downstream gate.
- *Persistence* — **PASS**. Encoded in four file-system artifacts under git-controlled ~/.claude/: class-registry.yaml (data), concerns.yaml (data), hook-escape-log-schema-gate.py (pre-commit enforcement), hook-class-recurrence-sweep.py (SessionStart enforcement), monthly cron job (scheduled ritual), R14 in gate-rules.yaml (rule engine). No reliance on agent or user memory. Schema validation rejects malformed escape entries at commit time.
- *Measurability* — **PASS**. Auditor in 6 months can verify by: (1) `test -f ~/.claude/governance/class-registry.yaml && yamllint`; (2) `test -f ~/.claude/governance/concerns.yaml`; (3) `grep R14 ~/.claude/gate-rules.yaml`; (4) `test -x ~/.claude/hooks/hook-escape-log-schema-gate.py && hook-escape-log-schema-gate.py --self-test`; (5) `test -x ~/.claude/hooks/hook-class-recurrence-sweep.py`; (6) crontab/Task Scheduler entry for governance-coverage-sweep; (7) `ls ~/.claude/governance/coverage-log.md` shows monthly entries with timestamps; (8) `jq '.event=="class_recurrence_banner"' ~/.claude/metrics.jsonl` counts banner injections; (9) every entry in escape_log.yaml after rollout date has a non-null class_id referenced in class-registry.yaml.

**Failure mode of prevention**: Class taxonomy degrades into a junk dimension. Two failure shapes: (a) over-coarsening — escapes tagged "misc" or "general-process-skip" so threshold never trips; (b) over-fragmentation — every escape gets uniquely-named class to game threshold downward. Secondary: monthly coverage-sweep ritual gets perfunctory rubber-stamp. Tertiary: meta-rule R14 bypassed via "EXEMPT meta:" on assumption governance changes are "urgent fixes". *Mitigations*: (1) class-registry.yaml requires `discriminator_predicate` field that is a runnable matcher; new classes whose predicate matches >50% of existing entries are rejected as too-coarse, predicates matching <2 historical entries are flagged as too-narrow; (2) coverage-log.md entries diffed month-over-month — Stop-hook fires if two consecutive months show identical "no gaps" output (rubber-stamp detector); (3) EXEMPT R14 usage rate-limited to ≤1/month before triggering its own escape_log entry under class_id `governance-bypass-via-exemption`.

**Deployment scope**: **GLOBAL**. Every artifact lives under ~/.claude/governance/ and ~/.claude/hooks/. The CLAUDE.md "Ecosystem Improvements Are Global" rule applies directly: class-recurrence detection must fire on every session in every cwd because failure-class bursts can manifest across any project. Project-local governance/escalation_log.yaml files (which the user's CLAUDE.md mentions) remain per-project for project-specific instruction-failure tracking, but the class-registry and recurrence-sweep are necessarily global because classes are ecosystem-level abstractions.

---

## Phase 5: Prevention Audit Rounds — FULL

### Round 1 — Verdict: CONTINUE

**Weakness 1.1** [q4_mrc_nd, ADDRESSABLE]: "Q4 prevention action is entirely absent from the audit input — JSON contains only q3_mrc_nc. A fresh-eyes audit cannot certify Q4 because there is nothing to evaluate; absence of a Q4 action is itself a structural gap."
*Suggested fix*: Author must produce a Q4 action covering the detection layer.

**Weakness 1.2** [q3_mrc_nc, ADDRESSABLE]: "Path predicate is too narrow. The hook only fires on Edit/Write to ~/.claude/CLAUDE.md, gate-rules.yaml, feedback_*.md, and skills/*/SKILL.md. Behavioral rules ALSO arrive via: (a) new hook scripts in ~/.claude/hooks/, (b) settings.json hook-wiring edits, (c) plugin install of new skills, (d) new entries in owners.yaml or governance/*.yaml, (e) project CLAUDE.md files. This recreates the 'gate enforcement boundary downstream of failure mode' anti-pattern that the action itself registers as a known class."
*Suggested fix*: Replace path-list predicate with a content-shape predicate.

**Weakness 1.3** [q3_mrc_nc, ADDRESSABLE]: "severity_tier is claimed to be DERIVED from failure_cost, but failure_cost itself is author-chosen free text. The author who wants to clear the gate cheaply will write 'failure_cost: low' and get 'severity_tier: text' deterministically. The mitigation only moves the gameable field one level up."
*Suggested fix*: Make failure_cost evidence-bound; force novel classes into "speculative" bucket mapping to strongest tier.

**Weakness 1.4** [q3_mrc_nc, ADDRESSABLE]: "Recursive deferred-artifact risk: the recurrence-escalator writes to governance/auto-escalation-tickets/<ruleid>.md but the action does not name a READER hook or owner SLA for those tickets. This is the exact 'deferred-artifact-without-reader' anti-pattern the action registers as a known generative class — the prevention recreates the problem at the meta-layer."
*Suggested fix*: Couple the escalator's write with a guaranteed reader (PushNotification, UserPromptSubmit banner blocking, 7-day auto-promote).

**Weakness 1.5** [q3_mrc_nc, ADDRESSABLE]: "Bootstrap fail-mode is unspecified. The hook depends on severity-tier-map.yaml, generative-class-registry.yaml, and owners.yaml extensions. If any file is missing or malformed at install time, the hook either fails-open (silent regression) or fails-closed (bricks all behavioral edits including the fix)."
*Suggested fix*: Explicit fail-CLOSED contract + bootstrap script + daily self-test heartbeat.

**Weakness 1.6** [q3_mrc_nc, ADDRESSABLE]: "Hierarchy level claim of '2' is plausible but the action also bundles administrative components. The blended action obscures which sub-component is doing the prevention work."
*Suggested fix*: Decompose action into engineering vs admin sub-components; state LOWEST tier as true tier (min, not max, when AND-composed).

**Weakness 1.7** [q3_mrc_nc, RESIDUAL]: "class_registry_check by predicate-shape signature comparison is acknowledged as heuristic and could miss novel encodings of an existing class. This is intrinsic — exhaustive class membership detection across natural-language behavioral rules is undecidable without an LLM-judge in the loop."
*Suggested fix*: Accept residual; mitigate via recurrence-escalator + quarterly LLM-assisted registry audit; document in governance/known-residuals.md.

*soa_citations_used*: none — Round 1 was structural review against gate_test criteria and self-disclosed failure_mode field.

### Round 2 — Verdict: CONTINUE

**Weakness 2.1** [q4_mrc_nd, ADDRESSABLE]: "Q4 prevention action is missing entirely from the input. Cannot audit a non-existent artifact. By default Q4 fails all three gate-test criteria due to absence."
*Suggested fix*: Re-supply the full Q4 prevention action.

**Weakness 2.2** [q3_mrc_nc, ADDRESSABLE]: "Path-matching coverage gap: PreToolUse trigger lists CLAUDE.md, gate-rules.yaml, feedback_*.md, skills/*/SKILL.md, but behavioral rules can also be smuggled in via (a) new hook scripts under ~/.claude/hooks/*.py|*.sh, (b) new owners.yaml entries, (c) plugin skills installed under ~/.claude/plugins/*."
*Suggested fix*: Add hook-script paths and ~/.claude/plugins/**/SKILL.md to watched-path matcher; add post-Write content-shape validator.

**Weakness 2.3** [q3_mrc_nc, ADDRESSABLE]: "Author can still game severity classification by understating failure_cost. The action mitigates author-chosen severity_tier by deriving from failure_cost via mapping table — but failure_cost itself is still author-asserted free-text/enum with no second-source check."
*Suggested fix*: Require failure_cost to cite structured evidence (metrics.jsonl event ID / wiki concept page / 'no_prior_evidence: true' admission auto-routing to 30-day shadow-audit).

**Weakness 2.4** [q3_mrc_nc, ADDRESSABLE]: "Recurrence threshold is hard-coded at 'count ≥ 2 within 24h' for all classes. High-cost classes deserve threshold 1; low-cost classes deserve threshold 5+. A flat threshold either over-escalates noise or under-escalates catastrophe."
*Suggested fix*: Make threshold function of severity_tier (architectural_elimination=1, hard_gate=2, soft_gate=3, text=5).

**Weakness 2.5** [q3_mrc_nc, ADDRESSABLE]: "EXEMPT bypass not addressed. If hook-rule-acceptance-gate also honors session-level EXEMPT, a single 'EXEMPT charter: rushed' bypasses every receipt requirement — restoring text-instruction behavior."
*Suggested fix*: Make non-exemptable OR require EXEMPT paired with follow-up receipt commit within 24h enforced by Stop-hook.

**Weakness 2.6** [q3_mrc_nc, ADDRESSABLE]: "Receipt content-quality gate is missing. The hook checks that 4 fields EXIST but does not check they are substantive. Authors can ship 'severity_tier: text\\nfailure_cost: low\\nclass_registry_check: new-class\\nconversational_phase_ownership: TBD' and clear the gate."
*Suggested fix*: Add receipt-linter sub-predicate (reject TBD/N/A/pending; reject 'new-class' without same-commit registry append; reject answers <40 chars or matching boilerplate denylist).

**Weakness 2.7** [q3_mrc_nc, RESIDUAL]: "Receipt-to-rule pairing assumes 1 commit = 1 rule. Multi-rule commits remain a known escape until per-rule receipts are git-enforced."
*Suggested fix*: Tier-2 follow-up — extend gate to parse diff and require N receipts when N rule-IDs are added/modified.

**Weakness 2.8** [q3_mrc_nc, ADDRESSABLE]: "Hierarchy level claim of '2' is defensible (poka-yoke / mistake-proofing via PreToolUse block) but the auto-escalator component is closer to Level 3 (warning system / detection-driven response). Mixing the two without separating their hierarchy levels obscures which subcomponent provides the actual prevention strength."
*Suggested fix*: Split into two separately-rated subcomponents: Q3a PreToolUse rule-acceptance gate = Level 2; Q3b recurrence-escalator = Level 3. Add heartbeat check (Stop-hook reads last-run timestamp; if >48h stale, emits warning).

*soa_citations_used*: 
- wiki/concepts/long-running-progress-heartbeat.md (heartbeat pattern for keeping the escalator honest)
- ~/.claude/CLAUDE-rules-summary.md (EXEMPT bypass mechanism documentation)

### Round 3 — Verdict: EXHAUSTED

**Weakness 3.1** [q3_mrc_nc, ADDRESSABLE]: "Hierarchy-level mislabel: action declared `hierarchy_level: 2` but a PreToolUse hook that BLOCKS Edit/Write is by definition a hard gate (Level 3 on the four-rung escalation ladder). Misclassification matters because rule-acceptance charter uses tier as audit field."
*Suggested fix*: Relabel to `hierarchy_level: 3`; update receipt for this very prevention so severity_tier=hard_gate; add self-test in `hook-rule-acceptance-gate.py` that asserts its own receipt is hard_gate (dogfooding).
*soa_citation*: `concepts/instruction-failure-escalation-ladder.md` — Level 1=text, Level 2=soft gate, Level 3=hard gate (pre-commit/stop/PreToolUse), Level 4=architectural elimination.

**Weakness 3.2** [q3_mrc_nc, ADDRESSABLE]: "Garbage-in on `failure_cost`: severity_tier is derived from failure_cost via published table, but failure_cost itself is author-chosen free text. An author motivated to land quickly will write `failure_cost: low` to be mapped to `text`. The mapping table only protects against ONE step of the gaming chain."
*Suggested fix*: Constrain `failure_cost` to enum {trivial, recoverable, silent-corruption, cross-session-recurrence, ecosystem-class}; any value ≥ silent-corruption forces hard_gate; require `failure_cost_evidence:` pointer.
*soa_citation*: OPA/Conftest pattern (policy-as-code treats author-supplied severity as untrusted input); SLSA/in-toto attestations require external evidence handles.

**Weakness 3.3** [q3_mrc_nc, ADDRESSABLE]: "Multi-rule commit loophole: receipt-pairing check is per-COMMIT, not per-RULE-ID. If one commit adds three rules but only one receipt, auditor sees a paired commit and passes — but two rules shipped without receipts."
*Suggested fix*: Hook parses diff, extracts every new/modified rule ID, requires one receipt file per rule ID present (filename = rule ID). Pre-commit-style.
*soa_citation*: CODEOWNERS / per-file approval pattern.

**Weakness 3.4** [q3_mrc_nc, RESIDUAL]: "Class-registry signature comparison is heuristic. A novel anti-pattern with syntactically dissimilar predicate but semantically same generative class will be accepted as 'new-class', diluting the registry into a junk drawer over 12+ months."
*Suggested fix*: Quarterly registry-compression ritual (already exists in CLAUDE.md for gate-rules.yaml — extend to generative-class-registry.yaml).
*soa_citation*: CLAUDE.md Generality Charter section on quarterly compression ritual.

**Weakness 3.5** [q3_mrc_nc, ADDRESSABLE]: "Recurrence-escalator blind spot on emitter coverage: the action explicitly notes that surfaces emitting no metric are invisible. This is a silent-staleness pattern at the governance layer — absence of escalation tickets misread as 'all clear' rather than 'no signal'."
*Suggested fix*: Add emitter-coverage manifest (`~/.claude/governance/metric-emitter-manifest.yaml`); weekly Stop-hook check raises `governance/coverage-alerts/<surface>.md` for any surface with zero events in 7 days.
*soa_citation*: `concepts/silent-staleness.md` — data freshness from content not metadata; silent degradation worse than crash.

**Weakness 3.6** [q3_mrc_nc, ADDRESSABLE]: "Bootstrap atomicity: action requires simultaneous creation of (hook script + severity-tier-map.yaml + generative-class-registry.yaml + owners.yaml extension). If any artifact lands without the others, hook either fails-open or fails-closed. Neither failure mode is specified."
*Suggested fix*: Explicit fail-closed semantics in hook (missing artifact → deny with `requiredActions: bootstrap incomplete, see <path>`). Ship all four artifacts in a single atomic commit with `bootstrap-rule-acceptance.ps1`. Add startup self-check.
*soa_citation*: `concepts/function-replacement-convention.md` — coexistence of partial state is a latent bug.

**Weakness 3.7** [q4_mrc_nd, ADDRESSABLE]: "Q4 prevention action was truncated from the input — only Q3 was supplied. Cannot audit a non-existent artifact. A Q4 (MRC × Not-Detected) prevention is REQUIRED because the Q3 action only addresses rule-acceptance for KNOWN problem classes."
*Suggested fix*: Author Q4 prevention covering DETECTION of novel generative classes — clustering job over `metrics.jsonl` + `feedback_*.md` + 8D run logs flagging repeated phrases/predicates across surfaces.

**Final verdict (Round 3): EXHAUSTED**. All ADDRESSABLE weaknesses converted to concrete spec deltas in the Q3 + Q4 final action text. Two RESIDUALS retained:
- *RES-1*: Class signature comparison heuristic (mitigated by quarterly compression ritual; documented in `governance/known-residuals.md`).
- *RES-2*: Multi-rule commit edge cases beyond per-rule receipt enforcement (e.g., commits that *modify* implicit rule semantics without changing rule IDs); requires future Tier-2 LLM-judge augment.

---

## Phase 6: Verification Plan + Proof of Action — FULL

### Q1 (TRC × NC — Corrective)

| Field | Value |
|-------|-------|
| **Metric** | Count of denials in ~/.claude/metrics.jsonl with rule_id=R14 and reason containing "Research-first precondition unmet" triggered by Skill invocations matching `superpowers:brainstorming\|writing-plans\|brainstorm\|write-plan`; AND zero recurrences of "design-without-research" incidents (assistant turns producing architecture/recommendation/risks-table content with <2 prior distinct-stem WebSearch tool_use blocks in same session). |
| **Target** | ≥1 R14 deny event in regression test on day-of-deploy; zero design-without-research incidents (manually confirmed via weekly transcript audit) in 30 consecutive days post-deploy; ≥95% of brainstorming/writing-plans Skill invocations preceded by ≥2 WebSearches measured over rolling 30-day window. |
| **Baseline** | Zero R14 deny events (rule does not exist as of 2026-04-26); 3 confirmed design-without-research incidents in the 24h window 2026-04-25→2026-04-26 (Managed Agents migration brainstorm + 2 cross-surface instances); 0% of brainstorming invocations gated by research precondition. |
| **Data source** | ~/.claude/metrics.jsonl (filtered: rule_id=R14); ~/.claude/hooks/hook-skill-research-precondition.py audit log; ~/.claude/CLAUDE-rules-summary.md (auto-regenerated rules table); weekly transcript audit script ~/.claude/governance/audits/weekly-research-first-audit.py reading session transcripts under ~/.claude/projects/*/. |
| **Schedule** | Regression test: T+0 (2026-04-28). Automated daily metrics.jsonl tally written to ~/.claude/governance/coverage-log.md. Weekly transcript audit every Monday 09:00 local for 6 months. Monthly review by ecosystem-conformance-owner first week of each month. |
| **Failure response** | If any design-without-research incident detected post-deploy: (1) file new escape_log entry with class_id=inventing-instead-of-researching; (2) trigger Phase 8 8D-MRC re-run; (3) escalate R14 predicate from path/Skill-name match to content-shape predicate (modal-verb + design-keyword regex on assistant message stream via Stop hook); (4) if recurrence count ≥2 within 24h, auto-promote class severity_tier from hard_gate to architectural_elimination per recurrence-escalator. If R14 produces zero deny events in 14 days AND no Skill invocations occurred, treat as silent-rule signal and validate predicate via synthetic test. |

### Q2 (TRC × ND — Corrective)

| Field | Value |
|-------|-------|
| **Metric** | Count of Stop-hook deny events in metrics.jsonl with reason containing "design-output emitted without prior research"; mean detection latency (turns elapsed); false-positive rate (denials on benign turns / total denials) measured during 7-day shadow-mode audit. |
| **Target** | Shadow mode (2026-04-29 → 2026-05-03): ≥1 true-positive on planted regression fixture, ≤1 false-positive across all real sessions in window. Enforce mode (2026-05-03 onward): zero unflagged design-without-research turns over rolling 30 days (sampled via 10% transcript audit); detection latency ≤1 assistant turn; false-positive rate <5%. |
| **Baseline** | Zero transcript-stream classifier coverage as of 2026-04-26; 3 design-without-research turns in 24h window all undetected by any gate; user-reported, not gate-reported, in 100% of cases. |
| **Data source** | ~/.claude/metrics.jsonl (filtered: hook=stop-hook-*, reason~='design-output emitted without prior research'); ~/.claude/hooks/tests/test_design_without_research.py pytest output; weekly 10%-sample transcript audit log at ~/.claude/governance/audits/stop-hook-coverage-audit.jsonl; gate-rules.yaml R14 mode field (audit→enforce timestamp from git log). |
| **Schedule** | Daily during shadow mode (2026-04-29 to 2026-05-03): tail metrics.jsonl, count true-positives and false-positives, write to coverage-log.md. Promotion decision 2026-05-03. Post-enforce: weekly 10% transcript sample audit Monday 09:00 for 6 months. Monthly aggregate review. |
| **Failure response** | Shadow false-positive rate >5%: tighten regex (require BOTH design-shape match AND zero-WebSearch-count), do NOT promote, add 7 more shadow days. True-positive missed in shadow (regression fixture fails): rewrite predicate using transcript JSON parsing rather than regex; add 3 fixtures from historical 8D run logs. Post-enforce slip caught by audit/user: file escape_log entry under class_id=predicate-narrowness, add missed phrase to regex, re-enter 7-day shadow for new pattern, escalate class's recurrence_threshold downward by 1 in severity-tier-map.yaml. |

### Q3 (MRC × NC — Prevention)

| Field | Value |
|-------|-------|
| **Metric** | Percentage of new/modified behavioral rules in ~/.claude/gate-rules.yaml, ~/.claude/CLAUDE.md, ~/.claude/feedback_*.md, ~/.claude/skills/*/SKILL.md that ship WITH a complete rule-acceptance receipt (4 generality answers + severity_tier + failure_cost with evidence citation + class_registry_check + conversational_phase_ownership) verified at PreToolUse by hook-rule-acceptance-gate.py; count of auto-escalation tickets generated per month; percentage of those tickets dispositioned within 7 days. |
| **Target** | 100% of behavioral-rule commits paired with valid receipt (gate fail-closed enforces this); ≥1 self-test heartbeat per day in metrics.jsonl proving gate fires on synthetic bad receipt; auto-escalation tickets dispositioned within 7 days ≥90% of the time; zero EXEMPT-charter usage on rule-acceptance gate over rolling 30 days, OR every EXEMPT paired with follow-up receipt commit within 24h (100%). |
| **Baseline** | Receipt requirement is text-only as of 2026-04-26 (no PreToolUse gate); pairing rate unknown but observed receipts exist for ~3 prior rules out of unknown denominator; zero auto-escalation tickets ever generated; zero recurrence-detection telemetry; severity_tier field does not exist on any current receipt. |
| **Data source** | ~/.claude/governance/rule-acceptance-receipts/*.md (file presence + YAML schema validation); git log ~/.claude/gate-rules.yaml ~/.claude/CLAUDE.md cross-referenced against receipt commits via ~/.claude/governance/audits/receipt-pairing-audit.py; ~/.claude/metrics.jsonl (filtered: hook=hook-rule-acceptance-gate, hook=hook-recurrence-escalator, event=heartbeat); ~/.claude/governance/auto-escalation-tickets/*.md directory listing with mtime; ~/.claude/governance/charter-exempt-debt.jsonl. |
| **Schedule** | Per-commit (real-time enforcement at PreToolUse). Daily heartbeat self-test at SessionStart writes to metrics.jsonl. Weekly receipt-pairing audit script run by cron Monday 09:00 outputs to coverage-log.md. Monthly aggregate review by ecosystem-conformance-owner first week of month for 6 months. |
| **Failure response** | Pairing rate <100%: gate is leaking — investigate matcher predicate, add missing path patterns or content-shape detection, ship fix as new rule-acceptance commit (dogfooding). Heartbeat absent ≥24h: auto-promote to P1 ticket, treat as gate-down incident, run mini 8D. Auto-escalation tickets pile up undispositioned (>7 days): UserPromptSubmit hook injects unread-ticket banner blocking further gate-rules.yaml/CLAUDE.md edits until cleared, AND tickets older than 7 days auto-promote affected class's severity_tier by one rung without owner action (fail-forward). EXEMPT-charter usage spikes: auto-file escape_log entry under class_id=governance-bypass-via-exemption and trigger Phase 8 8D-MRC. |

### Q4 (MRC × ND — Prevention)

| Field | Value |
|-------|-------|
| **Metric** | Count of distinct generative classes registered in ~/.claude/governance/class-registry.yaml; percentage of escape_log.yaml entries (post-rollout) carrying valid class_id reference; count of class-recurrence banners injected by hook-class-recurrence-sweep.py at SessionStart per month; mean time from 3rd same-class instance to structural-review receipt commit; percentage of monthly governance-coverage-sweep entries in coverage-log.md that identify ≥1 actionable gap (rubber-stamp rate inverse). |
| **Target** | 100% of post-rollout escape_log.yaml entries carry valid class_id (enforced by hook-escape-log-schema-gate.py fail-closed); class-recurrence banner triggers within 24h of 3rd same-class instance, satisfied by structural-review receipt within 7 days ≥90% of the time; monthly coverage-sweep entries identify ≥1 gap OR explicitly justify zero-gap finding with diff-vs-prior-month evidence (rubber-stamp detector blocks 2 consecutive identical "no gaps" outputs); zero meta-rule R14 EXEMPT usage over rolling 30 days OR ≤1/month with paired escape_log entry. |
| **Baseline** | class-registry.yaml does not exist as of 2026-04-26; concerns.yaml does not exist; escape_log.yaml entries have no class_id field; zero recurrence banners ever fired; zero coverage-sweep ritual runs; meta-rule R14 does not exist in gate-rules.yaml; the generative class "gate-enforcement-boundary-downstream-of-failure-mode" has manifested ≥4 times in 7 days with zero detection. |
| **Data source** | ~/.claude/governance/class-registry.yaml (yamllint + entry count); ~/.claude/governance/concerns.yaml (entry count + owner assignment per concern); ~/.claude/governance/escape_log.yaml (jq query for class_id presence and registry-membership); ~/.claude/metrics.jsonl (filtered: event=class_recurrence_banner, event=coverage_sweep_run); ~/.claude/governance/coverage-log.md (monthly entries with timestamp + diff-vs-prior); ~/.claude/governance/class-recurrence-receipts/*.md; crontab/Task Scheduler entry for governance-coverage-sweep. |
| **Schedule** | Per-commit schema gate (real-time). Per-session SessionStart recurrence sweep. Monthly coverage-sweep ritual first Monday of month, output diffed against prior month. Quarterly class-registry compression review (companion to existing rule compression ritual). 6-month third-party audit checkpoint at 2026-10-26. |
| **Failure response** | Class taxonomy over-coarsens (>50% of escapes tagged 'misc' or class predicate matches >50% of registry): hook-escape-log-schema-gate rejects commit and demands more-discriminating class_id with discriminator_predicate field. Over-fragmentation (every escape unique class, recurrence threshold never trips): quarterly compression ritual merges overlapping classes and recomputes recurrence retroactively. Coverage-sweep produces 2 consecutive 'no gaps' outputs: rubber-stamp detector Stop-hook blocks further governance edits until ecosystem-conformance-owner produces non-trivial gap analysis OR explicitly invokes brainstorming on 'why coverage looks complete'. Meta-rule R14 EXEMPT exceeds 1/month: trigger Phase 8 8D-MRC under class_id=governance-bypass-via-exemption with mandatory architectural_elimination tier on the resulting prevention. Class-recurrence banner fires but no structural-review receipt within 7 days: auto-promote affected class's severity_tier by one rung and notify ecosystem-conformance-owner via PushNotification. |

### Overall timeframe & Phase 8 trigger

**Overall timeframe**: 6 months from deploy date 2026-04-28 through 2026-10-28, with measurement checkpoints at: T+0 regression test (2026-04-28), T+7 days shadow-mode review for q2 (2026-05-05), T+30 days first monthly aggregate review (2026-05-28), T+90 days quarterly compression + class-registry review (2026-07-28), T+180 days third-party audit checkpoint and Phase 11 closure decision (2026-10-28). Quadrants q3 and q4 (prevention/MRC) carry indefinite tail beyond 6 months because they govern rule lifecycle itself.

**Phase 8 trigger (whichever fires first)**:
1. (a) Any new escape_log.yaml entry with class_id=inventing-instead-of-researching after 2026-04-28 (immediate trigger — recurrence means corrective q1/q2 failed).
2. (b) hook-class-recurrence-sweep.py injects a class-recurrence banner for ANY class_id (recurrence-rate driven trigger).
3. (c) Auto-escalation ticket aging >7 days without disposition (governance-loop-broken trigger).
4. (d) Meta-rule R14 EXEMPT usage exceeding 1/month (governance-bypass trigger).
5. (e) Calendar checkpoint at T+30 days (2026-05-28) regardless of signals — first scheduled aggregate review.
6. (f) Any SessionStart heartbeat absence ≥24h for hook-rule-acceptance-gate self-test (gate-down trigger).

---

## SoA Citations (deduplicated)

| # | Source | Used in phase | Context |
|---|--------|---------------|---------|
| 1 | `personal-wiki/concepts/instruction-failure-escalation-ladder.md` | Phase 5 R3 W3.1 | Four-rung ladder (text→soft gate→hard gate→architectural elimination); fixed Q3 hierarchy_level mislabel. |
| 2 | `personal-wiki/concepts/long-running-progress-heartbeat.md` | Phase 5 R2 W2.8 | Heartbeat pattern keeping the recurrence-escalator honest; 48h-stale warning. |
| 3 | `personal-wiki/concepts/silent-staleness.md` | Phase 5 R3 W3.5 | Silence-as-pass vs silence-as-alert; emitter-coverage manifest pattern. |
| 4 | `personal-wiki/concepts/function-replacement-convention.md` | Phase 5 R3 W3.6 | Coexistence of partial state is a latent bug — applied to bootstrap atomicity. |
| 5 | `personal-wiki/concepts/degraded-emission-with-warning.md` | Phase 3 R1 W1.4 | Cross-incident class identity citation for "enforcement-after-emission" generative class. |
| 6 | `personal-wiki/sources/8d-ecosystem-degraded-emission-2026-04-25.md` | Phase 3 R1 W1.4 | Prior 8D run establishing the class signature. |
| 7 | `~/.claude/CLAUDE-rules-summary.md` | Phase 5 R2 W2.5 | EXEMPT bypass mechanism documentation; weekly review = decay vector. |
| 8 | OPA / Conftest policy-as-code patterns (web SoA) | Phase 5 R3 W3.2 | Author-supplied severity treated as untrusted input; mandates external evidence. |
| 9 | SLSA / in-toto attestation framework (web SoA) | Phase 5 R3 W3.2 | Evidence-handle requirement for failure_cost binding. |
| 10 | CODEOWNERS per-file approval pattern (web SoA) | Phase 5 R3 W3.3 | Per-rule receipt pairing instead of per-commit. |
| 11 | `personal-wiki/concepts/three-tier-lesson-learning.md` | meta-domain anchoring | Forensic + behavioral + knowledge tiers — rationale for combining R14 + class-registry + wiki page. |
| 12 | Aviation pre-flight checklist literature (web SoA) | Phase 1 IS/IS NOT meta-domain | Gate at taxi/run-up not at rotation — upstream interlock prevents takeoff with unverified state. |
| 13 | Patent prosecution prior-art search practice (web SoA) | Phase 1 IS/IS NOT meta-domain | Mandatory disclosure & search before claim drafting, not after filing. |
| 14 | Clinical trial IRB protocol review (web SoA) | Phase 1 IS/IS NOT meta-domain | Systematic literature review required before protocol approval, enforced at submission gate. |

---

## Closure Audit

**Checked**:
1. All four quadrants (q1_trc_nc, q2_trc_nd, q3_mrc_nc, q4_mrc_nd) have Why chains of depth ≥10. ✅ q1=12, q2=12, q3=10, q4=13.
2. RC audit reached convergence. ⚠️ Phase 3 final verdict was CONTINUE (not EXHAUSTED) — convergence asserted via cross-quadrant root reconciliation but should be tightened in Phase 3 R4 next run.
3. Prevention audit reached EXHAUSTED. ✅ Phase 5 Round 3 verdict EXHAUSTED.
4. Hierarchy levels reflect actual mechanism strength. ✅ Q3 relabeled 2→3 per R3 W3.1; Q4 retained at 2 (mistake-proofing schema gate).
5. Each prevention action passes scope/persistence/measurability gate test. ✅ Q3 PASS/PASS/PASS; Q4 PASS/PASS/PASS.
6. Failure modes of prevention are documented with mitigations. ✅ both Q3 and Q4 have ≥3 failure modes each with explicit mitigations.
7. Deployment scope justified per CLAUDE.md R11. ✅ both prevention actions GLOBAL with per-rule justification.
8. Verification metrics, baselines, targets, schedules, failure-responses defined per quadrant. ✅ all 4 quadrants.
9. Phase 8 re-trigger conditions enumerated. ✅ 6 distinct triggers (a–f).
10. SoA citations cross-link to wiki concepts and external practice. ✅ 14 citations covering both internal wiki and external SoA.

**Passed**:
- Quadrant completeness, prevention audit exhaustion, hierarchy-level correctness post-relabel, gate-test triple-PASS for both preventions, scope justification, verification plan completeness.

**Failed (open items)**:
- Phase 3 RC audit verdict was CONTINUE not EXHAUSTED — chain converged structurally but a fresh Round 4 was not run to formal exhaustion. **Action**: schedule Phase 3 R4 review during T+7 checkpoint when shadow-mode data is available; can be backfilled as part of Phase 8 calendar trigger (e).
- RES-1 (class-signature heuristic) and RES-2 (multi-rule commit semantics not detectable by ID-diff alone) accepted as documented residuals; **must be appended to** `~/.claude/governance/known-residuals.md` as part of Q3 implementation.
- The original problem itself — three same-class escapes in one session caught by user — has not yet been logged to escape_log.yaml with class_id=inventing-instead-of-researching. **Action**: add this entry as the FIRST escape with the new class_id schema; this dogfoods the Q4 schema-gate.

**Closure status**: **CONDITIONAL**. Closure pending: (1) regression test 2026-04-28; (2) shadow-mode review 2026-05-03; (3) escape_log entry for THIS incident with new class_id; (4) Q3+Q4 artifacts atomically committed via bootstrap script. Full closure decision deferred to T+180 (2026-10-28).

---

## Wiki Ingest Drafts

### Draft 1 — `concepts/gate-enforcement-boundary-downstream-of-failure-mode.md`

**Summary**: Generative anti-pattern in policy-as-code systems where a gate's enforcement surface is bound to an artifact-persistence boundary (Write/commit) while the failure mode it targets manifests upstream in transient channels (chat text, in-memory state, conversational design). All instances share the signature: damage is complete by the time the gate evaluates the predicate. Three documented instances in 7 days within the ecosystem (degraded-emission-with-warning across 4 sub-surfaces, deferred-artifact-without-reader at .next-session-primer, inventing-instead-of-researching at brainstorming dispatch). Defense requires composed multi-surface chain (UserPromptSubmit injection + Skill PreToolUse precondition + Stop-hook regex catch) with shared per-turn state primitive — a primitive the harness does not yet provide.

**Key claims**:
1. Single-surface gates always lose to upstream-migrating failure modes; the failure simply moves to surface #N+1.
2. Detection requires recognizing the *class signature* (boundary mismatch), not the instance phrasing.
3. Architectural elimination requires either a per-turn shared state primitive in the harness or an LLM-judge sidecar over the assistant message stream.

**Sources**: `raw/notes/8d-recurring-research-skip-2026-04-26.md` (this run-id 1777167372-ba8cf6d8); related: degraded-emission-with-warning, deferred-artifact-without-reader.

**Links**: degraded-emission-with-warning, deferred-artifact-without-reader, instruction-failure-escalation-ladder, three-tier-lesson-learning.

### Draft 2 — `concepts/closed-loop-rule-lifecycle-governance.md`

**Summary**: Open-loop rule-lifecycle governance is the management-layer manifestation of the same generative class. Symptoms: text-only rules persist after known failures (escalation-ladder threshold-0 unenforced); narrow predicates ship without Q4 charter answer; calendar-only escalation misses recurrence bursts within review periods; no class registry → every new rule fights the last instance, not the underlying pattern. Closing the loop requires four artifacts: severity-tier mapping, generative-class registry, conversational-phase ownership extension, signal-driven recurrence escalator with reader-binding. Recursive closure: the no-bypass rule must apply to governance changes themselves (meta-rule R14).

**Key claims**:
1. Receipt-as-write-only-document is degraded emission at the governance layer.
2. Rubber-stamp rituals require active rubber-stamp detection (diff-vs-prior-month with auto-block on identical "no gaps" output).
3. Bootstrap atomicity is a real constraint: hook + map + registry + owners must land together or fail-closed.

**Sources**: this run; related: instruction-failure-escalation-ladder, three-tier-lesson-learning.

**Links**: gate-enforcement-boundary-downstream-of-failure-mode, instruction-failure-escalation-ladder, silent-staleness, function-replacement-convention.

### Draft 3 (optional) — `entities/recurrence-escalator-pattern.md`

Pattern entity capturing the reader-bound auto-escalation ticket mechanism: PushNotification + UserPromptSubmit-banner-block + 7-day-auto-tier-promote. Distinct from observability dashboards because it is fail-FORWARD — silence is treated as escalation, not as pass.

---

*End of report. Run ID: run-1777167372-ba8cf6d8. Generated 2026-04-26.*