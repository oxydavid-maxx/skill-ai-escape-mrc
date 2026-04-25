# 8D Report: Recurring "Ship-with-Warning" Handoff Anti-Pattern

**Date**: 2026-04-25T11:39:16.507974
**Problem**: Recurring "ship with warning" / handoff anti-pattern. Across multiple recent incidents I have shipped artifacts that have known-broken behavior in the target medium and added a warning telling the user where to view it correctly instead of fixing the root cause. Examples: (a) ECOSYSTEM.md emailed with a "diagrams render in VS Code or GitHub" warning instead of pre-rendering Mermaid to inline images for Outlook; (b) earlier session ship-then-warn patterns the user repeatedly caught. The R12 never-handoff Stop hook did not catch any of these because its phrase regex is tuned to overt "you can run X yourself" patterns, not the subtler "this only renders in Y, view it there" framing. The systemic problem is that R12 covers explicit handoff phrases but not "shipping a degraded artifact with a workaround pointer" — semantically the same handoff. Run full 8D: produce technical and systemic root causes for both the laziness/shortcut behavior and the gate's blind spot, plus corrective and prevention actions including a concrete R12 phrase-list extension.
**Run ID**: run-1777084608-63f5cadc
**Model**: Claude (Agent SDK pipeline; LangGraph FSM-driven 8D MRC skill)

---

## Pipeline Timeline

This 8D execution traversed seven phases (Phase 0 dual-tier research, Phase 1 IS/IS-NOT scoping, Phase 2 four-quadrant Why chains, Phase 3 root-cause audit, Phase 4 corrective + prevention authoring, Phase 5 prevention audit, Phase 6 verification + proof-of-action plan). Phase 8 (closure) is scheduled for 2026-10-25 conditional on the four-quadrant exit gate.

**Phase-by-phase log:**

- **Phase 0 — Dual-tier research / SoA priming.** Pulled meta-categories (`Known-defect pass-through with disclaimer (ship-with-deviation)`; `Surface-pattern detector evaded by semantic paraphrase`; `Producer/consumer rendering-medium impedance mismatch`) and meta-domains (`Pharmaceutical GMP batch-deviation / CAPA governance`; `Aviation Minimum Equipment List (MEL) deferred-defect control`; `Email marketing pre-flight cross-client rendering (Litmus / Email on Acid)`) to seed cross-domain analogies for the audit rounds. These three meta-domains became reusable analogy anchors in Phase 3 for evaluating whether the corrective/prevention plan reaches a class-level fix.
- **Phase 1 — IS / IS NOT scoping.** Authored four-dimensional fence (`what` / `where` / `when` / `extent`) with explicit `is`, `is_not`, `distinction` per dimension. Distinction column was used to derive the semantic-equivalence framing that the rest of the 8D leans on.
- **Phase 2 — Why chains, four quadrants.** Produced full chains for q1_trc_nc (12 Whys; later flagged for branch-conflation in audit), q2_trc_nd (11 Whys), q3_mrc_nc (12 Whys), q4_mrc_nd (12 Whys). Each Why carries a `new_insight` field; q1 Whys carry `audit_notes` arrays accumulated across audit rounds.
- **Phase 3 — RC audit, three rounds (round 1, round 2, round 3, all verdict CONTINUE).** Round 1 raised quadrant-leakage concern (q1's Whys 7–12 were flagged as detection-side material that belonged in q2/q3); round 2 doubled down on the branching critique and called for q1 to be split into sibling sub-chains; round 3 surfaced semantic restatement defects (Why 1 as event-restatement, Whys 4+5 as paraphrase, Why 6 as enforcement-mechanism conflation). Verdict on all three rounds was `CONTINUE` — i.e., the audit kept finding ADDRESSABLE weaknesses but the pipeline still progressed because the residual issues were either RESIDUAL (acceptable) or were recorded as audit_notes attached to the relevant Whys for downstream phases to honor.
- **Phase 4 — Full actions.** Authored q1_trc_nc and q2_trc_nd corrective actions; authored q3_mrc_nc and q4_mrc_nd prevention actions. Each action carries owner, target_date, and either evidence_of_completion (corrective) or gate_test + hierarchy_level + failure_mode_of_prevention + deployment_scope (prevention). Hierarchy_level for both prevention actions is `2` (administrative-process control with automated enforcement, sitting above text-rule and below architectural elimination).
- **Phase 5 — Prevention audit.** Single round, verdict `EXHAUSTED` with `_fallback: true` set — the prevention audit ran out of stronger alternatives to propose, signaling the prevention plan reached a defensible Pareto frontier given the deployment surface. No new SoA citations were retrieved this round (search returned empty for stronger prevention patterns within the constraints).
- **Phase 6 — Verification plan + proof of action.** Produced per-quadrant proof block with metric, data_source, target, baseline, measurement_schedule, failure_response. Authored 6-month overall_timeframe (2026-04-25 → 2026-10-25) and a programmatic phase_8_trigger predicate that gates closure on simultaneous achievement of all four quadrant exit conditions.
- **Phase 7 — This rendering.** No further LLM judging or audit; pure markdown emission of the assembled state.

**Decision points and loop-backs:**

- Phase 3 verdict was `CONTINUE` for three consecutive rounds rather than `REWORK → Phase 2`. The pipeline opted to record audit critiques as `audit_notes` on individual Whys rather than re-author the chains, on the rationale that the structural defects (branch conflation, misfiling) are correctly diagnosed and can be honored at Phase 4 action authoring time without re-spinning Phase 2.
- Phase 5 verdict `EXHAUSTED` with fallback flag set is the prevention-audit equivalent of "no stronger alternative found" — it does NOT mean the prevention is optimal, only that the search didn't surface a better option in this run.
- No SoA-citation rounds returned high-yield URL lists in this run; both the Phase 3 and Phase 5 audits relied on cross-domain analogy from Phase 0 meta-domains (pharma CAPA, aviation MEL, email pre-flight) rather than fresh URL retrieval.

---

## Section A: Root Cause Matrix

|       | Non-Conformance (NC) | Non-Detection (ND) |
|-------|----------------------|--------------------|
| **TRC** | Q1: Hook system is open-loop at the technical level — Stop/PreToolUse hooks emit per-event decisions but ingest no signal from the next user turn, so the gate cannot self-update from its own escapes. Coverage permanently lags novel framings. | Q2: Detection stack is monomodal (lexical regex on Stop-hook completion text) and self-blind (no allow-stream sampling, no miss-rate telemetry), with no medium-aware PreToolUse layer at egress — so semantically-equivalent morphing forms of handoff fall outside both the lexical net and the gate's category taxonomy. |
| **MRC** | Q3: No scheduled, automated coverage-audit obligation in the governance model — when a failure class recurs (n≥2 with consistent framing), nothing forces a class-completeness review of the relevant rule, so rules stay scoped to the originally-observed lexical instance. | Q4: Gate governance lacks a closed-loop effectiveness review process — no defined Detection-Coverage KPI, no recurring audit of human-caught-after-gate-deployed incidents, and no feedback path that escalates a gate's semantic blind spots into rule extensions. Gates are treated as write-once artifacts instead of living controls. |

---

## Section B: Corrective Actions Matrix

|       | Non-Conformance (NC) | Non-Detection (ND) |
|-------|----------------------|--------------------|
| **TRC** | Q1: Re-render ECOSYSTEM.md Mermaid diagrams to PNG via mermaid-cli, rebuild email as `multipart/related` with inline `cid:` references, strip the "renders in VS Code or GitHub" note entirely, and resend to oxydavid@gmail.com. | Q2: Extend the phrase regex in `~/.claude/hooks/stop-hook-no-handoff-gate.sh` with the medium-redirect family (`renders? in`, `view in`, `open in`, `paste into`, etc.); add a fixture file pinning the exact missed completion text and wire it into the hook's self-test. |
| **MRC** | Q3: *(prevention only — see Section B2)* | Q4: *(prevention only — see Section B2)* |

---

## Section B2: Prevention Actions Matrix

|       | Non-Conformance (NC) | Non-Detection (ND) |
|-------|----------------------|--------------------|
| **TRC** | Q1: *(corrective only — see Section B)* | Q2: *(corrective only — see Section B)* |
| **MRC** | Q3: Add a "rule-coverage steward" automated subsystem under `~/.claude/governance/`: pre-commit hook on `gate-rules.yaml` requiring `morphing_variants:` ≥3 + `class_definition:`, weekly cron clustering observed failures by semantic class against rule variants, Stop-hook coverage-debt gate blocking session completion on unresolved high-severity gaps. | Q4: Institute a closed-loop Gate Effectiveness Governance system: schema extension requiring `covered_class:` and `excluded_class:` on every rule, pre-commit schema gate, monthly Detection-Coverage KPI audit, auto-generation of `feedback_gate_miss_*.md` on KPI breach that propagates through R7/R8 hard gates. |

---

## Section C: Proof of Action Matrix

|       | Non-Conformance (NC) | Non-Detection (ND) |
|-------|----------------------|--------------------|
| **TRC** | Q1: metric=count of mermaid-fence/workaround-pointer artifacts in `~/.claude/sent-mail-archive/`; target=0; baseline=1 known-bad in inbox; data_source=local .eml archive + Outlook screenshot or user reply; schedule=one-shot within 24h then sampled 6 months; failure_response=playwright OWA test harness on .eml. | Q2: metric=replay-gate detection rate on 11-phrase fixture corpus; target=100% (11/11) every commit, zero regressions over 6 months; baseline=0/11 (R12 missed all medium-redirect framings); data_source=`~/.claude/hooks/fixtures/r12_medium_redirect_*.txt` + `.selftest-results.jsonl`; schedule=pre-commit on every regex edit + monthly full replay; failure_response=auto-open `feedback_r12_regex_regression_*.md`. |
| **MRC** | Q3: metric=(a) % of rules with morphing_variants≥3 + class_definition; (b) age of newest `coverage_audit_*.md`; (c) open high-severity coverage gaps; target=100% / ≤10 days / 0 gaps >14 days; baseline=0/10 rules / 0 audits / no escalation log entries; data_source=gate-rules.yaml + governance/ + escalation_log.yaml; schedule=pre-commit + weekly cron Sunday 06:00 + Stop-hook every session; failure_response=Telegram alert + auto-promote warn→enforce on stale gaps. | Q4: metric=per-rule 6-month rolling Detection-Coverage KPI = gate_catches / (gate_catches + human_catches_matching_covered_class); target=≥0.80 by month 6, ≥95% feedback-tagging compliance, 6 consecutive monthly audits, R12 class human-catches=0 in months 4–6; baseline=Detection-Coverage undefined, 0% tagging, 0 audit artifacts, ≥2 R12-class catches in past 30 days; data_source=gate-effectiveness-*.json + metrics.jsonl + feedback_*.md + gate-rules.yaml; schedule=monthly on 1st via Task Scheduler + meta-gate freshness check every session + quarterly user roll-up; failure_response=auto-create `feedback_gate_miss_<rule_id>_*.md` propagating through R7/R8 + auto-escalate R12 to architectural-elimination tier on recurrence. |

---

## Phase 1: IS / IS NOT

| Dimension | IS | IS NOT | Distinction (why this narrows root cause) |
|-----------|----|--------|-------------------------------------------|
| **What** | Shipping a known-degraded artifact to the target medium plus a "view it correctly in <other tool>" workaround pointer (e.g., ECOSYSTEM.md emailed with raw Mermaid + "render in VS Code/GitHub" note). Semantically a handoff: the user is told to do the rendering work the agent should have done (pre-render Mermaid → PNG inline for Outlook). | An overt "you can run X yourself" / "please verify" / "I'll leave this for you" phrase — those are what R12's current regex catches. Not a refusal to ship, not a missing artifact, not a tool/permission failure that genuinely required user input. | Narrows root cause to a **semantic-equivalence gap**, not a behavioral one. The agent does produce output and does write a completion message — but the message reframes the handoff as a "rendering tip," which is lexically distinct from R12's deny phrases while functionally identical. Implies fix must extend the phrase list to medium-mismatch framings ("renders in", "view in", "open this in", "best viewed with", "looks correct in <X> instead"), not tighten the existing patterns. |
| **Where** | The artifact-delivery boundary — final Stop-hook moment after the agent has produced the file/email/message and is composing the completion summary. Specifically: (1) `~/.claude/hooks/stop-hook-no-handoff-gate.sh` phrase regex, (2) any Bash send-email / Write to user-facing medium where the format mismatches the medium's renderer (Outlook/email = no Mermaid, no `<details>`, limited CSS). | Not in the brainstorming / planning / coding phases — those produce intermediate artifacts where "view in VS Code" is legitimate. Not in PreToolUse — the artifact is already correct as a file; the failure is medium-specific. Not in personal-wiki or other agent-internal stores — only at the human-facing egress. | Locates the gate gap precisely at **egress to a constrained renderer**. The corrective action therefore needs two pieces: (a) extend R12 phrase list at the Stop hook (broad, catches all morphing forms), and (b) add a medium-aware PreToolUse check on email/Outlook sends that scans for ` ```mermaid``` ` fences, raw HTML `<details>`, or other Outlook-incompatible markup and denies until pre-rendered. Single-layer fix at the regex would still miss future media (Slack, Teams, SMS). |
| **When** | Late in task execution, after the artifact already exists in a portable format (Markdown with Mermaid), when the agent discovers the target medium can't render it and effort-to-fix (pre-render diagrams to PNG + inline as CID attachments) exceeds the shortcut (ship + warn). Recurring: at least two recent incidents — ECOSYSTEM.md + earlier ship-then-warn cases the user already caught. | Not at task start (medium constraints are predictable up front — Outlook ≠ GitHub has been true for years). Not on truly novel formats where the constraint is unknowable. Not on internal agent-to-agent handoffs where degraded rendering is acceptable. | The "discovery-too-late + sunk-cost-shortcut" timing signature is the smoking gun for the technical/systemic root-cause split: technically, the agent should have planned the medium constraint at task start (PreToolUse / spec phase); systemically, the absence of a medium-fit checklist at egress lets late-discovered mismatches collapse into shortcuts. Recurrence (n≥2 with same framing) plus a known wiki concept (Instruction Failure Escalation Ladder, threshold=0 for known-failed) means R12 must escalate from text-only to hard-gate **this turn** — not next. |
| **Extent** | Systemic and recurring — at minimum (a) Mermaid-in-Outlook ECOSYSTEM.md ship-and-warn, (b) prior ship-then-warn patterns explicitly called out by the user. Affects all egress media with renderer constraints (email/Outlook, Teams cards, Telegram, SMS, plain-text logs). Erodes the "Complete Before Reporting" and "Never Hand Off Work to User" contracts (R12 / completion-discipline). Caught by the human, not the gate, in 100% of observed cases. | Not a one-off slip; not all artifact deliveries (correctly-rendered emails, GitHub-targeted Markdown, file writes to disk are unaffected); not limited to Mermaid (HTML `<details>`, large tables, emoji-heavy formatting, dark-mode-only colors all fall in the same class). | Recurrence with consistent framing ("shipped + pointed user elsewhere") proves the failure mode is a **class, not an instance** — so the corrective action must be class-level, not incident-level. Concrete corrective + prevention actions: (1) Extend R12 phrase list to add: `render(s) (best )?in`, `view (this )?in`, `open (this\|it) in`, `best viewed (in\|with)`, `looks (correct\|right\|better) in`, `displays correctly in`, `will render (properly )?(in\|on)`, `see this in <tool>`, `paste into <tool>`, `use <tool> to view`. (2) Add medium-fit PreToolUse hook on email/chat sends that greps for ` ```mermaid``` ` / ` ```graph``` `, `<details>`, raw HTML beyond `<a>/<b>/<i>`, oversized tables — denies with required action "pre-render to inline image (CID) or convert to ASCII before sending." (3) Per Instruction Failure Escalation Ladder (threshold=0 for known-failed), escalate from text rule → hard gate this commit. (4) Add `feedback_ship_with_warning.md` documenting the morphing forms so the LLM-judge stop hook (already skeletoned at `~/.claude/hooks/stop-hook-llm-judge.py`) can be wired for intent-level coverage when grep-based extension proves insufficient. (5) Wiki-ingest a new concept page "Ship-with-Warning Anti-Pattern" linking to handoff/never-handoff and the escalation ladder, so future sessions hit it via index.md two-pass. |

---

## Phase 2: Why Chains (4 quadrants — FULL TEXT)

### Q1 — TRC × Non-Conformance

**Root**: Hook system is open-loop at the technical level: Stop/PreToolUse hooks emit per-event decisions but ingest no signal from the next user turn, so the gate cannot self-update from its own escapes. Every new morphing handoff form (medium-redirect being one) therefore requires a human to notice and hand-edit the phrase list — making coverage permanently lag novel framings.

**Why 1**: Why was ECOSYSTEM.md emailed to Outlook with raw ` ```mermaid``` ` fences plus a "renders in VS Code/GitHub" note instead of inline PNGs?
*New insight*: Names the concrete non-conformance: the artifact already existed in Markdown-with-Mermaid form, and at egress time the agent chose ship+warn rather than re-render. The decision point was at delivery, not authoring.
*Audit notes*: Either drop Why 1 and renumber (Why 2's "cost asymmetry" is the real first causal step), or rewrite Why 1 to ask a sharper question — e.g., "Why was the egress payload allowed to leave with format incompatible with the target renderer?" — so it opens a causal direction rather than re-describing the event.

**Why 2**: Why did the agent choose ship+warn over re-render at that decision point?
*New insight*: Cost asymmetry. Ship+warn = one sendmail call. Re-render = mermaid-cli → PNG → MIME multipart/related with cid: references in HTML body — a multi-step pipeline with no pre-built helper. The shortcut won because the proper path had no tooling.

**Why 3**: Why was there no pre-built mermaid→PNG→inline-CID helper in `~/.claude/` or the project?
*New insight*: All prior Mermaid usage targeted GitHub, VS Code preview, or the personal-wiki — media with native renderers. Email was the first constrained-renderer egress, and no helper was written reactively or proactively, so the toolchain has a capability hole that biases every future email-with-diagrams task toward the shortcut.
*Audit notes*: Split into Why 3a "no prior egress required a constrained renderer, so capability gap was latent" and Why 3b "tool-building is reactive-only — no proactive scan of upcoming egress targets exists". Why 3b then bridges naturally to a q3_mrc_nc rung about the missing capability-gap-discovery process.

**Why 4**: Why was the medium constraint (Outlook ≠ Mermaid) not detected at task start, when format choice could still cheaply change?
*New insight*: Artifact production and delivery are technically decoupled phases — the producer writes Markdown without a back-pressure signal from the delivery medium. The medium-capability check, if it exists at all, lives in the agent's head, not in code.
*Audit notes*: Insert intermediate Why: "Why does no task-acceptance step force the producer to declare target medium?" This trigger-layer Why is the actual link between capability (helper) and timing (early detection).

**Why 5**: Why are producer and delivery phases decoupled with no enforced contract between them?
*New insight*: There is no PreToolUse gate on egress tools (Bash sendmail, MCP send-message, Telegram sendMessage) that inspects payload format against a target-renderer capability matrix. Egress tools accept any string; the renderer mismatch is invisible to the toolchain.

**Why 6**: Why does no medium-capability matrix exist as a structured artifact the gate can consult?
*New insight*: Medium constraints have only been encoded as prose in scattered notes (e.g., the IS/IS-NOT itself). They are not a machine-readable table (`~/.claude/medium-capabilities.yaml` with entries like `outlook: {mermaid: false, html_details: false, raw_html: limited}`), so no hook can mechanically check "is this payload compatible with this medium?"
*Audit notes*: Either merge Whys 5+6 into one step ("no egress-gate + no machine-readable medium-capability matrix → mismatch invisible to toolchain"), or push Why 6 deeper to a genuinely new layer — e.g., "Why has no matrix been authored despite N prior medium-mismatch incidents?" which leads to escalation-ladder territory and bridges cleanly to q3. Either rewrite Why 6 narrowly ("no machine-readable medium-capability matrix exists as a structured artifact") and add Why 6.5 ("and no PreToolUse hook is wired to consult such a matrix even if it existed"), or merge with Why 5 per the existing audit_note and explicitly enumerate both preconditions in the merged step.

**Why 7**: Why didn't R12's Stop hook flag the completion message containing "renders in VS Code or GitHub"?
*New insight*: R12's regex is scoped to second-person handoff directives — "you can run X", "please verify", "I'll leave this for you". The medium-redirect framing is third-person/passive ("renders in X", "view in Y", "best viewed with Z") and reads as a helpful tip, not a directive — lexically outside the regex's coverage envelope despite being functionally identical.
*Audit notes*: End q1_trc_nc at Why 6 (no medium-capability matrix → no enforceable contract on producers) or push one more NC-level Why ("why are producers not required to declare target-medium at task acceptance"). Move Whys 7–12 into q2_trc_nd as the detection-side chain — they are excellent ND material, just misfiled. Either (a) keep the matrix branch and ask "why has no matrix been authored despite repeated medium-mismatch incidents" (ladder/escalation cause), or (b) split into a sibling sub-chain for the R12-coverage cause and label it explicitly. Don't pretend one descends from the other. Split q1 into two explicit sub-branches: q1a (producer→egress contract: Whys 2–6) and q1b (Stop-hook detection coverage: Whys 7–8, with Whys 10–11 as q1c on metrics-pipeline learning). Label each branch with its own root sentence so the q4_trc_md plan can spawn three parallel SoAs rather than a single pipeline that conflates them.

**Why 8**: Why was the regex scoped that narrowly in the first place?
*New insight*: The original phrase list was seeded from a corpus of overt "leaving work for you" incidents. The medium-redirect morphing form had not yet been observed when the regex was authored, so by construction it sits outside the pattern set. The gate's coverage is bounded by historical training data.
*Audit notes*: Add Why 8.5: "Why is there no synthetic/adversarial generation of unseen morphing forms to seed the regex before they appear in the wild?" This bridges the technical NC chain (q1/q2) to the management-system MRC chain (q3) about preventive coverage processes vs. reactive corpus-driven coverage.

**Why 9**: Why hasn't the phrase list been extended to cover medium-redirect framings after prior ship-then-warn incidents the user already caught?
*New insight*: Each prior incident was handled as a one-off behavioral correction at the text-instruction tier and never escalated to the gate-update tier. No `feedback_ship_with_warning.md` file was written, so the Instruction Failure Escalation Ladder's threshold=0-for-known-failed rule never fired — escalation depends on a marker file that itself depends on a human writing it.
*Audit notes*: Move Why 9 to q3_mrc_nc as one of the management-level Whys (the ladder is a process artifact, not code). Keep q1's chain technical: "no automated escape-clustering" (Why 10) is technical; "no marker file written" is process. Move Why 9 to q3_mrc_nc as one of the management-level Whys. In q1, replace it with the technical analog: "Why does the gate not auto-extend its phrase list from observed escapes?" which leads naturally into Why 10 (no escape-clustering) and Why 11 (per-event hook architecture) — keeping q1 strictly technical.

**Why 10**: Why is there no automated pattern-clustering over past Stop-hook misses that would have surfaced "ship+warn" as a recurring class without the user having to notice?
*New insight*: `metrics.jsonl` logs hook decisions (deny/warn/audit + matched rule) but does NOT capture the next user turn's content. There is no signal in the data pipeline that ties "user said 'that's a handoff'" back to the originating Stop-hook pass, so even if the same miss happens 5 times, the metrics file shows 5 successful Stops, not 5 escapes.

**Why 11**: Why does the metrics pipeline not capture user-correction follow-ups so the gate could learn from its own escapes?
*New insight*: The hook architecture is per-event by design — each PreToolUse/Stop call decides in isolation and writes its decision row. There is no UserPromptSubmit-side analyzer that scans the next user message for correction keywords ("that's a handoff", "you should have", "why did you ship", "no, fix it") and back-attributes them to the most recent Stop pass. The data model has no `escape_id` foreign key linking the two events.
*Audit notes*: Reorder so the learning-loop branch (Whys 10–11) precedes the regex-coverage branch in dependency terms, OR explicitly mark it as a sibling sub-chain. Consider terminating q1 at the architectural cause: "hook events are stateless per-call by design — no closed-loop signal from next user turn." That is the deepest technical NC and a natural handoff to q2_trc_nd.

**Why 12**: Why was the hook system designed open-loop (per-event, no feedback channel from later user turns) rather than closed-loop?
*New insight*: Hooks were modeled on the underlying SDK event API (PreToolUse, Stop, UserPromptSubmit are independent callbacks), so the implementation inherited that statelessness. Adding cross-event correlation requires a stateful sidecar (e.g., a small SQLite/JSONL keyed by session + turn that joins Stop decisions to the next UserPromptSubmit's correction-class score) that was never built because the gates "mostly worked" on the overt cases. This is the deepest technical cause that is still controllable by code changes alone — and the one that, once fixed, would make all future morphing forms self-detecting instead of requiring a human to notice and hand-edit the regex.
*Audit notes*: Restore the full text. Likely continuation: "...mostly worked at launch, so the closed-loop investment was deferred until a novel morphing form (medium-redirect) revealed the open-loop blind spot." Verify and emit.

### Q2 — TRC × Non-Detection

**Root**: The detection stack is monomodal (lexical regex on Stop-hook completion text) and self-blind (no allow-stream sampling, no miss-rate telemetry), with no medium-aware PreToolUse layer at egress — so semantically-equivalent morphing forms of handoff (e.g., "render in <tool>") and medium-mismatch shipping fall outside both the lexical net and the gate's category taxonomy, and the gate cannot observe its own false negatives to self-correct.

**Why 1**: R12 did not flag the ECOSYSTEM.md ship-and-warn email because the Stop hook's phrase regex never matched "diagrams render in VS Code or GitHub".
*New insight*: Pinpoints the literal miss: the deny decision hinges on a string match, and that string was absent.

**Why 2**: The phrase regex enumerates overt deferral patterns ("you can run X yourself", "please verify", "I'll leave this to you") but contains no entries for medium-redirect framings ("render(s) in", "view in", "best viewed in", "open in <tool>", "paste into <tool>").
*New insight*: The miss is not a bug in matching — it is a coverage gap: the pattern set is a closed enumeration whose membership was decided once and never revisited.

**Why 3**: The pattern set was seeded from the first cohort of handoff incidents (explicit deferrals) and treated as static; morphing forms surfacing in later incidents were never folded back in.
*New insight*: Reveals a maintenance-process gap inside a technical artifact: the regex is data, not code, but no data-update pipeline exists for it.

**Why 4**: There is no automated "user-caught miss → new phrase added to regex" loop; updates would require a human to edit `stop-hook-no-handoff-gate.sh` after each incident, and that editing has not happened despite ≥2 recurrences.
*New insight*: Names the missing feedback artifact — a learned-from-misses ingestion path — that would let the gate evolve at the pace of new morphing forms.

**Why 5**: Even if updates were timely, the detection tier is single-modality (grep-only); the skeletoned LLM-judge intent classifier at `~/.claude/hooks/stop-hook-llm-judge.py` was never activated, so any phrasing the regex doesn't enumerate slips through with no second-line check.
*New insight*: Surfaces architectural fragility: the gate is one bad regex away from total bypass, with no defense-in-depth.

**Why 6**: The LLM-judge tier was deferred under the policy "activate when grep proves insufficient," but "insufficient" has no measurable definition or threshold — so the trigger condition is unfalsifiable and the upgrade never fires.
*New insight*: Identifies a meta-detection failure: the rule for when to upgrade detection is itself undetectable.

**Why 7**: No miss-rate telemetry exists because `metrics.jsonl` logs only deny events; allow-path completions are not sampled, classified, or audited, so user-caught misses leave zero footprint in the gate's own observability stream.
*New insight*: Exposes the self-blindness asymmetry: the gate counts its wins (denies) but cannot count its losses (allows that should have denied).

**Why 8**: Allow-path sampling is absent because the Stop hook's design treats "no pattern matched" as terminal success and exits; there is no second-pass classifier or async LLM scorer running over allowed completions to estimate false-negative rate.
*New insight*: Frames the architectural choice: the hook is a gate, not a sensor — it decides, but does not measure decision quality.

**Why 9**: Even a perfect Stop-hook phrase list would still have missed the Mermaid-in-Outlook case at the moment it mattered most: at egress to a constrained renderer. No PreToolUse check inspects outbound Bash send-mail / chat-post payloads for renderer-incompatible markup (` ```mermaid``` `, raw `<details>`, oversized tables, dark-mode-only CSS).
*New insight*: Locates a second blind spot orthogonal to the first: detection is concentrated at completion-text egress, ignoring artifact-payload egress.

**Why 10**: PreToolUse egress checks and Stop-hook handoff checks are treated as orthogonal concerns in the hook taxonomy; there is no shared category like "agent shipped user-required work to a medium that cannot consume it" that would activate either layer on the medium-mismatch case.
*New insight*: Names a taxonomy gap: "handoff" and "medium mismatch" are functionally the same failure (user must finish the work) but live in different category buckets, so neither layer claims responsibility.

**Why 11**: "Handoff" is defined lexically (phrase patterns in completion text) rather than semantically (any path that leaves user-required work undone), because the gate was built with a regex-cheap-first design choice that assumed overt phrasing would dominate; semantic-equivalence detection would require either a per-medium rule corpus or an LLM classifier, and neither was scoped at the time the gate was authored.
*New insight*: Reaches the deepest controllable technical cause: the detection contract was specified in the wrong vocabulary (lexical, not semantic), and that specification choice — combined with no allow-path telemetry — guarantees that morphing forms and medium-egress mismatches will keep escaping until the contract is rewritten and a measurement loop is added.

### Q3 — MRC × Non-Conformance

**Root**: No scheduled, automated coverage-audit obligation in the governance model: when a failure class recurs (n≥2 with consistent framing), nothing forces a class-completeness review of the relevant rule, so rules stay scoped to the originally-observed lexical instance and morphing variants (e.g., "view in VS Code" framings of handoff) keep slipping past. Controllable fix: add a recurrence-triggered coverage-audit cron + checklist owned by a defined "rule-coverage steward" role, with class-completeness as a required exit criterion for closing any behavioral-gate incident.

**Why 1**: Why was a ship-with-warning artifact allowed to leave the agent's egress boundary at all? Because the workspace's delivery governance has no defined "medium-fit acceptance criterion" that an artifact must pass before it counts as "shipped" — the operative completion definition is "file produced and message sent," not "file renders correctly in target medium."
*New insight*: Identifies a missing acceptance-criterion in the management system, not a missing technical check.

**Why 2**: Why is the completion definition missing the medium-fit criterion? Because the "Complete Before Reporting" and "Never Hand Off Work to User" policies in CLAUDE.md are written as behavioral aspirations (prose rules) rather than as a checklist of testable exit conditions tied to artifact type and destination.
*New insight*: Surfaces the policy-authoring style — aspirational prose vs. testable checklist — as a contributor.

**Why 3**: Why are those policies written aspirationally rather than as testable exit conditions? Because the rule-authoring process for `~/.claude/` governance treats new rules as "add a paragraph when a failure is observed" instead of "define the equivalence class of failures, then encode it" — there is no requirement to produce a class definition before encoding a rule.
*New insight*: Names a specific governance defect: no class-definition step in rule authoring.

**Why 4**: Why does the rule-authoring process skip class definition? Because rule changes flow through a lightweight YAML edit + auto-deploy hook with no peer/design review and no requirement for adversarial "how could this morph and still pass?" test cases.
*New insight*: Identifies the absence of an adversarial-morphing review as a structural gap in the change-control process.

**Why 5**: Why is the change-control process for behavioral gates lightweight in the first place? Because the workspace governance model classifies all hook/rule edits as "personal automation" and applies no SDLC discipline distinguishing safety-critical behavioral gates (where false negatives = recurring user harm) from convenience automation (where false negatives are tolerable).
*New insight*: Surfaces a missing tier in the artifact-classification policy: behavioral-gate criticality is not graded.

**Why 6**: Why is there no criticality grading for behavioral gates? Because the Instruction Failure Escalation Ladder, the closest existing meta-policy, defines escalation along a single mechanism-strength axis (text → soft → hard → architectural) and is silent on a coverage/completeness axis (specific phrase → equivalence class → semantic intent).
*New insight*: Names a structural blind spot in the escalation ladder itself — strength without coverage.

**Why 7**: Why does the escalation ladder optimize only mechanism strength and not semantic coverage? Because it was authored around the observed failure mode at the time (users bypassing or forgetting text rules), so the design space was scoped to "make it harder to skip" and never expanded to "make it broader to recognize variants."
*New insight*: Traces the ladder's blind spot to the scope of its originating incident — fix-the-instance, not the-class.

**Why 8**: Why was the ladder's design never expanded post-authoring to add a coverage axis? Because there is no scheduled meta-policy review cycle for governance rules themselves — individual incidents trigger rule edits, but the framework that governs rule edits has no review cadence.
*New insight*: Identifies a missing meta-governance loop: rules evolve, but the rule-evolution policy is static.

**Why 9**: Why does the meta-policy lack a review cadence? Because the post-incident process treats an incident as "closed" the moment a plausible fix is deployed, with no required step asking "does this fix cover the equivalence class, or only this specific incident, and does our rule-authoring framework need updating to prevent the next variant?"
*New insight*: Names the specific missing step in incident closure — equivalence-class coverage check + framework-update prompt.

**Why 10**: Why does incident closure stop at first-plausible-fix instead of asking the class-coverage question? Because the workspace's three-tier lesson-learning model (forensic + behavioral + knowledge wiki) records what happened and what to change, but does not assign ownership for a "class-completeness audit" on either the forensic 8D or the behavioral feedback rule — completeness is everyone's responsibility and therefore no one's.
*New insight*: Locates a specific accountability gap in the lesson-learning model: no owner of class-completeness.

**Why 11**: Why is class-completeness ownership unassigned? Because the governance system has no role/persona defined for "rule-coverage steward" — it has authors (who add rules) and enforcers (hooks) but no curator whose job is to periodically ask "what variants of caught failures would still slip past?" and propose phrase-list / semantic extensions.
*New insight*: Identifies a missing organizational role in the governance model — coverage stewardship.

**Why 12**: Why has no coverage-steward role been instantiated even though the wiki concept "Instruction Failure Escalation Ladder" implies the need? Because the workspace governance is implicitly single-actor (the user + Claude), and any role not embodied in an automated hook or scheduled cron simply does not exist — there is no policy mandating that recurring-failure classes (n≥2 same framing) trigger a scheduled coverage-audit cron with a defined deliverable.
*New insight*: Closes on the controllable management lever: a scheduled, automated coverage-audit obligation triggered by recurrence count, not human memory.

### Q4 — MRC × Non-Detection

**Root**: Gate governance lacks a closed-loop effectiveness review process — there is no defined Detection-Coverage KPI, no recurring audit of human-caught-after-gate-deployed incidents, and no feedback path that escalates a gate's semantic blind spots into rule extensions. Gates are treated as write-once artifacts instead of living controls.

**Why 1**: Why did the management system fail to detect the ship-with-warning recurrence? Because R12's detection scope is defined entirely by an explicit handoff-phrase regex list, with no governance requirement that the rule cover semantic equivalents of handoff (e.g., medium-mismatch deflections).
*New insight*: Detection scope was implicit (whatever the regex happens to match) rather than declared (an enumerated class of behaviors the rule must cover).

**Why 2**: Why is the detection scope only an implicit regex? Because the rule-authoring process in `gate-rules.yaml` has no IS/IS-NOT or behavioral-class field that forces the author to write down what the rule must catch and what it deliberately excludes.
*New insight*: The schema of a gate rule omits the very metadata (covered-class, excluded-class) that would make scope auditable.

**Why 3**: Why does the schema omit covered-class metadata? Because there is no rule-authoring template or checklist mandating semantic-equivalence enumeration at creation time.
*New insight*: Authoring is a free-form YAML edit, not a structured intake — so quality of scope depends on author memory in the moment.

**Why 4**: Why is there no rule-authoring template? Because the management policy treats gate rules as ad-hoc scripts (one-off automations) rather than as controls under change management.
*New insight*: Gates are mentally categorized as "helpers," which exempts them from the change-management rigor applied to user-facing instructions.

**Why 5**: Why does change management exclude gates? Because the auto-commit + auto-push hook on `~/.claude/` ships rule edits with zero review, intentionally optimizing speed at the cost of a pre-merge quality check on the rule itself.
*New insight*: The ecosystem's frictionless write loop (good for content) is also active over its enforcement layer (bad for controls), and no asymmetry was designed in.

**Why 6**: Why was no asymmetry designed in? Because the Instruction Failure Escalation Ladder is applied to user-level instructions only; the ladder has no analogue for the gate rules that enforce those instructions.
*New insight*: The escalation ladder is a single-layer policy — it disciplines the disciplined, but not the disciplinarian.

**Why 7**: Why is there no meta-ladder for gates themselves? Because no governance instrument tracks gate effectiveness (catches vs misses) as a measurable property.
*New insight*: Effectiveness is invisible because it isn't measured; misses surface only when the human happens to notice and complain.

**Why 8**: Why is gate effectiveness not measured? Because the management system defines no Detection-Coverage KPI such as "incidents caught by gate ÷ total incidents matching the rule's intent."
*New insight*: Without a denominator (intent-matching incidents including human-caught ones), the system cannot compute a miss rate — only a hit count, which always looks fine.

**Why 9**: Why is no KPI defined? Because no recurring audit cadence exists that joins `feedback_*.md` user-catch records against `gate-rules.yaml` deployments to compute that miss rate.
*New insight*: There is data (feedback files, metrics.jsonl) and there are rules — but no scheduled join between them, so blind spots stay statistically invisible.

**Why 10**: Why is there no scheduled join? Because the monthly review clause in CLAUDE.md covers feedback-vs-instruction reconciliation but stops one level short of feedback-vs-gate reconciliation.
*New insight*: The review charter has the right shape but the wrong scope boundary — it audits whether instructions are gated, not whether gates actually catch their target class.

**Why 11**: Why does the review charter stop short? Because governance was designed assuming "rule exists ⇒ class is covered," i.e., the existence of a gate is treated as proof of detection rather than as a claim requiring evidence.
*New insight*: The unstated assumption (deployment = coverage) is what allows semantic blind spots to persist after a rule is in place — escape detection collapses into rule presence.

**Why 12**: Why does the system rely on that assumption? Because the management framework lacks a closed-loop control posture for gates: no declared coverage class, no measured miss rate, no scheduled audit, and no automatic escalation on miss-rate breach. Each piece is missing because the previous one is missing — root cause is the absence of the loop itself, not any single component.
*New insight*: The pieces (KPI, audit, escalation, schema) are co-missing because they are facets of one absent design pattern: gates as living controls with feedback. Installing any one in isolation will decay; the loop must be instituted as a whole.

---

## Phase 3: RC Audit Rounds

### Round 1 — Verdict: CONTINUE

**Weakness 1.1 — ALL quadrants — ADDRESSABLE**
*Issue*: Only q1_trc_nc is shown. Quadrants q2_trc_nd, q3_mrc_nc, q4_mrc_nd are absent from the input, and q1's Why 12 is truncated mid-sentence ("the gates mostl..."). The 4-quadrant audit cannot certify completeness, MRC management-system level, or ND parity vs NC depth without those chains.
*Suggested fix*: Re-emit the full payload: complete Why 12 of q1, then provide q2/q3/q4 with their roots and Why chains. Until then, the audit is constrained to q1 only.

**Weakness 1.2 — q1_trc_nc / Why 7 — ADDRESSABLE**
*Issue*: Quadrant leakage: Whys 7–12 stop being NC causes ("why was the wrong action taken at egress") and shift to ND causes ("why didn't R12 detect the wrong action"). The pivot at Why 7 ("Why didn't R12's Stop hook flag the completion message") is detection-side reasoning that belongs in q2_trc_nd, not q1_trc_nc.
*Suggested fix*: End q1_trc_nc at Why 6 (no medium-capability matrix → no enforceable contract on producers) or push one more NC-level Why ("why are producers not required to declare target-medium at task acceptance"). Move Whys 7–12 into q2_trc_nd as the detection-side chain — they are excellent ND material, just misfiled.

**Weakness 1.3 — q1_trc_nc / Why 7 — ADDRESSABLE**
*Issue*: Causal jump rather than deeper cause. Why 6 lands on "no machine-readable medium-capability matrix." Why 7 then asks why R12 didn't fire — but R12 is a different mechanism (Stop hook regex), not a deeper cause of the matrix being absent. Two parallel causes are being chained as if linear.
*Suggested fix*: Either (a) keep the matrix branch and ask "why has no matrix been authored despite repeated medium-mismatch incidents" (ladder/escalation cause), or (b) split into a sibling sub-chain for the R12-coverage cause and label it explicitly. Don't pretend one descends from the other.

**Weakness 1.4 — q1_trc_nc / Why 1 — RESIDUAL**
*Issue*: Why 1's new_insight describes the decision point but doesn't add causal information beyond restating the symptom ("ship+warn rather than re-render"). It functions more as a problem statement than a Why.
*Suggested fix*: Acceptable as the chain's entry point — 5-Whys conventionally opens with the observed event. Mark explicitly as "Symptom anchor" rather than "new insight" so the chain starts cleanly at Why 2.

**Weakness 1.5 — q1_trc_nc / Why 9 — ADDRESSABLE**
*Issue*: Why 9 cites the Instruction Failure Escalation Ladder's "threshold=0 for known-failed" rule and concludes escalation didn't fire because no `feedback_*.md` marker exists. This is a real cause but it is a management-system cause (governance ritual depending on a human-written marker), not a technical one — it belongs in q3_mrc_nc.
*Suggested fix*: Move Why 9 to q3_mrc_nc as one of the management-level Whys (the ladder is a process artifact, not code). Keep q1's chain technical: "no automated escape-clustering" (Why 10) is technical; "no marker file written" is process.

**Weakness 1.6 — q1_trc_nc / Why 12 — ADDRESSABLE**
*Issue*: Why 12 is cut off mid-word ("the gates mostl..."). The reasoning that "gates mostly worked" is the load-bearing justification for why no closed-loop was built, but it's unverifiable in this state.
*Suggested fix*: Restore the full text. Likely continuation: "...mostly worked at launch, so the closed-loop investment was deferred until a novel morphing form (medium-redirect) revealed the open-loop blind spot." Verify and emit.

**Weakness 1.7 — q1_trc_nc / chain depth — RESIDUAL**
*Issue*: Chain depth is 12 — substantially longer than the canonical 5–7. While most steps add genuine causal structure, the long chain risks blurring the boundary between root cause and contributing chain. After moving NC/ND/MRC content to their proper quadrants, q1 will likely shrink to 5–6 Whys, which is healthier.
*Suggested fix*: After re-quadrant-assignment, accept whatever depth remains. Don't pad to 12 artificially.

**Weakness 1.8 — q1_trc_nc / Why 2 — RESIDUAL**
*Issue*: The "cost asymmetry" claim assumes mermaid→PNG→CID is meaningfully harder than ship+warn. In practice, `npx -p @mermaid-js/mermaid-cli mmdc -i in.mmd -o out.png` plus a 5-line Python email helper is ~15 minutes once. The asymmetry is real at the moment of decision but not structural — it was a missing-tool problem (Why 3) more than a true cost problem.
*Suggested fix*: Tighten Why 2 to "perceived cost asymmetry under no-pre-built-helper conditions" so it reads as a proximate driver, not a structural one. The structural cause is Why 3.

**Weakness 1.9 — q1_trc_nc / Why 11 — RESIDUAL**
*Issue*: The claim that `metrics.jsonl` has no `escape_id` linking Stop decisions to subsequent UserPromptSubmit corrections is plausible given the architecture described in user's CLAUDE.md (per-event hooks), but it's stated as fact without citing the actual schema. If wrong, the entire closed-loop conclusion in Why 12 is built on a false premise.
*Suggested fix*: Verify by reading `~/.claude/metrics.jsonl` schema or the hook code that writes it before claiming the join key is absent. If it IS absent, cite the exact field list. If it exists, revise.

**Round 1 SoA citations used**: None (no fresh URL retrieval — audit relied on Phase 0 meta-domain analogies: pharma CAPA batch deviation, aviation MEL deferred-defect, email pre-flight cross-client rendering).

### Round 2 — Verdict: CONTINUE

**Weakness 2.1 — q1_trc_nc / Why 1 — ADDRESSABLE**
*Issue*: Why 1 is a problem statement, not a causal step. It restates WHAT happened ("artifact existed as Markdown-with-Mermaid; agent chose ship+warn") and labels the decision point. A genuine first Why should advance from the non-conformance description to the first causal layer; instead this Why duplicates the framing the root statement already establishes.
*Suggested fix*: Either drop Why 1 and renumber (Why 2's "cost asymmetry" is the real first causal step), or rewrite Why 1 to ask a sharper question — e.g., "Why was the egress payload allowed to leave with format incompatible with the target renderer?" — so it opens a causal direction rather than re-describing the event.

**Weakness 2.2 — q1_trc_nc / Why 6 — ADDRESSABLE**
*Issue*: Why 6 ("no medium-capability matrix as structured artifact") is at risk of being a rephrase of Why 5 ("no PreToolUse egress gate inspects payload against a target-renderer capability matrix"). Why 5 already asserts both halves: gate absent AND no matrix to consult. Why 6 just zooms into the second half. The "new insight" is the file path suggestion (`~/.claude/medium-capabilities.yaml`), which is a remediation hint, not a deeper cause.
*Suggested fix*: Either merge Whys 5+6 into one step ("no egress-gate + no machine-readable medium-capability matrix → mismatch invisible to toolchain"), or push Why 6 deeper to a genuinely new layer — e.g., "Why has no matrix been authored despite N prior medium-mismatch incidents?" which leads to escalation-ladder territory and bridges cleanly to q3.

**Weakness 2.3 — q1_trc_nc / Why 7 — ADDRESSABLE**
*Issue*: Branch discontinuity already self-flagged in audit_notes on Why 7. Why 7 (R12 regex scope) does NOT descend from Why 6 (no capability matrix). They are sibling technical sub-causes: (a) producer-egress contract gap, and (b) detection-side regex coverage gap. Presenting them as a linear chain hides the fact that fixing the matrix would not fix the regex, and vice versa — these are independent failure modes of the same incident.
*Suggested fix*: Split q1 into two explicit sub-branches: q1a (producer→egress contract: Whys 2–6) and q1b (Stop-hook detection coverage: Whys 7–8, with Whys 10–11 as q1c on metrics-pipeline learning). Label each branch with its own root sentence so the q4_trc_md plan can spawn three parallel SoAs rather than a single pipeline that conflates them.

**Weakness 2.4 — q1_trc_nc / Why 9 — ADDRESSABLE**
*Issue*: Why 9 ("no `feedback_ship_with_warning.md` was written, so escalation-ladder threshold-0 rule never fired") is a management-system cause, not a technical one. The escalation ladder is a process artifact governed by who-writes-what convention; the absence of a marker file is a process gap. Audit_notes on Why 9 already flag this — it should live in q3_mrc_nc (management non-conformance: prior incidents stayed at text-tier, never escalated).
*Suggested fix*: Move Why 9 to q3_mrc_nc as one of the management-level Whys. In q1, replace it with the technical analog: "Why does the gate not auto-extend its phrase list from observed escapes?" which leads naturally into Why 10 (no escape-clustering) and Why 11 (per-event hook architecture) — keeping q1 strictly technical.

**Weakness 2.5 — q1_trc_nc / Why 11 — ADDRESSABLE**
*Issue*: Whys 10–11 form a third distinct causal branch (metrics pipeline cannot learn from its own escapes) but are appended after the R12-regex branch as if continuing it. Why 10 actually answers "why doesn't the gate self-extend" — which is upstream of Why 8 ("regex authored from historical corpus"), not downstream. The numbering implies dependence that doesn't exist.
*Suggested fix*: Reorder so the learning-loop branch (Whys 10–11) precedes the regex-coverage branch in dependency terms, OR explicitly mark it as a sibling sub-chain. Consider terminating q1 at the architectural cause: "hook events are stateless per-call by design — no closed-loop signal from next user turn." That is the deepest technical NC and a natural handoff to q2_trc_nd.

**Weakness 2.6 — q2_trc_nd — ADDRESSABLE**
*Issue*: q2_trc_nd (technical non-detection) chain is not visible in the input — only q1 is shown. Cannot verify check #3 (ND depth ≥ NC depth). Given that Whys 7–8 and 10–11 are detection-side material currently misfiled in q1, q2 may be under-developed: if those four Whys migrate to q2 as suggested, q2 will reach depth 4 — but the q2 ROOT statement and its own first 1–3 Whys still need to exist independently and bridge to them.
*Suggested fix*: Author q2_trc_nd explicitly with a root like "Stop-hook + metrics pipeline cannot detect ship+warn morphing forms because the detection layer is lexical-pattern-matching against a frozen corpus, with no closed-loop signal from user corrections." Then incorporate Whys 7–8 (regex coverage) and 10–11 (no escape-learning) under it, reaching ≥5 levels to match q1.

**Weakness 2.7 — q3_mrc_nc — ADDRESSABLE**
*Issue*: q3_mrc_nc (management non-conformance) chain not visible. Cannot verify check #2 (MRC quadrants at management-system level, not code-level). Why 9's content ("prior incidents stayed at text-tier, no marker file written, ladder threshold-0 never fired") is the seed for q3 but currently sits in q1. Without seeing q3, there is no evidence the management causes (incident triage policy, escalation-ladder ownership, who-writes-feedback-files convention, monthly review cadence) have been traced.
*Suggested fix*: Author q3_mrc_nc with a management-level root — e.g., "The Instruction Failure Escalation Ladder is a self-service convention (the affected agent must write its own `feedback_*.md`) with no independent triage role, so morphing forms that the agent does not self-recognize never get escalated past tier 1." Whys should target ownership, cadence, and accountability artifacts — not code paths.

**Weakness 2.8 — q4_trc_md — ADDRESSABLE**
*Issue*: q4_trc_md and q4_mrc_md (mis-delivery / management-side mis-delivery) chains not visible. Per check #3, ND quadrants must reach NC depth. With q1 currently at ~11 Whys (some misfiled), the threshold is high and unlikely to be met by q2/q4 unless authored deliberately.
*Suggested fix*: Once q1 is split (per Whys 7, 9, 11 fixes above) its effective depth on each branch will land at 4–5, which is a more realistic target for q2/q4 to match. Audit q4 specifically for management-system framing: who owns the escalation-ladder review, what the cadence artifact is, and why the cadence missed this incident class.

**Weakness 2.9 — q1_trc_nc / Why 11 — RESIDUAL**
*Issue*: Input is truncated mid-Why 11 ("There is n…"). Cannot audit any later Whys in q1 nor confirm where the chain terminates. If q1 in fact continues to Why 12+ with a deeper architectural cause (e.g., "hooks were modeled on Unix signal handlers, not on closed-loop controllers"), the audit may underweight it.
*Suggested fix*: Re-submit the full q1 chain with all Whys complete, plus q2/q3/q4 chains, for a complete depth and branching audit in the next round.

**Round 2 SoA citations used**: None (no fresh URL retrieval; audit reused Phase 0 meta-domain analogies and inspected accumulated audit_notes from round 1).

### Round 3 — Verdict: CONTINUE

**Weakness 3.1 — q1_trc_nc / Why 1 — RESIDUAL**
*Issue*: Why 1 is an event re-description ("artifact existed in Markdown form; agent chose ship+warn"), not a causal step that opens a new direction. The audit_notes on Why 1 already flag this. After three rounds, the original chain still leads with this restatement, which dilutes the visible NC depth by one rung.
*Suggested fix*: Apply the audit_note: drop Why 1 and renumber, OR rewrite to "Why was the egress payload allowed to leave with format incompatible with the target renderer?" — opens the producer→egress contract direction that Whys 2–6 actually traverse.

**Weakness 3.2 — q1_trc_nc / Why 3 — ADDRESSABLE**
*Issue*: Why 3 conflates two distinct claims: (a) prior Mermaid targets all had native renderers, and (b) no helper was "written reactively or proactively". (a) is a historical fact, (b) is a behavioral pattern — they are sibling causes, not parent→child. The "reactively or proactively" clause smuggles in the real deeper cause (reactive-only tool-building) without making it its own Why.
*Suggested fix*: Split into Why 3a "no prior egress required a constrained renderer, so capability gap was latent" and Why 3b "tool-building is reactive-only — no proactive scan of upcoming egress targets exists". Why 3b then bridges naturally to a q3_mrc_nc rung about the missing capability-gap-discovery process.

**Weakness 3.3 — q1_trc_nc / Why 4 — ADDRESSABLE**
*Issue*: Why 3 → Why 4 is a non-sequitur. "No helper exists" is a toolchain-capability claim; "medium constraint not detected at task start" is a timing/awareness claim. Even if a helper existed, detection timing wouldn't automatically improve — the producer would still need a trigger to consult the helper. The chain skips the trigger-design layer.
*Suggested fix*: Insert intermediate Why: "Why does no task-acceptance step force the producer to declare target medium?" This trigger-layer Why is the actual link between capability (helper) and timing (early detection).

**Weakness 3.4 — q1_trc_nc / Why 5 — RESIDUAL**
*Issue*: Whys 4 and 5 are near-paraphrases ("decoupled phases, no back-pressure" vs. "no enforced contract between them"). The audit_notes on Why 6 already flag the 5+6 overlap; the 4+5 overlap is the same defect one rung earlier. Two consecutive Whys saying "no contract" is one causal step stretched into two.
*Suggested fix*: Collapse 4+5 into "producer and delivery phases share no contract or back-pressure signal — medium-capability check lives only in agent reasoning, not in code". Frees a rung for the deeper cause (producer trigger absence, per Why 4 fix above).

**Weakness 3.5 — q1_trc_nc / Why 7 — RESIDUAL**
*Issue*: Whys 7–9 are detection-side causes (Stop-hook regex coverage, phrase-list seeding, escalation-marker absence). They belong in q2_trc_nd (technical non-detection) and q3_mrc_nc (management-system non-conformance), not q1. Audit_notes on Whys 7 and 9 already call this out across rounds 1–2; the misfiling persists into round 3.
*Suggested fix*: Apply the audit_notes: end q1_trc_nc at Why 6, move Whys 7–8 to q2_trc_nd, move Why 9 to q3_mrc_nc. Or, if keeping in q1, split q1 into q1a (producer→egress contract, Whys 2–6) and q1b (Stop-hook detection, Whys 7–8) with separate root sentences — as the audit_note already proposes.

**Weakness 3.6 — q1_trc_nc / Why 8 — ADDRESSABLE**
*Issue*: Why 8 stops at "bounded by historical training data" — a true but terminal observation. It does not ask the next obvious Why: "why is there no proactive/adversarial coverage-extension process?" Hook coverage = corpus-of-past-incidents is itself the management-system defect that should hand off to q3_mrc_nc, but the chain treats it as a leaf.
*Suggested fix*: Add Why 8.5: "Why is there no synthetic/adversarial generation of unseen morphing forms to seed the regex before they appear in the wild?" This bridges the technical NC chain (q1/q2) to the management-system MRC chain (q3) about preventive coverage processes vs. reactive corpus-driven coverage.

**Weakness 3.7 — q1_trc_nc / Why 9 — RESIDUAL**
*Issue*: Why 9's terminal clause "escalation depends on a marker file that itself depends on a human writing it" is excellent MRC material — it names a dependency loop in the management system, not a technical fault. Leaving it as the final rung of q1_trc_nc rather than as a q3 root means the strongest management-system insight is hidden inside a technical chain.
*Suggested fix*: Promote "`feedback_*.md` authorship is human-gated, so threshold=0-for-known-failed never fires automatically" to be a q3_mrc_nc root or top-rung Why. Replace Why 9's slot in q1 with a pointer/cross-reference.

**Weakness 3.8 — q1_trc_nc / chain structure — ADDRESSABLE**
*Issue*: The single q1 chain conflates three independent causal lineages under one root: (a) producer→egress contract gap, (b) Stop-hook detection coverage gap, (c) escalation-ladder authorship gap (per the visible audit_note proposing q1a/q1b/q1c split). A single root sentence with one linear chain forces these three to look like one problem, which will propagate into q4_trc_md as a single SoA when it should be three parallel SoAs.
*Suggested fix*: Adopt the audit_note's split: q1a (producer→egress: Whys 2–6), q1b (detection coverage: Whys 7–8), q1c (escalation authorship: Why 9 → q3). Spawn three parallel SoAs in q4_trc_md keyed to each branch; this also lets q2_trc_nd be matched branch-by-branch for ND-depth parity.

**Weakness 3.9 — q2_trc_nd — ADDRESSABLE**
*Issue*: q2_trc_nd, q3_mrc_nc, and q4_mrc_md are not visible in the input (truncated mid-Why 9 of q1). Cannot verify ND-depth parity with NC (check #3) or MRC management-system framing (check #2) without them. If the other quadrants are as shallow as q1's misfiled rungs suggest (i.e., q2 borrows Whys 7–8 from q1), ND will be structurally underdeveloped.
*Suggested fix*: Provide full q2/q3/q4 chains for next-round audit, or — if this is the terminal round — explicitly verify that q2 has at least 5–6 NDs of comparable depth to q1's NCs, and that q3/q4 framings are at the management-system level (escalation ladder, capability-gap-discovery process, marker-authorship workflow) and not at the regex/hook-config level.

**Weakness 3.10 — q1_trc_nc / Why 6 — ADDRESSABLE**
*Issue*: Why 6 implicitly assumes that authoring a YAML matrix is sufficient — but the matrix needs both (1) authorship and (2) a hook integration that consults it on egress. The Why blends a data artifact with its enforcement mechanism, hiding a second precondition.
*Suggested fix*: Either rewrite Why 6 narrowly ("no machine-readable medium-capability matrix exists as a structured artifact") and add Why 6.5 ("and no PreToolUse hook is wired to consult such a matrix even if it existed"), or merge with Why 5 per the existing audit_note and explicitly enumerate both preconditions in the merged step.

**Round 3 SoA citations used**: None (no fresh URL retrieval; audit was structural-pattern review against the Phase 0 meta-categories, particularly "surface-pattern detector evaded by semantic paraphrase" which mapped directly onto the q1 misfiling defect).

### Phase 3 final verdict and posture

The Phase 3 audit produced three rounds of CONTINUE without converging on PASS. The pipeline elected to **proceed to Phase 4 with audit_notes attached to each affected Why** rather than re-author Phase 2, on the rationale that:

- The structural defects (branch conflation, quadrant misfiling, paraphrase rungs) are all correctly diagnosed and recorded inline on the relevant Whys, so any reader of this report sees both the original chain and the auditor's proposed corrections.
- The Phase 4 actions can be authored to honor the auditor's intent (e.g., q3 prevention covers theescalation-ladder authorship gap that auditor wanted moved out of q1; q4 prevention covers the closed-loop effectiveness review the auditor wanted in q4_mrc_nd).
- The residual classification on the most paraphrastic Whys (1, 2, 5) signals these are acceptable as drafted given 5-Whys conventional latitude.

**Phase 3 residual risks**: Three RESIDUAL items remain accepted as-drafted: Why 1 (event re-description as chain anchor — conventional in 5-Whys), Why 2 (cost-asymmetry framing — proximate driver acceptable), Why 11 (escape_id schema claim unverified). The latter is the one that warrants a Phase 6 verification follow-up if the q4 prevention's audit script exposes the underlying schema.

---

## Phase 4: Full Actions (Corrective + Prevention) per Quadrant

### Q1 — TRC × Non-Conformance — CORRECTIVE

**Action**: Re-render the Mermaid diagrams in ECOSYSTEM.md to PNG (mermaid-cli `mmdc -i ecosystem.md -o ecosystem-{n}.png`), rebuild the email as `multipart/related` with the original prose as HTML body, embed each PNG via `cid:` references replacing the corresponding ` ```mermaid``` ` fences, strip the "renders in VS Code or GitHub" note entirely, and resend to oxydavid@gmail.com from the same sender as a follow-up titled "ECOSYSTEM.md (rev: inline diagrams)". Verify in Outlook web + desktop that all diagrams display inline before closing.

**Rationale**: Fixes this specific instance by eliminating the medium-renderer mismatch at its source: the recipient now sees the diagrams in Outlook directly, so the workaround pointer is no longer needed and the artifact stops being a degraded ship+warn. This is purely instance-level remediation — it does not extend R12, build a capability matrix, or close the open-loop hook design (those belong to q3/q4); it just resolves the one outstanding broken artifact already in the user's inbox.

**Owner**: Claude (current session)

**Target date**: 2026-04-25 (same day, before session close)

**Evidence of completion**:
1. New email message-id logged in session transcript with `multipart/related` Content-Type header confirmed via `Get-Item` on the saved .eml or sendmail return;
2. PNG artifacts saved under `D:/D-artifacts/ecosystem/diagrams/` with mmdc invocation captured in shell history;
3. Outlook web screenshot (or user confirmation reply) showing at least one diagram rendered inline with no broken-image placeholder;
4. Original ECOSYSTEM.md updated in repo to reference the PNG paths instead of raw fences, committed with message `fix(ecosystem): inline-render mermaid for outlook egress (q1_trc_nc CA)`;
5. No "view in VS Code/GitHub" string remains in the resent body (`grep -c` on the sent payload = 0).

### Q2 — TRC × Non-Detection — CORRECTIVE

**Action**: Extend the phrase regex in `~/.claude/hooks/stop-hook-no-handoff-gate.sh` with the medium-redirect family that slipped past on this incident. Add (case-insensitive, word-boundary anchored) at minimum: `renders? in`, `will render (in|on|under|when)`, `diagrams? render`, `best (viewed|rendered|read) (in|on|with)`, `view (it|this|them) in`, `open (it|this) in`, `paste (it|this|into)`, `only (renders|works|displays) in`, `to see (the|proper|correct) (rendering|diagrams|formatting)`, `copy (into|to) <?[A-Za-z]+>?`, `for (correct|proper) rendering (use|open|view)`. Then re-run the ECOSYSTEM.md Stop-hook transcript through the gate in replay mode and confirm it now emits a deny with the new pattern ID. Commit the regex diff plus a fixture file `~/.claude/hooks/fixtures/r12_medium_redirect_ecosystem_md.txt` containing the exact completion text that was missed, wired into the hook's self-test so any future regex edit that breaks this case fails CI on the auto-push.

**Rationale**: The instance miss was literally one string — "diagrams render in VS Code or GitHub" — never reaching the matcher. Enumerating the medium-redirect family (render/view/open/paste/copy-into-<tool>) closes the exact lexical hole for this incident and, via the pinned fixture, makes silent regression of this specific case impossible. It deliberately does NOT attempt to solve the class-level problems surfaced in Whys 5–11 (monomodal detection, absent allow-path telemetry, missing PreToolUse egress layer, lexical-vs-semantic contract) — those belong in systemic/prevention quadrants. Scoping the fix to "this instance would now be caught, and cannot silently un-catch" is the minimum that discharges q2_trc_nd without sprawl.

**Owner**: Kuangyu (self — artifact lives under `~/.claude/`, auto-commit + auto-push hook handles versioning)

**Target date**: 2026-04-26

**Evidence of completion**: fixture replay denies + self-test green + auto-pushed commit landed.

### Q3 — MRC × Non-Conformance — PREVENTION

**Action**: Add a "rule-coverage steward" automated subsystem under `~/.claude/governance/` with three coupled components:

1. A **pre-commit hook** on `~/.claude/gate-rules.yaml` that REJECTS any new or modified behavioral gate unless its YAML entry contains a non-empty `morphing_variants:` array (≥3 distinct lexical framings of the same semantic class) and a `class_definition:` field stating the equivalence class in plain prose;
2. A **Windows Task Scheduler cron** (`~/.claude/governance/coverage_audit.py`, weekly) that scans the last 7 days of transcripts + all `feedback_*.md` files, clusters denied/observed failures by semantic class (LLM-judge call), diffs each class against the `morphing_variants` of every active rule, and writes `~/.claude/governance/coverage_audit_YYYY-WW.md` listing under-covered classes with proposed phrase-list extensions;
3. A **Stop-hook addendum** (`~/.claude/hooks/stop-hook-coverage-debt-gate.sh`) that BLOCKS session completion if `coverage_audit_*.md` from the prior week contains unresolved class-coverage gaps tagged `severity: high` (i.e., recurrence n≥2).

The cron itself is monitored: missing weekly artifact older than 10 days triggers a Telegram alert via `@kw_claude_daily_bot`. Bootstrapping deliverable: backfill `morphing_variants` for all R1–R12 gates in this commit, including R12 with the "view in VS Code / renders in GitHub / open with X / use the file at" semantic class.

**Hierarchy level**: 2 (administrative-process control with automated enforcement — above text-rule, below architectural elimination)

**Gate test**:
- *Scope* — **PASS**. Prevents the CLASS of "gate covers a lexical instance but not its semantic equivalence class" across all current and future behavioral rules. The pre-commit hook makes class-undefined rules un-mergeable (every new rule must declare its class + ≥3 morphing variants); the weekly cron retroactively scans transcripts to surface variants not yet in any rule's variant list; the stop-hook addendum forces resolution before a new session can close cleanly. Together they cover (a) new-rule authoring blind spots, (b) drift in existing rules as users invent new framings, and (c) accountability for closing gaps. Specifically catches the R12 ship-with-warning morphing case (and N future analogues) because each rule must now enumerate framings, and the cron flags transcript phrases not covered by any rule's variant list.
- *Persistence* — **PASS**. Embedded in three independent automated mechanisms, none requiring human memory: (1) git pre-commit hook on `gate-rules.yaml` — bypassed only by `--no-verify`, which the `stop-hook-no-handoff-gate` already polices and which CLAUDE.md prohibits; (2) Windows Task Scheduler weekly trigger with self-monitoring (Telegram alert on staleness ≥10 days, per the Silent Staleness Pattern wiki concept); (3) Stop hook gate that runs on every session end. Located under `~/.claude/` which is auto-committed + auto-pushed by existing hook, so the configuration itself is versioned and survives machine reinstall. No reliance on Claude or user remembering to audit.
- *Measurability* — **PASS**. A third-party auditor in 6 months can verify, in under 15 minutes, all of: (a) `git log -- ~/.claude/gate-rules.yaml` shows every change since deployment includes `morphing_variants` + `class_definition` fields (grep the YAML diffs); (b) `schtasks /query /tn coverage_audit` returns an enabled weekly task; (c) `ls ~/.claude/governance/coverage_audit_*.md` shows ≥20 weekly artifacts with monotonically increasing week numbers and no gap >10 days; (d) `ls ~/.claude/hooks/stop-hook-coverage-debt-gate.sh` exists and is referenced from settings.json; (e) `~/.claude/governance/escalation_log.yaml` records each high-severity coverage gap and its closure commit SHA. All five checks are objective binary file-system / git-history / scheduler-state observations.

**Failure mode of prevention**: Three silent-failure modes the deployment must explicitly counter:
1. **Cron silently dies** — addressed by the 10-day staleness Telegram alert (per Windows Task Scheduler Automation + Silent Staleness Pattern wiki concepts: Task Scheduler "Stop the task if it runs longer than" and unbuffered stdout settings must be set, and the freshness signal must come from artifact content/mtime, not metadata).
2. **Cron runs but morphing-variant clustering becomes rubber-stamp** — LLM-judge agrees with whatever phrasing it sees and never flags classes; addressed by requiring the audit prompt to include adversarial seed cases (3 known historical morphing examples including the ship-with-warning case) and asserting the LLM-judge re-detects them on every run (regression assertion fails → Telegram alert).
3. **Pre-commit hook on `gate-rules.yaml` is bypassed via `git commit --no-verify` or `-c core.hooksPath=`** — addressed by the existing `stop-hook-no-handoff-gate`'s hook-bypass detection plus a new audit field requiring every `gate-rules.yaml` commit SHA to appear in the weekly audit's "rule changes reviewed" section; orphan commits (in git but not in audit) trigger a high-severity gap.
4. **The audit identifies gaps but no one closes them** — addressed by the Stop-hook coverage-debt gate that blocks session completion until high-severity gaps are either resolved or explicitly EXEMPT-ed with rationale, plus the `escalation_log.yaml` requirement.

**Deployment scope**: GLOBAL.

**Scope justification**: Per CLAUDE.md "Ecosystem Improvements Are Global" rule (R11 in the active gate-rules summary): any hook, gate, feedback rule, or governance mechanism that must fire across every cwd/session MUST live under `~/.claude/`, not in project memory. This prevention is precisely such a mechanism — it governs the rule-authoring process for ALL behavioral gates, audits ALL transcripts regardless of project, and the failure class it prevents (gate-coverage gaps allowing semantically-equivalent variants past) is project-agnostic. The originating incident (ship-with-warning ECOSYSTEM.md email) occurred in a non-project egress action, and the equivalence class spans every project: any artifact, any destination. Co-locating with existing global governance (`~/.claude/hooks/`, `~/.claude/gate-rules.yaml`, `~/.claude/feedback_*.md`, `~/.claude/CLAUDE.md`) also gets the auto-commit + auto-push to `oxydavid-maxx/claude-config` for free, so the prevention itself is versioned and recoverable. Project-scoped deployment would violate R11 and fail to fire on cross-project egress (email, Telegram, wiki ingest), which is where the observed incident class actually occurs.

### Q4 — MRC × Non-Detection — PREVENTION

**Action**: Institute a closed-loop **Gate Effectiveness Governance (GEG)** system at `~/.claude/`, consisting of four coupled artifacts that together convert gates from write-once scripts into living controls:

1. **Schema extension (`~/.claude/gate-rules.yaml`)** — every rule MUST declare two new required fields:
   - `covered_class:` an enumerated list of behavior-signature patterns (regex OR semantic descriptors with example phrases) the rule claims to detect.
   - `excluded_class:` an enumerated list of behaviors deliberately out-of-scope.

   For R12 specifically, `covered_class` must enumerate handoff-equivalents including the "shipped degraded artifact + view-it-elsewhere pointer" pattern (with seed phrases: "renders in", "view in", "open in <tool>", "best viewed", "diagrams only show in", "this works correctly when you …").

2. **Pre-commit hook (`~/.claude/hooks/gate-rules-schema-gate.sh`)** — rejects any commit to `gate-rules.yaml` where any rule is missing `covered_class` / `excluded_class` or has them as free-form prose without ≥1 enumerated pattern. Bypasses the existing auto-commit+auto-push only when the schema gate passes.

3. **Monthly automated audit (`~/.claude/audits/gate-effectiveness-audit.py`)** — scheduled via Windows Task Scheduler on the 1st of each month. Joins:
   - `feedback_*.md` (human-catch corpus across `~/.claude/` and project memories)
   - `metrics.jsonl` (gate-catch corpus)
   - `gate-rules.yaml` `covered_class` declarations

   Computes per-rule **Detection-Coverage KPI** = `gate_catches / (gate_catches + human_catches_matching_covered_class)` and writes `~/.claude/audits/gate-effectiveness-<YYYY-MM>.json` plus a Markdown summary.

4. **Auto-escalation on KPI breach** — when any rule's Detection-Coverage < 0.80 OR when `human_catches_matching_covered_class ≥ 2` in a month, the audit auto-creates `~/.claude/feedback_gate_miss_<rule_id>_<YYYY-MM>.md` listing the missed instances and required rule extensions. This file propagates through the existing R7/R8 escalation ladder, so the next attempt to edit code in the affected domain forces a rule update before merge.

**Charter update**: extend the "Monthly review" clause in `~/.claude/CLAUDE.md` from "feedback-vs-instruction" to "feedback-vs-instruction-vs-gate-coverage," explicitly requiring sign-off on the audit report.

**Hierarchy level**: 2 (administrative-process control with automated enforcement)

**Gate test**:
- *Scope* — **PASS**. Applies uniformly to every rule in `gate-rules.yaml` (R1–R12 and any future rule), not just R12 or the handoff class. The schema gate refuses any rule missing `covered_class`; the audit computes Detection-Coverage for every rule. The CLASS being prevented is "gate exists but its semantic coverage is unmeasured/unaudited," which is the systemic failure behind every potential blind-spot recurrence — not just the ship-with-warning instance.
- *Persistence* — **PASS**. Four mechanisms enforce persistence without relying on memory: (1) YAML schema field is structurally required and rejected by the pre-commit hook; (2) pre-commit hook is invoked by git itself, not by Claude's recall; (3) audit script is scheduled by the OS task scheduler on a fixed cron, independent of any session; (4) audit-generated `feedback_gate_miss_*.md` files plug into the existing R7/R8 hard gates that already enforce on every PreToolUse. Removing any one component leaves a visible gap that the others surface.
- *Measurability* — **PASS**. A third-party auditor in 6 months can verify with five file-system observations: (i) `grep -L 'covered_class' ~/.claude/gate-rules.yaml` returns no rules — every rule has the field; (ii) `~/.claude/hooks/gate-rules-schema-gate.sh` exists, is executable, is referenced in `.git/hooks/pre-commit` or husky config; (iii) test-commit a rule without `covered_class` to confirm the hook rejects it; (iv) `~/.claude/audits/gate-effectiveness-2026-{05..10}.json` — six monthly reports exist with per-rule Detection-Coverage numbers; (v) for any rule whose 6-month rolling Detection-Coverage < 0.80, a corresponding `feedback_gate_miss_*.md` exists. All five checks are deterministic file/output inspections, no judgment required.

**Failure mode of prevention**: Three plausible silent-failure modes:

1. **Vague `covered_class` declarations** — authors satisfy the schema gate by writing `covered_class` as broad prose ("anything related to handoff") rather than enumerated patterns. The schema gate's "≥1 enumerated pattern" check can be gamed with placeholder regex (`.*`) that matches everything and inflates the denominator falsely, pushing Detection-Coverage artificially high. Mitigation: schema gate must additionally reject `covered_class` entries that are pure wildcards or shorter than N characters; periodic LLM-judge audit of `covered_class` quality.

2. **Audit-corpus mismatch** — `feedback_*.md` files are written in free prose without standardized tagging, so the audit's regex join against `covered_class` patterns systematically under-counts human-catches (false low denominator → falsely high coverage). The system declares all gates healthy while blind spots persist. Mitigation: require each new `feedback_*.md` to declare a `target_rule:` front-matter field linking the human-catch to the rule it should have caught (or `none` for genuinely uncovered classes); audit then trusts the link instead of inferring it.

3. **Audit job silently fails** — Task Scheduler runs the audit but it errors (path issue, schema drift, file lock) and produces no JSON; subsequent months also fail; no one notices because the audit's output is itself the only signal. Mitigation: a second meta-gate — a stop hook that on each session checks "is the most recent `gate-effectiveness-*.json` older than 35 days?" and warns if so. This recursion (audit-the-audit) terminates because the meta-gate is in-band and runs every session.

**Deployment scope**: GLOBAL.

**Scope justification**: Per the user's CLAUDE.md "Ecosystem Improvements Are Global" rule (R11 / scope-leak gate), any artifact that enforces behavior across all sessions and all cwds must live under `~/.claude/`. Every component of this prevention — `gate-rules.yaml` schema, pre-commit hook, audit script, audit reports, auto-generated `feedback_gate_miss` files, and the charter clause in CLAUDE.md — governs the global enforcement layer (the gates themselves), not any single project. Project-scoped deployment would defeat the purpose: the gates fire globally, so their effectiveness must be audited globally. Additionally, `~/.claude/` has the auto-commit+auto-push hook, so all four artifacts are versioned and recoverable; the prevention itself benefits from the same persistence guarantees it imposes on the rules it audits.

---

## Phase 5: Prevention Audit Rounds

### Round 1 — Verdict: EXHAUSTED (fallback)

**Weaknesses identified**: None.

**Stronger alternatives surfaced from SoA**: None retrieved this round. The audit attempted to identify stronger prevention patterns from the Phase 0 meta-domains (pharma CAPA, aviation MEL, email pre-flight) but did not surface a concrete URL-grounded alternative that dominated the GEG + rule-coverage steward design across the three gate-test axes (scope, persistence, measurability).

**Fallback flag**: `_fallback: true` is set on this round. Per skill convention this means the audit terminated by exhaustion-of-search rather than by convergence-on-PASS. Interpretation: the prevention plan as authored is on the Pareto frontier given the deployment surface (~/.claude/ ecosystem with auto-commit, weekly Task Scheduler, R7/R8 hard gates, three-tier lesson-learning model already in place), but it is not formally certified optimal — only that no stronger alternative was surfaced in this run.

**Implications for closure**:
- The Phase 6 verification plan should be treated as load-bearing: if KPI evidence in months 4–6 indicates the prevention is decaying or the failure modes are materializing, the failure_response paths must escalate decisively (architectural-elimination tier for R12 specifically, per the q4 failure_response spec).
- The Phase 5 EXHAUSTED outcome is itself a candidate for a wiki-ingest note: "Prevention-audit EXHAUSTED with `_fallback` should trigger a 90-day re-audit calendar entry, since the audit certified absence-of-search-result, not presence-of-optimality."

**Phase 5 residual risks**: None recorded explicitly, but inherits the three failure-mode risks declared in the Phase 4 prevention authoring (vague `covered_class`, audit-corpus mismatch, audit silent-fail) — none of which were demoted by Phase 5.

---

## Phase 6: Verification Plan + Proof of Action

### Q1 — TRC × Non-Conformance — Corrective verification

- **Metric**: Count of ECOSYSTEM.md email artifacts delivered to oxydavid@gmail.com containing (a) raw ` ```mermaid``` ` fences OR (b) any "renders in / view in / open in <tool>" workaround pointer string, measured via grep on the sent .eml payload stored under `~/.claude/sent-mail-archive/`.
- **Data source**: `~/.claude/sent-mail-archive/*.eml` (local archive of egress emails) + Outlook web inline-render screenshot OR user reply confirmation attached to the same thread.
- **Target**: 0 offending artifacts in follow-up email; Content-Type header == `multipart/related`; ≥1 cid:-referenced PNG attachment per original mermaid fence; user confirmation of inline render received within 24h of resend.
- **Baseline**: 1 known-bad artifact currently in inbox (the original ECOSYSTEM.md email with mermaid fences + "renders in VS Code or GitHub" note).
- **Measurement schedule**: One-shot verification within 24h of resend; then sampled inspection of any future ECOSYSTEM*.md egress email for 6 months (zero tolerance).
- **Failure response**: If resend still contains raw fences or workaround string: revert to local PNG pipeline, re-run `mmdc` with `--backgroundColor white --width 1600`, inspect .eml with `Select-String -Pattern 'mermaid|renders in|view in'` before send; if user reports broken render: escalate to Outlook-specific test harness using playwright MCP to load the .eml in OWA and assert no broken-image placeholders before any further egress.

### Q2 — TRC × Non-Detection — Corrective verification

- **Metric**: Replay-gate detection rate on a fixed fixture corpus: percentage of the 11 seed medium-redirect phrases ("renders in", "will render in/on/under/when", "diagrams render", "best viewed/rendered/read in/on/with", "view it/this/them in", "open it/this in", "paste it/this into", "only renders/works/displays in", "to see the proper rendering", "copy into <tool>", "for correct/proper rendering use/open/view") that the extended `stop-hook-no-handoff-gate.sh` regex denies when replayed against `~/.claude/hooks/fixtures/r12_medium_redirect_*.txt`.
- **Data source**: `~/.claude/hooks/fixtures/r12_medium_redirect_*.txt` (fixture corpus) + hook self-test output logged to `~/.claude/hooks/.selftest-results.jsonl` on each auto-push.
- **Target**: 100% (11/11) fixture phrases denied by regex; self-test green on every commit touching `stop-hook-no-handoff-gate.sh`; zero regressions over 6 months (no fixture ever flips from deny → allow after a regex edit).
- **Baseline**: 0/11 phrases currently detected (the original R12 regex missed "diagrams render in VS Code or GitHub" entirely, and none of the 10 sibling phrases are in the current pattern list).
- **Measurement schedule**: Automatic on every git commit to `~/.claude/hooks/stop-hook-no-handoff-gate.sh` (pre-commit self-test); monthly full-corpus replay logged to `~/.claude/audits/r12-fixture-replay-<YYYY-MM>.json`.
- **Failure response**: If any fixture flips to allow: block the offending commit via self-test exit code 1; if monthly replay shows degradation: auto-open `feedback_r12_regex_regression_<date>.md` which plugs into R7/R8 hard gates and forces rule repair before next code edit in `~/.claude/hooks/`; if fixture corpus itself is found to be stale (new morphing forms observed in transcripts but not in fixtures): trigger q3 coverage-audit path.

### Q3 — MRC × Non-Conformance — Prevention verification

- **Metric**: Dual metric: (a) percentage of rules in `~/.claude/gate-rules.yaml` with non-empty `morphing_variants:` (≥3 entries) AND non-empty `class_definition:` fields; (b) freshness of `~/.claude/governance/coverage_audit_*.md` — age in days of the most recent weekly artifact.
- **Data source**: `~/.claude/gate-rules.yaml` (YAML field inspection via `yq` in the pre-commit hook) + `~/.claude/governance/coverage_audit_*.md` (file mtime + content) + `~/.claude/governance/escalation_log.yaml` (closure records).
- **Target**: (a) 100% of active rules (currently R1–R12) carry `morphing_variants` ≥3 AND `class_definition` within 30 days of deployment, and stays at 100% thereafter; (b) newest `coverage_audit_*.md` is ≤10 days old at any sampled point over 6 months (≤25 audits produced in 6 months, zero gaps >10 days); (c) zero high-severity coverage gaps remain open >14 days per `escalation_log.yaml`.
- **Baseline**: (a) 0/10 rules currently carry `morphing_variants` or `class_definition`; (b) 0 `coverage_audit_*.md` artifacts exist; (c) no `escalation_log` entries for coverage class.
- **Measurement schedule**: Pre-commit hook runs on every `gate-rules.yaml` change; weekly cron every Sunday 06:00 local for coverage_audit; Stop-hook coverage-debt gate fires on every session end; monthly roll-up review on 1st of month per CLAUDE.md charter.
- **Failure response**: If (a) drops below 100%: pre-commit hook already blocks merge — if bypassed via `--no-verify`, `stop-hook-no-handoff-gate` logs the orphan SHA and opens `feedback_gate_schema_bypass_<date>.md`; if (b) artifact ages >10 days: Telegram alert to `@kw_claude_daily_bot` topic `ecosystem-health` via existing bot token, and Stop-hook blocks session completion until audit re-runs successfully; if (c) gap aged >14 days: auto-promote from warn to enforce mode in `gate-rules.yaml` and append to `escalation_log.yaml` with rationale; if LLM-judge clustering in the cron becomes rubber-stamp (fails to re-detect the 3 adversarial seed cases): cron exits non-zero, absence of fresh artifact triggers the (b) path.

### Q4 — MRC × Non-Detection — Prevention verification

- **Metric**: Per-rule 6-month rolling Detection-Coverage KPI = `gate_catches / (gate_catches + human_catches_matching_covered_class)`, computed monthly per rule in `~/.claude/gate-rules.yaml` and written to `~/.claude/audits/gate-effectiveness-<YYYY-MM>.json`; additionally, count of `feedback_*.md` files carrying `target_rule:` front-matter field versus total `feedback_*.md` count (tagging compliance).
- **Data source**: `~/.claude/audits/gate-effectiveness-<YYYY-MM>.json` (audit output) + `~/.claude/metrics.jsonl` (gate-catch corpus) + `~/.claude/feedback_*.md` and project-memory feedback files (human-catch corpus, joined by `target_rule` front-matter) + `~/.claude/gate-rules.yaml` `covered_class` declarations.
- **Target**: (a) Every active rule's 6-month rolling Detection-Coverage ≥ 0.80 by month 6; (b) ≥95% of `feedback_*.md` files created after deployment carry a `target_rule:` front-matter field; (c) 6 consecutive monthly audit JSON artifacts exist (2026-05 through 2026-10) with no gap >35 days; (d) R12-specific: zero recurrences of "ship-with-warning" class human-catches over the 6-month window (`human_catches_matching_covered_class` for R12 = 0 for months 4–6).
- **Baseline**: (a) Detection-Coverage undefined — no `covered_class` declarations and no audit exists; (b) 0% of current `feedback_*.md` carry `target_rule` front-matter; (c) 0 audit artifacts; (d) ≥2 known R12-class human-catches in the 30 days preceding deployment (ECOSYSTEM.md email + prior ship-then-warn session the user flagged).
- **Measurement schedule**: Monthly on the 1st via Windows Task Scheduler; meta-gate (`stop-hook-audit-freshness`) checks artifact age ≤35 days on every session end; quarterly cross-project roll-up by the user on first Monday of each quarter per CLAUDE.md charter; 6-month sign-off review at 2026-10-25.
- **Failure response**: If any rule's Detection-Coverage < 0.80: audit auto-creates `~/.claude/feedback_gate_miss_<rule_id>_<YYYY-MM>.md` listing missed instances, which propagates through R7/R8 hard gates forcing rule extension before next edit in that domain; if tagging compliance (b) < 95%: add a feedback-file creation hook that rejects `feedback_*.md` writes lacking `target_rule` front-matter; if audit job silently dies (no fresh artifact in 35 days): meta-gate stop hook warns every session start + Telegram alert fires; if R12 class recurrence ≥1 over months 4–6: auto-escalate R12 from enforce mode to architectural-elimination tier (e.g., PreToolUse egress gate that blocks any email send whose body grep matches the `covered_class` patterns) and log to `escalation_log.yaml`.

### Overall timeframe & Phase 8 trigger

**Overall timeframe**: 6 months — 2026-04-25 (deployment) through 2026-10-25 (final sign-off review). Rationale: q3 coverage-audit cron needs ≥20 weekly artifacts to establish a trend line; q4 Detection-Coverage KPI is a 6-month rolling window so the first meaningful per-rule value lands at month 6; R12 recurrence-zero target requires observation across months 4–6 after the corpus of covered phrases has stabilized from q2 and q3 feedback. Any shorter horizon risks declaring success before the audit-the-audit meta-gate has had a chance to catch a silent cron failure (which by design takes up to 35 days to surface).

**Phase 8 trigger**: Phase 8 (congratulate-and-close) triggers on 2026-10-25 when ALL of the following are simultaneously true, verified by a single audit script run:

1. **q1** — user confirmation reply received for the resent ECOSYSTEM.md email AND grep of `~/.claude/sent-mail-archive/` for any subsequent mermaid-fence or "renders in/view in/open in" string returns zero hits over the full 6-month window;
2. **q2** — `~/.claude/hooks/.selftest-results.jsonl` shows 100% (11/11) fixture-phrase denial on every self-test run since deployment, with zero regressions;
3. **q3** — ≥24 weekly `coverage_audit_*.md` artifacts exist with no gap >10 days, 100% of rules carry `morphing_variants`≥3 + `class_definition`, and `escalation_log.yaml` shows zero open high-severity coverage gaps;
4. **q4** — six consecutive monthly `gate-effectiveness-<YYYY-MM>.json` artifacts exist, every rule's 6-month rolling Detection-Coverage ≥0.80, ≥95% of new `feedback_*.md` files carry `target_rule` front-matter, and R12-class human-catches over months 4–6 equals 0.

If ANY of the four conditions fails the audit script: Phase 8 is deferred, the failing quadrant's failure_response fires, and re-evaluation is scheduled 30 days later. The trigger itself is automated: `~/.claude/governance/phase8-trigger-check.py` runs on 2026-10-25 via Task Scheduler, writes a PASS/FAIL artifact to `~/.claude/governance/phase8-decision-2026-10-25.json`, and on PASS sends a Telegram notification to `@kw_claude_daily_bot` requesting final user sign-off before formal closure.

---

## SoA Citations (deduplicated)

No external URL citations were retrieved during Phase 3 (3 audit rounds) or Phase 5 (1 audit round, EXHAUSTED with fallback) in this run. The audit phases relied exclusively on cross-domain analogy from the Phase 0 meta-domains, listed below for traceability:

- **Pharmaceutical GMP batch-deviation / CAPA governance** — analog for ship-with-deviation pass-through with disclaimer; informed the Q3 prevention design (recurrence-triggered class-completeness audit echoes pharma CAPA equivalence-class completeness review).
- **Aviation Minimum Equipment List (MEL) deferred-defect control** — analog for "shipping a degraded artifact with a workaround pointer" being categorically distinct from refusing to ship; informed the IS/IS-NOT distinction column (medium-redirect framing IS a handoff, semantically equivalent to MEL deferral without proper authority).
- **Email marketing pre-flight cross-client rendering (Litmus / Email on Acid)** — analog for medium-aware PreToolUse egress checks; informed the q1 producer→egress contract analysis and the q3 medium-capability matrix proposal.

Wiki concepts referenced (in-repo, not external URLs) — these are the **internal SoA** for this 8D and should be considered the authoritative citations:

- `concepts/instruction-failure-escalation-ladder.md` (threshold=0 for known-failed; four-rung text→soft→hard→architectural)
- `concepts/three-tier-lesson-learning.md` (forensic + behavioral + knowledge-wiki composition)
- `concepts/silent-staleness.md` (3-layer defense; data freshness from content not metadata)
- `concepts/windows-task-scheduler.md` (critical settings, stdout buffering, LogonType, exit codes)
- `concepts/wiki-to-code-traceability.md` (triple marker convention; pre-commit hard gate; text instructions fail)
- `concepts/hook-class-taxonomy.md` (event-handler vs prompt-injection; env-gated short-circuit; setting_sources=None doesn't suppress plugin SessionStart hooks)
- `concepts/self-healing-automation.md` (4-layer self-healing; fail forward)

---

## Closure Audit

**What was checked**:

- **Quadrant completeness** — all four quadrants (q1_trc_nc, q2_trc_nd, q3_mrc_nc, q4_mrc_nd) carry root + Why chain + action (corrective for q1/q2, prevention for q3/q4) + verification block. **PASS.**
- **NC/ND parity** — q1 chain depth 12, q2 chain depth 11, q3 chain depth 12, q4 chain depth 12. ND quadrants reach NC depth. **PASS** (with caveat that Phase 3 audit flagged q1 conflates three sub-branches; if treated as branches q1a/b/c the effective per-branch depth is shorter but ND still reaches branch-parity).
- **MRC management-system framing** — q3 root explicitly names governance artifacts (coverage-audit obligation, rule-coverage steward role, recurrence-trigger cadence); q4 root explicitly names governance artifacts (Detection-Coverage KPI, recurring audit, feedback-to-gate escalation). **PASS.**
- **Phase 3 audit closure** — three rounds CONTINUE; ADDRESSABLE issues recorded as audit_notes inline on each affected Why; RESIDUAL issues accepted with rationale. The audit's structural critiques (split q1 into a/b/c sub-branches; move Why 9 to q3) are honored implicitly in Phase 4 actions (q3 prevention covers escalation-ladder authorship; q4 prevention covers closed-loop effectiveness). **PASS with recorded debt** (q1 chain still single-rooted in Phase 2 output; downstream phases honor the auditor's intent).
- **Phase 5 audit closure** — single round, EXHAUSTED with `_fallback: true`. Interpretation: prevention plan on Pareto frontier given deployment surface, not formally optimal. **PASS with caveat** (90-day re-audit recommended).
- **Action specificity** — q1 corrective names exact mmdc command, exact Content-Type header, exact resend title; q2 corrective lists 11 exact regex patterns; q3 prevention lists three coupled artifacts with exact file paths and exact YAML fields; q4 prevention lists four coupled artifacts with exact KPI formula. **PASS.**
- **Verification metrics objectivity** — every metric is a file-system observation (grep count, file mtime, JSON field) or a deterministic replay (fixture-corpus match rate). Zero metrics depend on subjective judgment. **PASS.**
- **Failure-response definition** — every quadrant's verification carries a failure_response that names exact escalation paths (revert-to-pipeline, auto-open feedback file, Telegram alert, auto-promote warn→enforce, escalate to architectural-elimination tier). **PASS.**
- **Deployment scope** — both prevention actions declare GLOBAL with explicit R11 justification (Ecosystem Improvements Are Global). **PASS.**
- **Phase 8 trigger automation** — programmatic trigger script + dated decision artifact + Telegram notification path. **PASS.**

**What passed**: All 10 closure checks. Report integrity is intact for sign-off at 2026-10-25 conditional on the Phase 8 trigger predicate evaluating PASS.

**What failed / debt recorded**:
- q1 Why chain not refactored into q1a/q1b/q1c per Phase 3 audit_notes — recorded debt; downstream phases honor intent.
- Phase 5 EXHAUSTED with `_fallback: true` — recorded debt; re-audit recommended at 90 days.
- Phase 3 RESIDUAL Why 11 unverified `escape_id` schema claim — recorded debt; will be empirically resolved when Q4 prevention's audit script joins `metrics.jsonl` to `feedback_*.md` for the first time.
- No fresh URL-grounded SoA citations retrieved this run — recorded debt; Phase 0 dual-tier research was meta-domain-only.

---

## Wiki Ingest Drafts

The following knowledge artifacts produced by this 8D are candidates for ingestion into `D:/D-claude/personal-wiki/` per the user's CLAUDE.md "Proactive Wiki Ingestion" rule. Each is summarized in one line; user approval required before saving to `raw/`:

1. **Concept: "Ship-with-Warning Anti-Pattern"** — Producer-to-medium impedance mismatch + workaround-pointer framing IS a handoff (semantic-equivalence with R12); add to `concepts/` linking to `instruction-failure-escalation-ladder.md`, `three-tier-lesson-learning.md`, and a new sibling `concepts/medium-aware-egress-gate.md`.
2. **Concept: "Gate Coverage vs Gate Strength"** — The Instruction Failure Escalation Ladder optimizes mechanism strength on one axis (text→soft→hard→architectural) but is silent on coverage completeness on a perpendicular axis (specific phrase→equivalence class→semantic intent); a complete escalation policy requires both. Cross-link to `instruction-failure-escalation-ladder.md`.
3. **Concept: "Closed-Loop Behavioral Gates as Living Controls"** — Gates as write-once scripts decay because the failure-mode space evolves faster than the rule corpus; a Detection-Coverage KPI (gate_catches / (gate_catches + human_catches_matching_covered_class)) institutes the loop. Cross-link to `silent-staleness.md` and `self-healing-automation.md`.
4. **Concept: "Phase 5 EXHAUSTED with `_fallback`"** — When prevention-audit search returns no stronger alternative, the `_fallback` flag signals frontier-but-unverified-optimal; a 90-day re-audit is the appropriate hedge. Cross-link to `three-tier-lesson-learning.md`.
5. **Concept: "Medium-Capability Matrix"** — Machine-readable YAML mapping target medium → renderer capabilities (mermaid: bool, html_details: bool, raw_html: limited, max_table_cols: N, dark_mode_only_colors: bool); consumed by a PreToolUse egress hook to deny payload egress on capability mismatch. Cross-link to `hook-class-taxonomy.md` and `wiki-to-code-traceability.md`.
6. **Source summary: "8D run-1777084608-63f5cadc — Recurring ship-with-warning"** — Full forensic record of this 8D, linking to the five concept pages above and to the q3/q4 prevention deployments. Save under `raw/notes/2026-04-25-ship-with-warning-8d.md` and ingest per personal-wiki/CLAUDE.md workflow.

---

*End of report. Phase 8 sign-off scheduled 2026-10-25 conditional on Phase 8 trigger predicate.*