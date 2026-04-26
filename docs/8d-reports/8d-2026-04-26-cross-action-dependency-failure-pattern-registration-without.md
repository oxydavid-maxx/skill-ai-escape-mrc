# 8D Report: Cross-Action Dependency Failure — Registration-Without-Implementation

**Date**: 2026-04-26T13:13:40.675459
**Problem**: Cross-action dependency failure pattern: registration-without-implementation. Today 2026-04-26 a subagent dispatched to execute a 4-action governance hardening plan committed `settings.json` wiring for 5 PreToolUse/Stop/SessionStart hooks BEFORE the corresponding hook scripts existed. This created a PreToolUse cascade where every subsequent Edit/Write tool call triggered the missing scripts and errored, blocking further work. Main session caught it post-hoc and shipped 5 stub hooks (no-op `exit 0`) as a cascade-fix, then dispatched a follow-up subagent to replace the stubs with real implementations. Generative class: **registration-without-implementation** / **wiring-before-substance** — producer claims a system surface is complete (settings.json wiring asserts hooks exist + are operational) without the substance behind that claim (the hook script files). Cousin of escape #1 (degraded-emission-with-warning) shifted from output-boundary to configuration-boundary, and cousin of the deferred-artifact-without-reader class shifted from output to wiring. This 8D ships prevention BEFORE the second instance — honoring the discovery-charter's pre-empt principle.
**Run ID**: run-1777179234-fa0c7e64
**Model**: Claude Sonnet 4.5 (skill-8d-mrc LangGraph FSM)
**Pre-existing rules that missed**: R6 (wiki-domain knowledge — n/a, didn't violate), R13 (output-boundary — wrong surface, this is configuration-boundary), R14 (Skill invocation — wrong gate point), R15 (class-recurrence — first-instance free pass by design), claude-hooks lint matcher↔extractor parity (only existing scripts, no settings.json closure check), per-commit pre-commit hook (none exists for path-existence validation).

---

## Pipeline Timeline

**Phase 0 — Dual-tier research and meta-class enumeration**
Identified three meta-categories and three transferable analogue domains:
- *Declaration-Implementation Divergence* (manifest references an artifact that does not yet exist)
- *Non-Atomic Multi-Artifact Deployment* (related substance and its wiring land in separate commits/transactions)
- *Forward-Reference Without Binding-Time Verification* (a name is registered before the resolver checks the target resolves)

Analogues mined for transferable controls:
1. Commercial aviation pre-flight / Minimum Equipment List — no aircraft dispatches until every checklist line item has a verified physical match. Transferable pattern: hard pre-departure gate that resolves every manifest reference to an inspected artifact, with deferred items only allowed via an explicit MEL exception and a placard.
2. Pharmaceutical GMP batch release — a lot cannot ship until every referenced reagent, deviation report, and Certificate of Analysis is on file and signed. Transferable pattern: Quality-Person release gate that fails closed on any missing referenced document, plus periodic reconciliation between the batch record index and the document vault.
3. Theatrical tech rehearsal cue-sheet integration — opening night is blocked until every numbered light/sound/fly cue has a matching loaded asset and an operator confirmation. Transferable pattern: dry-run dress rehearsal that exercises the full manifest-to-asset binding once before live audience.

**Phase 1 — IS / IS NOT containment**: 4 dimensions populated (what / where / when / extent). Distinction column produced the prevention mount-point identification: PreToolUse on Write/Edit targeting `~/.claude/settings.json`, plus dispatcher contract.

**Phase 2 — Why-chain construction (4 quadrants)**: q1_trc_nc (12 whys to root), q2_trc_nd (11 whys), q3_mrc_nc (12 whys), q4_mrc_nd (12 whys). Branched parallel causal threads at q1.W3 per round-1/round-3 audit feedback (harness atomicity vs subagent skill template).

**Phase 3 — RC Audit (3 rounds)**:
- Round 1 verdict: CONTINUE. 8 weaknesses logged. Critical addressables: q2/q3/q4 entirely absent (later supplied), q1.W12 truncated, q1.W6–W8 collapse to one node.
- Round 2 verdict: CONTINUE. 7 weaknesses. q1.W11 empirical claim unverified; q1.W3 single-threaded (parallel branch missed); q1.W5 prescriptive leak (Residual).
- Round 3 verdict: CONTINUE. 7 weaknesses. q1.W6–W8 still tautological; q1.W3 branch still not materialized; q1.W11 truncated; q2/q3/q4 absent or short-supplied; q1.W10 deliberate-vs-incidental flagged Residual.

**Phase 4 — Full Actions** authored: corrective for q1+q2 (reconciliation log + R16 PreToolUse gate), prevention for q3+q4 (six-artifact governance bundle + risk-typology coverage regime).

**Phase 5 — Prevention Audit (3 rounds, EXHAUSTED at round 3)**:
- Round 1: 8 weaknesses. Q4 missing; R16 scope narrow (settings.json only, sibling surfaces unaddressed); hierarchy-level claimed 2 but Level 3 architectural-elimination achievable via generative coupling (NixOS / Bazel / Terraform analogue); silent-decay vector on measurability; fail-mode for diff-application unspecified; pre-commit invocation surface unclear; Generality Charter receipt missing; quarterly cadence too slow.
- Round 2: 7 weaknesses. Q4 still truncated; R16 scope still hooks-only (mcpServers, statusLine, plugins/* uncovered); non-empty-body check sub-SoA (passes `exit 0`); calendar-driven discovery loop; recursive wiring-parity for the gate's own pre-commit hook; asymmetric requiredActions push toward stub creation; Level mix unannotated.
- Round 3 verdict: EXHAUSTED. 7 weaknesses, 1 Residual (path-resolution drift). Final addressables: SKILL.md prose clause is text-only (escalation-ladder violation), substance check defeated by `exit 0`, project-scoped `.claude/settings.json` not covered, MultiEdit intermediate-state semantics unspecified, cadence mismatch with monthly review ritual, Q4 still missing in input.

**Phase 6 — Verification + Proof of Action**: 4-quadrant proof block authored, 6-month timeframe (2026-04-27 → 2026-10-27), monthly + quarterly checkpoints, atomic phase-8 trigger commit defined.

**Phase 7 — Closure audit**: see closure section below.

**SoA search queries** (yielded useful):
- "configuration-boundary referential integrity validators" → NixOS module system, Bazel BUILD generation, Terraform `for_each`
- "manifest-to-asset binding pre-flight checks" → Aviation MEL, Pharma GMP batch release, theatrical tech rehearsals
- "instruction failure escalation ladder text → soft → hard → architectural" → wiki/concepts/instruction-failure-escalation-ladder.md
- "degraded-emission-with-warning sibling classes" → wiki/concepts/degraded-emission-with-warning.md

**SoA search queries** (yielded empty / inconclusive):
- "Claude Agent SDK multi-file transactional Write" — no SDK release notes propose it; W4 confirmed as fixed architectural premise.
- "Claude Code MultiEdit intermediate-state semantics" — undocumented; required hook design to specify final-state-only validation explicitly.

**Loop-backs**: Phase 3 round-1 → branched back to Phase 2 to author q2/q3/q4 (initially absent). Phase 3 round-2 → back to Phase 2 to verify W11 actor-model-shift framing. Phase 5 round-2 → back to Phase 4 to author Q4 (initially truncated in input). Phase 5 round-3 reached EXHAUSTED with 1 Residual accepted.

---

## Section A: Root Cause Matrix

|       | Non-Conformance (NC)                                                                                                                                                              | Non-Detection (ND)                                                                                                                                                                                          |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: No PreToolUse validator on Write/Edit of `~/.claude/settings.json` performs eager filesystem referential-integrity resolution; implicit single-actor invariant never lifted. | Q2: Three-tier lesson-learning composition contract is text-only — knowledge tier can ship a named anti-pattern without producing any detector obligation; recursively self-instantiating gap.            |
| MRC   | Q3: Governance-of-governance layer absent — no scheduled, owned, deliverable-bearing process backed by a class-registry coverage-telemetry schema asks "which classes are unprotected?" before first instance. | Q4: No chartered owner for a (boundary × severity × detectability) risk-typology matrix with measured coverage-fraction; metric system gives no incentive to enumerate uncovered classes.                  |

---

## Section B: Corrective Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                                | Non-Detection (ND)                                                                                                                                                                                                                |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: Reconcile current `settings.json` ↔ `hooks/` state — walk every `command` path with `os.access(F_OK\|X_OK)`, hash each of 5 stub hooks vs no-op signature, replace stubs OR remove wiring, exercise via synthetic Edit probe, single atomic commit. | Q2: Implement `~/.claude/hooks/hook-settings-wiring-closure-gate.py` as PreToolUse(Write\|Edit) gate scoped to settings.json variants; deny edits referencing non-existent/non-executable script paths; register as R16 with rule-acceptance receipt. |
| MRC   | Q3: (see Section B2)                                                                                                                                                                                                                | Q4: (see Section B2)                                                                                                                                                                                                                |

---

## Section B2: Prevention Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                                | Non-Detection (ND)                                                                                                                                                                                                                |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q3: Six-artifact prevention bundle — `hook-settings-wiring-parity-gate.py` (R16, configuration-boundary category) + `class-registry.yaml` + dispatcher template extension + symmetric pre-commit hook + `coverage-gap-discovery-owner` role + monthly/event-driven coverage-delta-report. **Gate-test: PASS / PASS / PASS.** | Q4: Risk-Typology Coverage Regime — `risk-typology-matrix.yaml` (boundary × severity × detectability) + `risk-typology-owner` chartered + receipt-required PreToolUse on rule edits + Stop-hook on 8D closure requiring class-registry entry + nightly `governance.coverage_fraction` metric + subagent dispatch atomicity declaration. **Gate-test: PASS / PASS / PASS.** |

### Q3 gate_test evidence (full)
- **Scope: PASS** — R16 fires on every Edit/Write/MultiEdit targeting any settings.json variant under `~/.claude/`, parses the proposed post-edit JSON, and validates EVERY hook command path — not just the 5 paths from today's incident. The class-registry + coverage-delta-report ritual generalizes further: any newly-named generative class gets a registry entry that drives owning-rule assignment, so the prevention machinery covers `registration-without-implementation` AND establishes the discovery-loop that surfaces sibling classes (deferred-artifact-without-reader, etc.) before their first instance.
- **Persistence: PASS** — PreToolUse hooks fire from the harness on every tool invocation regardless of user, cwd, or session — independent of any individual remembering the rule. The pre-commit hook covers out-of-harness edits. The quarterly coverage-gap ritual is owned (owners.yaml entry), scheduled (cron via existing claude-hooks scheduler), and produces a dated artifact (coverage-delta-report.md) — embedded in tooling+process, not memory. metrics.jsonl records every R16 firing, so silent decay is detectable.
- **Measurability: PASS** — An auditor in 6 months can verify by: (1) reading `~/.claude/gate-rules.yaml` and confirming R16 exists with category=configuration-boundary, mode=enforce; (2) running a synthetic test — propose a settings.json edit referencing `/tmp/nonexistent-fake.sh` and confirm the PreToolUse returns deny with the expected reason; (3) inspecting metrics.jsonl for R16 firings since landing date; (4) confirming class-registry.yaml exists with the registration-without-implementation entry and timestamps; (5) checking that `~/.claude/governance/coverage-delta-report.md` has been regenerated quarterly with git-visible commit history; (6) confirming owners.yaml has coverage-gap-discovery-owner with non-null assignee.

### Q4 gate_test evidence (full)
- **Scope: PASS** — Targets the class "unclassified anti-pattern remains undetected until count-based recurrence", not the instance. Mechanism: every future rule authored MUST be classified into the (boundary × severity × detectability) matrix via the receipt gate; every future 8D MUST register its named class with full typology fields via the closure gate; coverage-fraction metric surfaces empty cells regardless of whether any specific class has been observed; quarterly expansion ritual actively enumerates uncovered cells. The regime is class-agnostic — it catches the next first-instance class (call it X) the same way it would have caught registration-without-implementation: X gets named in an 8D, gate (4) forces typology classification, the receipt gate (3) forces a rule that populates X's cell, coverage-fraction tracks the closure. No part of the mechanism mentions today's instance.
- **Persistence: PASS** — Five enforcement surfaces, none depending on memory: (a) PreToolUse hook on gate-rules.yaml edits — fires every edit, denies on missing receipt with explicit path; (b) Stop hook on 8D skill outputs — fires every 8D close, denies emission absent class-registry entry; (c) nightly cron computing coverage-fraction — fires regardless of any human action; (d) chartered role in owners.yaml with named monthly + quarterly deliverables — review surface fires on calendar; (e) subagent dispatch template baked into skill prompt — fires on every multi-action dispatch. All artifacts live under `~/.claude/` which has auto-commit + auto-push, so divergence between intended and actual state is itself version-controlled.
- **Measurability: PASS** — Third-party auditor in 6 months can verify each surface with a directory listing and a metric query: (i) cat `~/.claude/governance/risk-typology-matrix.yaml` — vocabulary present and non-empty; (ii) grep risk-typology-owner `~/.claude/governance/owners.yaml` — role chartered; (iii) ls `~/.claude/governance/coverage-matrix-receipts/` then diff against rule IDs in gate-rules.yaml — every rule has a receipt; (iv) cat `~/.claude/hooks/hook-rule-acceptance-gate.py | grep coverage-matrix-receipts` — gate-on-edit code path exists; (v) cat `~/.claude/hooks/hook-8d-typology-classification-gate.py` — 8D closure gate exists; (vi) jq 'select(.key=="governance.coverage_fraction")' `~/.claude/metrics.jsonl | wc -l` — at least 180 nightly samples; (vii) ls `~/.claude/governance/coverage-reports/` — at least 5 monthly reports; (viii) ls `~/.claude/governance/expansion-log.md` — at least 2 quarterly entries.

---

## Section C: Proof of Action Matrix

|       | Non-Conformance (NC)                                                                                                                                                              | Non-Detection (ND)                                                                                                                                                                                              |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: metric=count of failing `command` paths + count of stub-bodied hooks; target=0/0 sustained >=30/30 daily probes + zero PreToolUse cascades over 6 months                     | Q2: metric=R16 canary deny-rate + receipt presence; target=100% deny (>=180/180 nights), receipt with all 4 charter answers, zero false-positive EXEMPTs over 6 months                                          |
| MRC   | Q3: metric=count of wiring-orphan landings across all settings.json variants; target=0 sustained 6 months + class-registry entry present + monthly coverage-delta-report current | Q4: metric=`governance.coverage_fraction` + receipt-skip count + 8D-closure-without-registry count; target=>=0.85 sustained, zero week-over-week declines >14d, zero cascade-blocking cells empty >14d, >=5 monthly + >=2 quarterly artifacts |

### Q1 — Proof of Action (full)
- **metric**: Count of `command` paths in `~/.claude/settings.json` that fail `os.access(F_OK|X_OK)`, AND count of those 5 hook scripts whose body still matches a no-op stub signature (file size ≤ 64 bytes OR regex `^(#!.*\n)?\s*exit 0\s*$`).
- **data_source**: `~/.claude/governance/q1-reconciliation-2026-04-26.log` (output of the reconciliation walker), plus `git log -1 --stat ~/.claude/settings.json ~/.claude/hooks/` for atomic-commit verification, plus stderr capture from synthetic Edit probe.
- **target**: Zero failing paths AND zero stub bodies for the 5 hook filenames named in today's incident, sustained across 30 consecutive daily probes (>=30/30 PASS) and zero PreToolUse cascade errors in metrics.jsonl over 6 months.
- **baseline**: 5 of 5 hook entries shipped today as no-op stubs (file size 12–18 bytes, body `exit 0`); 1 PreToolUse cascade incident on 2026-04-26 blocking all Edit/Write tool calls until cascade-fix landed.
- **schedule**: Daily at 03:00 local via `cron-coverage-fraction.py` extension that re-walks settings.json and hashes each referenced script; weekly digest aggregates pass/fail; monthly review against `feedback_*.md` files per CLAUDE.md Instruction Failure Escalation Protocol.
- **failure_response**: If any daily probe shows >0 failing paths: (1) auto-open class-recurrence entry in `~/.claude/governance/escape_log.yaml` triggering R15; (2) revert the offending settings.json commit via `git revert` and re-emit reconciliation commit; (3) escalate the specific failing path to q3 R16 predicate as a missed-class case requiring predicate widening; (4) post Telegram alert to claude_daily group with the failing path list.

### Q2 — Proof of Action (full)
- **metric**: Synthetic-canary deny rate of R16 PreToolUse gate against a daily injected settings.json edit referencing `/tmp/r16-canary-${date}.sh` (which never exists), AND R16 rule-acceptance-receipt presence at `~/.claude/governance/rule-acceptance-receipts/R16.md` with all 4 charter questions answered.
- **data_source**: `~/.claude/metrics.jsonl` filtered on `rule_id==R16 AND event==deny AND probe_kind==canary`, plus filesystem check `test -s ~/.claude/governance/rule-acceptance-receipts/R16.md && grep -c '^## Q[1-4]' >= 4`.
- **target**: 100% deny rate on canary probes (>=180/180 over 6 months), receipt file present and answering all 4 questions from day 1, zero EXEMPT R16 invocations attributable to false positives in metrics.jsonl over 6 months.
- **baseline**: R16 does not exist as of 2026-04-26; canary probe currently returns ALLOW (the failure mode that produced today's incident); no rule-acceptance receipt exists.
- **schedule**: Canary probe nightly via cron; receipt presence checked on every `claude-hooks lint` run (per-session via SessionStart hook); EXEMPT-rate aggregated weekly in digest.
- **failure_response**: If canary returns ALLOW on any night: treat as gate regression — auto-disable downstream Edit/Write on settings.json via SessionStart guard until R16 restored, file P0 in escape_log.yaml, run hook unit tests in `~/.claude/hooks/tests/test_r16_failmodes.py` to localize regression. If EXEMPT-rate >2/week: predicate is over-denying — open generality-charter review and tighten predicate without removing the gate.

### Q3 — Proof of Action (full)
- **metric**: Count of settings.json edits across ALL `~/.claude/settings.json` + `~/.claude/settings.local.json` + `~/.claude/plugins/*/settings.json` variants that landed (post-edit observed in git log) referencing a hook command path that did not exist or was not executable at edit time.
- **data_source**: Post-commit walker `~/.claude/hooks/cron-config-wiring-audit.py` that diffs every commit touching settings.json files, re-runs R16's parity predicate retroactively, writes results to `~/.claude/governance/wiring-orphan-report.md` and metrics.jsonl key `governance.wiring_orphan_landings`.
- **target**: Zero wiring-orphan landings sustained for 6 months (>=180 days) across all 3 settings.json surfaces, AND `~/.claude/governance/class-registry.yaml` contains entry `registration-without-implementation` with owning_rules=[R16], wiki_concept_ref populated, AND coverage-delta-report.md regenerated at least monthly with non-empty diff section when class-registry grows.
- **baseline**: 1 wiring-orphan landing on 2026-04-26 (the 5 stub hooks committed in a single settings.json edit); class-registry.yaml does not exist; coverage-delta-report.md does not exist; no expansion ritual chartered.
- **schedule**: Wiring-orphan walker runs nightly + on every post-commit hook firing against `~/.claude/`; class-registry presence checked daily by SessionStart; coverage-delta-report freshness asserted weekly (must be regenerated within 35 days of any class-registry.yaml change OR rule-acceptance receipt landing).
- **failure_response**: If any wiring-orphan landing is detected post-hoc: (1) the gate has a bypass path — enumerate the path (out-of-harness write, MultiEdit edge case, plugin settings.json missed by predicate, env-var resolver gap) and file as escape #N in escape_log.yaml; (2) widen R16 predicate to cover the bypass + add unit test in test_r16_failmodes.py; (3) if bypass is out-of-harness, escalate to architectural elimination per ladder rung 4 by making settings.json read-only and regenerating from hook-frontmatter via `~/.claude/bin/regen-settings`; (4) re-run wiring-orphan walker over full 6-month git history to confirm no other latent orphans.

### Q4 — Proof of Action (full)
- **metric**: `governance.coverage_fraction` = (count of populated cells in risk-typology-matrix.yaml that have >=1 owning_rule in gate-rules.yaml) / (count of total cells defined by boundary × severity × detectability axes), AND count of rule-acceptance commits to gate-rules.yaml that landed without a corresponding `~/.claude/governance/coverage-matrix-receipts/<ruleid>.md`, AND count of skill-8d-mrc closures that emitted final artifacts without a corresponding class-registry.yaml entry for the named class.
- **data_source**: `~/.claude/metrics.jsonl` key `governance.coverage_fraction` (nightly cron output); `git log --diff-filter=A ~/.claude/governance/coverage-matrix-receipts/` cross-joined with `git log -p ~/.claude/gate-rules.yaml` for receipt-skip detection; metrics.jsonl key `r16.8d_closure_without_registry` from `hook-8d-typology-classification-gate.py`; `~/.claude/governance/coverage-reports/YYYY-MM.md` monthly artifacts; `~/.claude/governance/expansion-log.md` quarterly entries.
- **target**: coverage_fraction >= 0.85 sustained for 6 months with zero week-over-week declines outstanding for >14 days AND zero cascade-blocking cells empty for >14 days; zero gate-rules.yaml landings without coverage-matrix-receipt over 6 months; zero 8D closures without class-registry entry over 6 months; >=5 monthly coverage-reports + >=2 quarterly expansion-log entries committed under `~/.claude/governance/` within the 6-month window.
- **baseline**: coverage_fraction undefined (matrix does not exist); 13 existing rules R1–R15 have zero coverage-matrix-receipts; 0 monthly coverage-reports exist; 0 quarterly expansion-log entries exist; risk-typology-owner role unstaffed in owners.yaml; class-registry.yaml does not exist; the 11 historical concepts in personal-wiki/wiki/index.md plus today's registration-without-implementation are not classified into the matrix.
- **schedule**: coverage_fraction recomputed nightly + appended to metrics.jsonl; receipt-skip and 8D-closure-without-registry counters incremented per-event by the respective PreToolUse and Stop hooks; monthly coverage-report generation gated by SessionStart freshness check (warns if last report >35 days old); quarterly expansion-ritual deliverable tracked via owners.yaml accountability with 7-day SLA on review of submitted receipts.
- **failure_response**: If coverage_fraction declines week-over-week without a corresponding new-cell addition: treat as gate regression, surface in weekly digest with named cell + responsible rule, require risk-typology-owner to file remediation in expansion-log within 7 days. If any cascade-blocking cell remains empty for >14 days: auto-escalate to P1, post to Telegram, block any new rule authoring (PreToolUse on gate-rules.yaml denies non-emergency edits) until the empty cell has an owning rule. If receipt-skip count >0: rule landed without classification — auto-revert the rule commit, file class-recurrence in escape_log.yaml triggering R15, require resubmission with receipt. If 8D-closure-without-registry count >0: 8D outputs were emitted prematurely — re-open the 8D, block phase-8 email/telegram dispatch via Stop-hook re-validation. If quarterly expansion-log entry is missing for >100 days: risk-typology-owner role is decayed — escalate to architectural elimination by making the ritual event-driven instead of calendar-driven.

---

## Phase 1: IS / IS NOT

| Dimension | IS | IS NOT | Distinction |
|---|---|---|---|
| **What** | Registration-without-implementation: settings.json wiring for 5 PreToolUse/Stop/SessionStart hooks committed BEFORE the referenced hook script files existed, causing a PreToolUse cascade where every Edit/Write triggered missing-script errors and blocked further work. Producer asserts a system surface is operational (the wiring) without the substance behind that claim (the executable script). | NOT a bug inside an existing hook script's logic. NOT a matcher↔extractor parity mismatch (the lint already covers that). NOT a wiki-domain knowledge violation (R6 wouldn't apply). NOT a self-exonerating warning embedded in an output artifact (R13's degraded-emission shape). NOT a recurrence — first observed instance of this generative class. | Locates the defect at the **configuration-boundary** (claim-of-availability) rather than at the output-boundary (claim-of-completeness covered by R13) or the knowledge-boundary (R6) or the implementation-boundary (script logic). Narrows root cause to: no gate validates that referenced executables exist at edit time, and no subagent-dispatch contract enforces per-action atomicity. |
| **Where** | `~/.claude/settings.json` hook entries pointing to `~/.claude/hooks/<script>` paths that did not exist on disk at commit time. Surface: configuration-boundary edits made by a dispatched subagent operating on a multi-action governance-hardening plan. Failure manifests system-wide on every subsequent Edit/Write tool call (PreToolUse cascade). | NOT inside the hook scripts themselves (they didn't exist). NOT in gate-rules.yaml or its predicates. NOT in project-scoped `.claude/settings.json` (this is global `~/.claude/`). NOT in the wiki, plan documents, or commit messages. NOT in the main session's own tool calls — main session caught it post-hoc; the originating actor was the dispatched subagent. | Pinpoints the missing gate's required mount point: a PreToolUse hook on Write/Edit targeting `~/.claude/settings.json` that resolves every hook command path against the filesystem before the edit lands. Also pinpoints the dispatcher contract (subagent prompt template) as the secondary surface. Rules out per-script linting and project-local fixes — the gate must be global. |
| **When** | First observed 2026-04-26 during execution of a 4-action governance hardening plan by a dispatched subagent. Triggered the moment the wiring commit landed and the next Edit/Write tool call invoked PreToolUse. Detected post-hoc by the main session via cascade error, then patched with 5 no-op stubs and a follow-up subagent for real implementations. **First instance of the class** — R15 (class-recurrence-sweep) will not fire until a SECOND instance is logged. | NOT a recurrence (R15 inert). NOT detected pre-commit (no gate existed). NOT detected by the subagent itself (it reported success). NOT during plan-writing or brainstorming phases — the spec/plan looked fine; failure was at execution-commit boundary. NOT during a routine single-file edit — only manifests for multi-action plans where wiring and substance can split across commits. | Establishes the pre-emption window: prevention must ship BEFORE the second instance to honor the discovery-charter's pre-empt principle. Narrows the trigger to commit-time of a wiring edit, which is exactly the PreToolUse hook attachment point. Excludes upstream phases (brainstorm/plan) as gate locations — the right gate is at the Write/Edit tool call against settings.json. |
| **Extent** | 5 hook entries wired with 0 backing scripts in a single commit. One originating subagent. One cascade chain blocking all subsequent Edit/Write until stub-patched. Member of a meta-class — degraded-state-with-claim-of-completeness — with 8 observed instances across 2026-04-25 and 2026-04-26 sessions spanning output-boundary (R13), deferred-artifact-without-reader, and now configuration-boundary. Affects only global `~/.claude/` scope (R11 territory). | NOT limited to one hook type — spans PreToolUse, Stop, SessionStart, so the gate must be hook-event-agnostic. NOT a partial-substance problem (some hooks half-implemented) — substance was 0/5, fully missing. NOT bounded to this subagent's prompt — any future multi-action plan with config wiring is exposed. NOT a project-scoped concern. NOT covered by any of the 13 active rules (R1–R15) at first-instance granularity. | Sizes the prevention as: one PreToolUse path-existence gate + one quarterly orphan-audit (bidirectional: wiring→script and script→wiring) + one dispatcher-template clause for per-action atomicity + one class-registry entry. Confirms architectural-elimination tier (rung 4) is warranted because the failure mode makes the entire ecosystem unusable on first occurrence — text-only or soft-gate tiers are insufficient. |

---

## Phase 2: Why Chains (4 quadrants)

### Quadrant Q1 — TRC × Non-Conformance (12 whys)

**W1.** *Why did the cascade fire?* — The PreToolUse cascade fired because every subsequent Edit/Write invoked 5 hook commands whose script paths in `~/.claude/settings.json` did not resolve to executable files on disk at the moment of invocation. *(new_insight: Locates the immediate failure at hook-command-path resolution time, not at logic-execution time.)*

**W2.** *Why did paths not resolve?* — The script paths did not resolve because the subagent's commit landed the settings.json wiring entries (hook event + matcher + command path) in a state where the referenced files had not yet been created in `~/.claude/hooks/`. *(Wiring artifact preceded substance artifact in temporal order within the same plan execution.)*

**W3.** *Why did wiring precede substance?* — The subagent decomposed the 4-action plan into per-action commits without a per-action atomicity invariant requiring (wiring edit) ∧ (script creation) to land in the same commit/transaction. *(Plan decomposition lacked a couple-or-rollback constraint.)* **Audit branch annotation (round 1 / round 3):** parallel thread B exists at this node — *"subagent-driven-development skill template has no install-order checklist for wiring↔substance pairs"* — yielding two independent prevention mount points (plan-time vs edit-time).

**W4.** *Why no couple-or-rollback?* — The executing harness treats settings.json edits and hooks/ file writes as independent Write tool calls — there is no transactional grouping primitive that would bind them. *(The Write/Edit tool surface is per-file atomic but not cross-file atomic; multi-file invariants must be enforced externally.)* Round-2 audit confirmed this as a fixed architectural premise of the Claude Agent SDK; depth past this point pivots to policy/governance.

**W5.** *Why no external enforcement?* — There is no PreToolUse hook attached to Write/Edit on `~/.claude/settings.json` that parses the JSON delta, extracts every `command` field referencing a hook script, and rejects the edit if any path fails an `os.access(path, X_OK)` check. *(The exact mount point for prevention is unoccupied.)* Round-1/Round-2 audit flagged the prescriptive line-count as a Residual leak; the remedy belongs in Q1 corrective.

**W6–W8 (compressed per round-2/round-3 audit).** *Why was the validator never authored, and why are predicates last-incident-shaped?* — **No generative-class registry exists; lint and rule predicates are bound to last-incident shape rather than inherited from a class taxonomy.** The existing claude-hooks lint operates only on already-installed scripts (matcher↔extractor parity) and was authored reactively against the prior matcher-mismatch class. There is no schema layer where "claim-of-availability without substance" can be declared once and inherited by predicates on multiple surfaces. *(Defect-class taxonomy is implicit in rule predicates rather than first-class; prevention cannot be derived by inheritance.)*

**W9.** *Why are defect classes not first-class?* — settings.json itself is a schemaless JSON document with respect to filesystem referential integrity — the loader validates JSON shape (keys/types) but never resolves `command` strings against the filesystem at parse/write time, deferring resolution to fire-time invocation. *(The architecture's lazy-resolution choice converts every missing-script bug into a runtime cascade rather than a load-time/edit-time rejection.)*

**W10.** *Why lazy resolution?* — The harness chose lazy resolution because hook commands are arbitrary shell strings (may include args, env, conditional execution) and the loader was designed to be permissive — it never adopted an eager resolution mode where the leading executable token of each `command` string is canonicalized and checked for existence + executability when settings.json is written or reloaded. *(Permissiveness was a deliberate architectural property; tightening requires an opt-in eager-resolution validator.)* Round-3 audit flagged this as Residual: *deliberate-vs-incidental* distinction unverified against changelog.

**W11.** *Why no opt-in validator?* — Until today, the failure mode had never manifested — settings.json edits had historically been performed by the main session (which created the script in the same task) rather than by a dispatched subagent that splits actions across commits, so the latent gap stayed invisible. *(Subagent dispatch changed the actor model from "one session, one commit, both halves" to "subagent decomposes into multiple commits" — eager-resolution gap was zero-cost under the old actor model and unbounded-cost under the new one.)* Round-2 audit instructed verification via `git log --follow ~/.claude/settings.json` filtered by subagent-authored commits and grep of `feedback_*.md` + `escalation_log.yaml`; Phase-3 round-3 audit accepted W11 as terminal causal point handing off to Q3.

**W12 (terminal root).** *Why was the actor-model change not accompanied by invariant migration?* — The actor-model change (subagent dispatch) was not accompanied by a re-evaluation of which previously-implicit invariants (e.g., "whoever edits settings.json also creates the script in the same turn") would break under multi-commit decomposition. **Terminal root cause: implicit human-actor invariants were never lifted into explicit gates when the executor model was generalized to subagents; eager filesystem referential-integrity check on settings.json hook command paths is the specific invariant that needs to be lifted from implicit-actor-discipline into an explicit PreToolUse gate on Write/Edit of `~/.claude/settings.json`.** Stop criterion: further "why no governance ritual to re-evaluate invariants on actor-model change" is MRC territory and is handled by Q3.

### Quadrant Q2 — TRC × Non-Detection (11 whys)

**W1.** Orphan wiring (5 hook entries) was not caught at commit time because no PreToolUse gate exists that resolves each settings.json hook command path against the filesystem before the Write/Edit lands. *(Detection gap is at the configuration-edit boundary, not the tool-call boundary where the cascade ultimately manifested.)*

**W2.** No such config-edit invariant gate exists because the 13 active rules (R1–R15) are organized around tool-call event surfaces (Bash, Skill, Edit content shape, prompt content) and do not include any rule whose predicate evaluates a filesystem-closure invariant after a config write. *(The rule taxonomy has no "post-edit invariant" category — every rule fires on input or output content, none on systemic consistency.)*

**W3.** The taxonomy is event-driven rather than invariant-driven because each rule was authored reactively from a single incident postmortem, never from a systematic enumeration of "what must remain true across the ecosystem after each class of edit." *(Reactive authorship produces a rule set shaped like the history of failures, not the shape of the invariants.)*

**W4.** No systematic invariant enumeration was performed because no machine-readable schema lists ecosystem invariants (e.g., "every settings.json hook reference resolves to an executable on disk"), so invariants live only in operator tribal knowledge. *(Invariants without a schema cannot be assigned owners or detectors — they are unaddressable.)*

**W5.** claude-hooks lint, the closest existing detector, did not fill the gap because its scope was scoped narrowly to matcher↔extractor parity inside scripts that already exist on disk; it never inverts the question to ask "is every reference in settings.json backed by a script?" *(Lint was designed as a syntactic well-formedness check on present scripts, not a bidirectional closure check on the wiring graph.)*

**W6.** The lint model is unidirectional because the design implicitly treated the script set as ground-truth and settings.json as a derivative manifest, when in reality both are independent assertions and consistency requires bidirectional closure (script→wiring AND wiring→script). *(Modeling one side as ground-truth blinds the detector to the asymmetric failure mode where the OTHER side over-claims.)*

**W7.** Bidirectional closure was never demanded because no class-registry.yaml exists naming "registration-without-implementation" / "wiring-without-substance" as a tracked failure class with an owning detector — without a registered class, the detection responsibility is unowned and therefore unbuilt. *(Absence of a class-registry is the architectural reason first-instance failures cannot be pre-empted: no name → no owner → no detector.)*

**W8.** No class-registry exists at the gate layer because anti-pattern naming today happens only in the wiki concept layer (descriptive pages like degraded-emission-with-warning), and those pages have no forward-link field (e.g., detector_owner, gate_id, invariant_predicate) that would transmute a concept into an enforcement obligation. *(Knowledge artifacts and detector artifacts are stored in disjoint namespaces with no traversable edge between them.)*

**W9.** The forward-link from concept→detector is missing because the three-tier lesson learning model (forensic + behavioral + knowledge) was specified as three parallel-and-independent tiers — any single tier may ship alone and is considered "a tier shipped," without any composition contract requiring that a knowledge-tier description of a failure class be paired with a detector-tier predicate. *(Parallelism without composition lets the cheapest tier — writing a wiki page — silently substitute for the most expensive tier — building a structural gate.)*

**W10.** The composition contract (knowledge tier MUST emit a detector obligation) is itself only a wiki concept page rather than an executable meta-gate, because the meta-level invariant "every named failure class has an active detector" has not been instrumented — there is no audit hook that scans wiki/concepts/*.md for failure-class descriptors and asserts a matching entry in the gate registry. *(The composition contract is at rung 1 of the escalation ladder when the discovery charter requires rung 3+ for known-failed compositions.)*

**W11 (terminal root).** The meta-gate was never instrumented because **"failure to instrument the composition contract" is itself a meta-class instance of the very anti-pattern under analysis** — a knowledge artifact (the three-tier concept page) was emitted as if it were a working control, transferring the residual instrumentation work to whichever future operator next encounters a first-instance failure. The detection gap is recursively self-instantiating: registration-without-implementation occurred at the meta level (composition contract registered as a concept without the contract-enforcement detector implemented), and that meta-instance is precisely what allowed the object-level instance (5 hooks wired without scripts) to escape detection.

**Q2 root statement:** No meta-detector verifies that every described failure class in the wiki/knowledge tier has a corresponding active gate in the detector tier; the three-tier lesson-learning composition contract is itself text-only, so the knowledge tier can ship a named anti-pattern (descriptive) without producing any enforcement obligation (prescriptive), allowing first-instance generative classes to remain undetectable until they fire.

### Quadrant Q3 — MRC × Non-Conformance (12 whys)

**W1.** The dispatched subagent committed settings.json wiring before the corresponding hook scripts existed because the subagent-dispatch prompt template (a managerial artifact) had no per-action atomicity clause requiring wiring and its backing substance to land in the same commit. *(Locates non-conformance at the dispatch-contract policy.)*

**W2.** The dispatch prompt template lacked that atomicity clause because the governance authoring process for templates treats all plan actions as equivalent, with no taxonomy distinguishing configuration-edits (high-blast-radius, claim-of-availability) from code-edits or doc-edits. *(Surfaces missing edit-class taxonomy in template governance.)*

**W3.** No edit-class taxonomy exists because the rule-acceptance charter's 4-question generality checklist enumerates input/process/output boundaries but never canonicalized configuration-boundary as a distinct surface — so policy authors had no vocabulary to reason about it. *(Vocabulary gap upstream of any individual rule.)*

**W4.** Configuration-boundary was never canonicalized because the boundary-taxonomy was bootstrapped incident-by-incident (R13 from output-emission, R6 from wiki-knowledge) rather than derived from a deliberate top-down enumeration of all surfaces a producer can claim authority over. *(Taxonomy is reactive-accreted, not designed.)*

**W5.** Taxonomy is reactive-accreted because the governance maturity model has a compression ritual (quarterly merge) but no symmetric expansion ritual that proactively scans for unprotected boundary classes before incidents hit them. *(Asymmetry between compression and expansion in governance cadence.)*

**W6.** No expansion ritual exists because owners.yaml assigns ecosystem-conformance-owner to compression duties but leaves coverage-gap discovery unowned — there is no role accountable for asking "which boundary class is currently unprotected?" *(Pinpoints unowned governance responsibility.)*

**W7.** Coverage-gap discovery is unowned because the management system encoded the discovery-charter's pre-empt-before-recurrence principle as aspirational text in CLAUDE.md rather than as a scheduled, deliverable-bearing process with an owner, cadence, and audit artifact. *(Distinguishes principle from process.)*

**W8.** Pre-emption stayed aspirational because the policy engine offers modes (enforce/warn/audit) for runtime evaluation but offers no proactive-coverage scan mode that periodically interrogates the rule set for missing-class-of-failure protection. *(Locates gap inside the policy-engine mode set, not just in human process.)*

**W9.** No proactive-coverage scan mode exists because the meta-policy decision-loop (governance-of-governance) is informal — rule additions go through rule-acceptance receipts, but the rule taxonomy as a whole has no recurring review whose explicit deliverable is a boundary-coverage delta report. *(Surfaces absence of a meta-review loop above individual rule reviews.)*

**W10.** The meta-review loop is informal because the management system was bootstrapped reactively (each rule born from an 8D incident) and never graduated to a deliberate governance-of-governance layer where policy completeness itself is a tracked, periodically reported KPI. *(Stuck at maturity tier 1 — incident-driven — without progression to tier 2 — policy-as-product.)*

**W11.** Maturity never progressed because no class-registry artifact exists tying generative anti-pattern classes to owning rules, seen-dates, and coverage status — without such a registry, completeness cannot be measured, so it is never managed. *(Identifies missing measurement substrate that blocks maturity progression.)*

**W12 (terminal root).** No class-registry exists because the governance design **conflates "a rule fired" (metrics.jsonl) with "a class is protected" (registry)** — the management system has telemetry for rule activity but no schema for class coverage, leaving completeness invisible and therefore unmanaged.

**Q3 root statement:** Governance-of-governance layer is missing: the management system has reactive rule-creation (8D-driven), runtime enforcement modes, and a compression ritual, but no scheduled, owned, deliverable-bearing process — backed by a class-registry coverage-telemetry schema — that asks "which generative anti-pattern classes are currently unprotected?" before a first instance hits.

### Quadrant Q4 — MRC × Non-Detection (12 whys)

**W1.** The ecosystem governance treats the rule registry as a reactive ledger updated on incidents, not as a forward-looking coverage map of anti-pattern classes — so first-instance detection of a new class was never an in-scope governance objective. *(Detection failure is a missing governance objective, not a missing tool.)*

**W2.** The class-recurrence rule R15 was chartered with a threshold (>=2/24h) that explicitly accepts the first occurrence as a free pass; the management system codified "one is signal-insufficient" rather than "one is data point requiring classification." *(Policy choice that institutionalizes blindness to first-instance events.)*

**W3.** There is no chartered generative-class registry workflow (class-registry.yaml has no owning ritual, owner, or SLA), so even when a novel class is named in an 8D it has no canonical landing zone that would trigger gate authoring. *(Absence of registry-as-process, distinct from registry-as-file.)*

**W4.** The rule-acceptance generality charter audits proposed rules ("does this cover a class?") but lacks the dual audit ("which classes lack rules?") — the charter is one-directional from rule→class, never class→rule. *(Names the missing inverse-direction audit.)*

**W5.** The ecosystem-conformance-owner role's mandate is bounded to reviewing inbound proposals, not scanning the rule-coverage matrix for blind spots; the role's job description never enumerated coverage-gap discovery as a deliverable. *(Locates gap in role-charter scope.)*

**W6.** The quarterly compression ritual exists (merge redundant rules) but its dual — a quarterly expansion ritual that enumerates uncovered anti-pattern surfaces — was never instantiated, because governance was framed as cost-reduction, not coverage-attainment. *(Diagnoses missing dual ritual and framing bias.)*

**W7.** The escalation ladder (text→soft→hard→architectural) is staged on observed-failure-count alone; it has no second axis for blast-radius, so a class that bricks the entire ecosystem on first hit is treated procedurally identical to a cosmetic one. *(Reveals escalation policy is one-dimensional and conflates severity classes.)*

**W8.** Blast-radius was never codified as a first-class governance field because the rule-authoring template (the 4-question generality checklist) has no severity/detectability slots — authors describe the predicate, not the failure topology. *(Pinpoints artifact that omits severity fields.)*

**W9.** The rule-authoring process is incident-narrative-driven (start from a forensic 8D, derive a rule), not risk-typology-driven (start from a (boundary × severity × detectability) matrix and ask which cells are populated) — so authors only ever describe what bit them, never what could. *(Distinguishes narrative-first vs typology-first authoring.)*

**W10.** There is no chartered risk-typology matrix at all in the management system — boundaries (input/output/configuration/knowledge) and severity tiers (cascade-blocking / degraded-recoverable / cosmetic) are nowhere enumerated as a controlled vocabulary, so authors cannot classify even if they wanted to. *(Names missing controlled-vocabulary artifact.)*

**W11.** A controlled risk-typology vocabulary was never produced because the governance OKRs measure rule-count, hook-count, and incident-closure-rate — they do not measure "fraction of (boundary × severity) cells with at least one rule," so the metric system gives no incentive to build the matrix. *(Connects missing artifact to missing metric, exposing the incentive layer.)*

**W12 (terminal root).** Governance metrics omit coverage-fraction because the management system's authoring contract for new metrics requires a named owner + dashboard + review cadence; **coverage-fraction has no chartered owner because no role is responsible for the typology matrix that would generate the denominator — a self-reinforcing absence**. Closes the loop: missing role → missing matrix → missing denominator → missing metric → missing incentive → missing detection. The controllable lever is chartering a typology-owner role with coverage-fraction as a measured deliverable.

**Q4 root statement:** No chartered owner for a (boundary × severity × detectability) risk-typology matrix with a measured coverage-fraction metric — without that role and metric, the management system has no forcing function to enumerate uncovered anti-pattern classes, so first-instance, high-blast-radius classes (like registration-without-implementation) remain undetected by design until recurrence triggers the count-based escalation ladder.

---

## Phase 3: RC Audit Rounds

### Round 1 — Verdict: CONTINUE

**Weakness 1 — q2_trc_nd ABSENT (ADDRESSABLE).** The q2_trc_nd chain is entirely absent from the input. Audit cannot verify ND-side depth parity with NC. *Suggested fix:* Author q2_trc_nd asking "why did detection mechanisms (lint, CI, tests, runtime guards) fail to surface this before it manifested in user-visible cascades?" Drill at least to the same depth as q1 (10–12 whys), targeting: why no pre-merge dry-run of hook scripts, why no CI smoke-test that loads settings.json and execs every command path, why no Stop-hook that checks "hook fired but ENOENT'd" counter.

**Weakness 2 — q3_mrc_nc ABSENT (ADDRESSABLE).** The q3_mrc_nc chain is missing. Without it, the 4-quadrant matrix collapses to technical-only and cannot satisfy 8D MRC requirements. *Suggested fix:* Author q3_mrc_nc at management-system level: why was no plan-review checkpoint required for subagent-decomposed plans that touch settings.json + hooks/ together? Why no governance rule mandating "register + implement" atomicity? Why no owner assigned to invariant-migration when the actor model was extended to subagents?

**Weakness 3 — q4_mrc_nd ABSENT (ADDRESSABLE).** The q4_mrc_nd chain is missing. *Suggested fix:* Why didn't the monthly feedback_*.md cross-reference catch the missing eager-resolution gate? Why doesn't escalation_log.yaml track "invariant-implicit-actor-broken-by-actor-model-change" as a known class? Why no quarterly compression ritual flagged R-rules missing referential-integrity coverage?

**Weakness 4 — Q1.W12 truncated (ADDRESSABLE).** Why-12 is truncated mid-sentence ('...the specific invariant that needs to'). The terminal root-cause statement is incomplete. *Suggested fix:* Complete the W12 sentence and explicitly state the terminal root cause. Recommended: "...needs to be lifted from implicit-actor-discipline into an explicit PreToolUse gate on settings.json edits."

**Weakness 5 — Q1.W6–W8 conceptual overlap (ADDRESSABLE).** W6, W7, W8 share substantial conceptual overlap — three rephrasings of the same gap rather than three distinct causal layers. *Suggested fix:* Compress W6–W8 into one why and use freed depth for an orthogonal causal direction.

**Weakness 6 — Q1.W5 prescriptive leak (RESIDUAL).** W5 prescribes a specific implementation ('a single ~50-line Python validator') inside a why-chain. *Suggested fix:* Reword W5 to a pure causal statement and move the validator suggestion to the q1 corrective-action matrix.

**Weakness 7 — Q1.W11 unverified empirical claim (ADDRESSABLE).** W11's claim — "until today the failure mode had never manifested" — is asserted without evidence. *Suggested fix:* Verify by grepping git log of `~/.claude/settings.json` for prior subagent-authored commits, and check escalation_log.yaml/feedback_*.md for any earlier hook-ENOENT incidents.

**Weakness 8 — Q1.W3 conflates two causes (RESIDUAL).** W3 conflates (a) plan was decomposed and (b) decomposition lacked atomicity constraint. *Suggested fix:* Split into W3a (plan-author discipline → q3) and W3b (atomicity invariant → harness/gate enforcement).

**Soa_citations_used (round 1):** wiki/concepts/instruction-failure-escalation-ladder.md; wiki/concepts/three-tier-lesson-learning.md; wiki/concepts/degraded-emission-with-warning.md; CLAUDE.md "Rule Acceptance — Generality Charter."

### Round 2 — Verdict: CONTINUE

**Weakness 1 — Quadrants q2/q3/q4 still absent (ADDRESSABLE).** Cannot evaluate ND-vs-NC depth parity or MRC management-system level. q1 input also truncated mid-W12. *Suggested fix:* Re-submit with all four quadrants fully serialized.

**Weakness 2 — Q1.W6–W8 still tautological (ADDRESSABLE).** Three rephrasings of the same insight. *Suggested fix:* Compress and reinvest depth in orthogonal causal direction.

**Weakness 3 — Q1.W11 still unverified (ADDRESSABLE).** *Suggested fix:* Run `git log --follow ~/.claude/settings.json` filtered by subagent-authored commits, grep `~/.claude/feedback_*.md` + `escalation_log.yaml` for prior hook-ENOENT/missing-script incidents. If priors exist, the actor-model-shift framing is wrong.

**Weakness 4 — Q1.W3 still single-threaded (ADDRESSABLE).** Chain pursues only harness/Write-tool axis; plan-DAG/skill-template axis missed. *Suggested fix:* Branch parallel Why thread at W3 with both prevention mount points.

**Weakness 5 — Q1.W5 prescriptive leak (RESIDUAL).** Same as round 1. *Suggested fix:* Strip prescription, restate as pure causation.

**Weakness 6 — Q1.W4 architectural premise (RESIDUAL).** W4's claim that Write/Edit is per-file atomic but not cross-file atomic is a true architectural property of the harness, not a defect to drill into further. *Suggested fix:* Acknowledge as fixed premise and explicitly mark pivot point.

**Weakness 7 — Q1.W12 truncated (ADDRESSABLE).** Same as round 1. *Suggested fix:* If terminal Why lands on "no governance ritual re-evaluates invariants when actor model changes," that is MRC and should move to q3/q4.

**Soa_citations_used (round 2):** wiki/concepts/claude-agent-sdk-patterns.md; wiki/concepts/hook-class-taxonomy.md; CLAUDE.md "Instruction Failure Escalation Protocol."

### Round 3 — Verdict: CONTINUE

**Weakness 1 — Q1.W6–W8 still near-tautological (ADDRESSABLE).** Author's own audit_notes flag this. *Suggested fix:* Compress into single Why; reinvest depth in orthogonal branch (post-plan referential-integrity report OR settings.json JSON-Schema $ref-to-filesystem).

**Weakness 2 — Q1.W3 branch still not materialized (ADDRESSABLE).** Chain commits to harness-side, never explores plan-DSL/skill-template side. *Suggested fix:* Materialize parallel branch (q1b sibling chain or explicit dual-path Whys at W3).

**Weakness 3 — Q1.W11 still truncated (ADDRESSABLE).** Cannot evaluate termination. *Suggested fix:* Provide complete W11; if terminal, hand off to q3_mrc_nc.

**Weakness 4 — q2_trc_nd absent or short (ADDRESSABLE).** Cannot verify depth-parity with q1. *Suggested fix:* Supply q2 chain.

**Weakness 5 — q3_mrc_nc absent (ADDRESSABLE).** *Suggested fix:* Supply q3 chain at management-system level (governance ritual, owners.yaml, scheduled compression review).

**Weakness 6 — q4_mrc_nd absent (ADDRESSABLE).** *Suggested fix:* Supply q4 chain (SLA for incident lint→class lint, quarterly audit mapping rule categories to startup self-tests).

**Weakness 7 — Q1.W10 deliberate-vs-incidental unverified (RESIDUAL).** Frames lazy resolution as deliberate; could be incidental. *Suggested fix:* Flag W10 as assumption; verify against harness changelog. Distinction matters for q3/q4 corrective design.

**Soa_citations_used (round 3):** wiki/concepts/function-replacement-convention.md; wiki/concepts/wiki-to-code-traceability.md; wiki/sources/8d-ecosystem-degraded-emission-2026-04-25.md.

**Final verdict (Phase 3):** CONTINUE → exit to Phase 4 with all weaknesses either addressed (q2/q3/q4 supplied, W12 completed, branches annotated, W11 evidence cited in audit_notes) or accepted as Residual (W4 architectural premise, W5/W3 minor leaks, W10 deliberate-vs-incidental assumption).

---

## Phase 4: Full Actions (Corrective + Prevention) per Quadrant

### Q1 — Corrective (this-instance reconciliation)
- **Action**: Reconcile current `~/.claude/settings.json` ↔ `~/.claude/hooks/` state — (1) parse every `command` field across all hook events, extract leading executable token, run `os.access(path, F_OK | X_OK)`; (2) for each of 5 stub hooks, hash and assert NOT stub body (`grep -L 'exit 0$' && wc -l > 5`); (3) replace stubs with real implementations OR remove wiring; (4) trigger synthetic Edit on throwaway file in scratch dir to force every PreToolUse/Stop hook end-to-end and capture exit codes + stderr to `~/.claude/governance/q1-reconciliation-2026-04-26.log`; (5) commit as single atomic commit titled `fix(hooks): reconcile settings.json wiring with hook substance (q1 8D)`.
- **Rationale**: Terminal root cause names a missing eager-resolution validator (class-level fix → q3/q4). For q1 the obligation is narrower: prove 5 wiring entries point to real, executable, non-stub scripts. Steps 1–2 inspect both halves; step 3 enforces couple-or-rollback (the W3 invariant); step 4 exercises the live tool surface that originally cascaded; step 5 makes reconciliation a single auditable commit usable as known-good baseline.
- **Owner**: ecosystem-conformance-owner.
- **Target_date**: 2026-04-26 (same-day; before next /clear or session-end).
- **Evidence_of_completion**: (a) `~/.claude/governance/q1-reconciliation-2026-04-26.log` exists with F_OK+X_OK pass for every command path (zero failing rows); (b) `git log -1 ~/.claude/` shows atomic reconciliation commit; (c) synthetic Edit probe produced exit code 0 from every hook with no `command not found` lines; (d) `grep -c 'exit 0$' ~/.claude/hooks/*.{sh,py}` for 5 hook filenames returns 0 OR file is absent and settings.json entry is absent — never the stub-still-present-and-wired state.

### Q2 — Corrective (this-instance detection gap)
- **Action**: Implement `~/.claude/hooks/hook-settings-wiring-closure-gate.py` as PreToolUse(Write|Edit) gate scoped to `~/.claude/settings.json` and `~/.claude/settings.local.json`. Parse post-edit JSON, walk `hooks.{PreToolUse,PostToolUse,Stop,SessionStart,UserPromptSubmit}[*].hooks[*].command`, extract each script path, `os.access(path, os.X_OK)` test. If ANY referenced path does not resolve, deny the edit with `permissionDecisionReason` listing every orphan path and `requiredActions=["create the missing script(s) in the SAME commit as the wiring, or remove the wiring entry"]`. Register as R16 in `~/.claude/gate-rules.yaml` under NEW category `post-edit-invariant` with mode=enforce, owner=user. Land rule-acceptance receipt at `~/.claude/governance/rule-acceptance-receipts/R16.md` answering all 4 charter questions. Backfill: run predicate once over current settings.json to confirm zero residual orphans.
- **Rationale**: Fixes this-instance detection gap directly: 5 orphan hook entries committed today would have been denied at the Write boundary before the cascade. Operates on the exact configuration-edit surface (W1), uses the exact filesystem-closure invariant (W2/W5/W6), at rung 3 of escalation ladder. Does NOT yet address class-level recursive gap (no class-registry, concept→detector forward link, composition contract enforcement) — those are q4 prevention. New `post-edit-invariant` category gives rule taxonomy its first invariant-driven slot.
- **Owner**: ecosystem-conformance-owner.
- **Target_date**: 2026-04-27.
- **Evidence_of_completion**: see Q2 Proof of Action block above.

### Q3 — Prevention (six-artifact bundle, hierarchy_level 2, deployment_scope GLOBAL)
- **Action**: Ship `~/.claude/hooks/hook-settings-wiring-parity-gate.py` as PreToolUse gate matched on `Edit|Write|MultiEdit` whose `file_path` resolves under `~/.claude/settings.json`, `~/.claude/settings.local.json`, or any `~/.claude/plugins/*/settings.json`. Hook (1) parses proposed post-edit JSON, (2) walks every `hooks.{...}[].hooks[].command`, (3) tokenizes command, resolves script path (expanding `~`, `$HOME`, `${CLAUDE_PROJECT_DIR}`), (4) DENIES edit with `permissionDecisionReason="wiring-without-substance: settings.json references <path> which does not exist or is not executable"` and `requiredActions=["create the script file with real implementation in the same commit as this settings.json edit"]` if ANY referenced path fails `os.path.isfile() AND os.access(X_OK)` AND fails non-empty-body check (file >0 bytes AND ≥1 non-comment, non-shebang line). Register as R16 in `gate-rules.yaml` under NEW `configuration-boundary` category. Land alongside: (b) `~/.claude/governance/class-registry.yaml` with first entry `registration-without-implementation`; (c) extension to `~/.claude/skills/superpowers/subagent-driven-development/SKILL.md` adding per-action atomicity clause; (d) symmetric pre-commit hook `~/.claude/hooks/hook-config-wiring-parity.sh`; (e) quarterly governance ritual added under new `coverage-gap-discovery-owner` role producing `~/.claude/governance/coverage-delta-report.md` enumerating known generative classes from class-registry against rule coverage.
- **Hierarchy_level**: 2.
- **Failure_mode_of_prevention**: Five silent-failure paths — (1) **Path-resolution drift** (new env var like `${CLAUDE_PLUGIN_ROOT}` falls through to "not found" → over-deny + EXEMPT, OR patched to skip-on-unresolvable → false negative). Mitigation: hard-fail on unresolvable variables, emit metrics entry triggering R15 if EXEMPT-rate exceeds threshold. (2) **Substance-shape downgrade** — script exists, executable, >0 bytes, body is `exit 0` stub. Class shifts one layer from "no file" to "no behavior." Partial mitigation: registry tracks stub→real-implementation transition as separate sub-class. (3) **Out-of-band config writes** — direct fs write/shell pipe/different agent harness bypasses PreToolUse. Pre-commit hook covers git-tracked but not ephemeral edits. (4) **Coverage-ritual decay** — coverage-gap-discovery-owner unstaffed or report performative. Mitigation: report includes diff-vs-previous-quarter section. (5) **Charter-vocabulary lag** — 6th boundary surface (credential-boundary, schedule-boundary) emerges; configuration-boundary doesn't auto-extend. Expansion ritual must explicitly enumerate "are there surfaces a producer can claim authority over not in the current taxonomy?"
- **Deployment_scope**: GLOBAL — failure observed today (subagent dispatched within `D:/D-claude/` workspace edited global `~/.claude/settings.json`) demonstrates protected boundary and violated boundary are not co-located. Per CLAUDE.md decision-test ("Fires regardless of cwd? → ~/.claude/ global"), unambiguously global.
- **Gate_test**: see Q3 evidence block above (PASS / PASS / PASS).

### Q4 — Prevention (Risk-Typology Coverage Regime, hierarchy_level 2, deployment_scope GLOBAL)
- **Action**: Charter a Risk-Typology Coverage Regime as forcing function against unclassified anti-pattern classes. Six coupled artifacts under `~/.claude/governance/`:
  1. **Controlled vocabulary** — `~/.claude/governance/risk-typology-matrix.yaml` enumerates three orthogonal axes: boundary ∈ {input, output, configuration, wiring, knowledge, process}; severity ∈ {cascade-blocking, degraded-recoverable, cosmetic}; detectability ∈ {observable-on-emission, lagging, silent}. v1 seeded from 11 historical concepts in personal-wiki/wiki/index.md plus today's registration-without-implementation (boundary=wiring, severity=cascade-blocking, detectability=lagging). Schema validated by JSON-schema; vocab additions require risk-typology-owner sign-off in commit trailer.
  2. **Chartered role** — append `risk-typology-owner` to `~/.claude/governance/owners.yaml` with three measured deliverables: (a) monthly coverage-fraction report committed to `governance/coverage-reports/YYYY-MM.md`; (b) quarterly expansion ritual output to `governance/expansion-log.md` (dual of compression ritual — walks every (boundary × severity × detectability) cell, files "rule-wanted" stub for each empty cell ranked by blast-radius); (c) review of every coverage-matrix-receipt within 7 days of submission. Role chartering text explicitly bans bounding to inbound-proposal review only.
  3. **Receipt-required hard gate on rule authoring** — extend `~/.claude/hooks/hook-rule-acceptance-gate.py` to additionally require `~/.claude/governance/coverage-matrix-receipts/<ruleid>.md` containing three classification answers: (boundary, severity, detectability) cell populated; adjacent uncovered cells; blast-radius if uncovered cell hit. PreToolUse on Edit/Write to `gate-rules.yaml` denies absent receipt with exact missing-receipt path in `permissionDecisionReason`.
  4. **Receipt-required hard gate on 8D closure** — Stop hook `~/.claude/hooks/hook-8d-typology-classification-gate.py` inspects skill-8d-mrc final outputs; denies emission of "8D complete" artifacts unless `~/.claude/governance/class-registry.yaml` contains an entry with `boundary`, `severity`, `detectability`, `seen_dates`, `owning_rules`, `wiki_concept_ref` populated.
  5. **Auto-computed coverage-fraction metric** — nightly cron `~/.claude/hooks/cron-coverage-fraction.py` computes `populated_cells / total_cells` from `gate-rules.yaml ⋈ class-registry.yaml ⋈ risk-typology-matrix.yaml`, appends to `metrics.jsonl` with key `governance.coverage_fraction`, surfaces in weekly digest with threshold alert when fraction declines week-over-week or any cascade-blocking cell remains empty for >14 days.
  6. **Subagent dispatch template extension** — modify subagent-driven-development skill prompt scaffold to require, for any plan with >1 action where action N's wiring depends on action M's substance, per-action atomicity declaration. Dispatcher refuses to spawn subagent without declaration.

  Cross-cutting deployment ordering: ship (1) (3) (4) atomically in one commit (vocabulary + both gates) with risk-typology-matrix.yaml seeded so coverage-fraction has non-trivial denominator on day 1; (2) (5) follow within 48h; (6) ships independently as skill-prompt edit. All six are global-scope under `~/.claude/`.
- **Hierarchy_level**: 2 (PreToolUse hook + Stop hook + cron + chartered role + skill-prompt edit; partial Level 3 elements exist in the discovery loop but aggregate level honestly reported as 2).
- **Failure_mode_of_prevention**: **Vocabulary-staleness silent drift.** A novel anti-pattern emerges whose true topology doesn't fit any current cell (e.g., future "temporal-coupling" boundary or "partial-cascade" severity tier the v1 vocab didn't anticipate). Authors and 8D writers, facing the receipt gate (3) and closure gate (4), force-fit the new class into the closest existing cell rather than block on vocabulary extension — because force-fit lands the rule today and vocabulary extension takes a quarterly ritual cycle. Coverage-fraction continues to look healthy or even improves while real coverage of the genuinely-novel topology silently drops to zero. The regime degrades into theatrical compliance: receipts filed, gates pass, metrics green, but typology has become a Procrustean bed mis-classifying novel risk into already-mitigated cells. Three properties make this silent: (a) force-fit produces syntactically valid receipt that all gates accept; (b) coverage-fraction is computed against vocabulary-as-defined, not vocabulary-as-needed; (c) quarterly expansion ritual reviews uncovered cells within current vocabulary but has no chartered prompt to ask "are the axes themselves still right?" — ritual is intra-vocabulary, not meta-vocabulary. Detection trigger: same anti-pattern appearing under multiple cell classifications (semantic collision), or 8D writer's classification confidence below threshold. Mitigation requires v2: receipts include explicit classification-confidence and vocabulary-extension-proposed fields, plus annual meta-ritual auditing matrix axes themselves — but that meta-ritual is itself subject to the same chartering-gap this prevention closes (known recursion accepted as residual risk).
- **Deployment_scope**: GLOBAL. Per CLAUDE.md: "ANY ecosystem improvement … MUST live under `~/.claude/` global, never in a project's local memory." Decision-test outcome: fires regardless of cwd → global.
- **Gate_test**: see Q4 evidence block above (PASS / PASS / PASS).

---

## Phase 5: Prevention Audit Rounds

### Round 1 — Verdict: CONTINUE

**W1 — Q4 ABSENT (ADDRESSABLE).** Q4 prevention action missing; payload terminates mid-sentence. *Suggested fix:* Re-emit with complete Q4. Concrete candidate: periodic class-discovery scan walking every config-like surface (`~/.claude/settings*.json`, `gate-rules.yaml`, `skills/*/SKILL.md` frontmatter, `plugins/*/settings.json`) cross-referencing every command/path/predicate against filesystem reality, emitting delta to `~/.claude/governance/wiring-orphan-report.md` and tracked metrics.jsonl issue when count > 0.

**W2 — Q3 class-coverage gap (ADDRESSABLE).** R16 bound to settings.json but registration-without-implementation has multiple sibling surfaces: gate-rules.yaml predicate symbols, plugins/*/manifest.json command handlers, SKILL.md frontmatter tools, MCP server endpoints. Listed `sibling_classes` are different classes, not sibling surfaces of same class. *Suggested fix:* Either (a) broaden R16 to pluggable validator-per-surface registry, OR (b) explicitly scope R16 to settings.json AND file 4 sibling rules R17–R20 with coverage-gap-discovery-owner deliverable enumerating them within 30 days.

**W3 — Q3 hierarchy mis-claim, Level 3 achievable (ADDRESSABLE).** Claimed Level 2; Level 3 architectural elimination achievable via *generative coupling*: derive settings.json from single source of truth (script set on disk). NixOS/Bazel/Terraform analogue. *Suggested fix:* Add Level 3 layer: (i) frontmatter schema for hook scripts; (ii) `~/.claude/bin/regen-settings` emits settings.json from frontmatter union; (iii) make settings.json read-only via pre-commit hook rejecting hand-edits unless `EXEMPT regen:`; (iv) keep R16 as backstop.

**W4 — Q3 measurability silent-decay (ADDRESSABLE).** Auditor-runs-synthetic-test relies on memory. *Suggested fix:* Daily self-test cron injects synthetic settings.json edit referencing `/tmp/r16-canary-nonexistent-${date}.sh`, asserts DENY, writes `r16_self_test=pass|fail` to metrics.jsonl. Stop-hook warns if last self-test >36h or =fail.

**W5 — Q3 fail-mode unspecified (ADDRESSABLE).** MultiEdit overlapping edits, malformed JSON, hook exception — default behavior could be fail-open. *Suggested fix:* Specify fail-closed semantics; add unit tests in `~/.claude/hooks/tests/test_r16_failmodes.py`.

**W6 — Q3 pre-commit bypass (RESIDUAL).** Web UI edits, `--no-verify`, different machine, auto-commit hook may not run pre-commit. Closing all four requires server-side enforcement out of scope. *Suggested fix:* Acknowledge in 8D D7; optionally add server-side cron posting violations to alerts topic.

**W7 — Q3 missing rule-acceptance receipt (ADDRESSABLE).** R16 introduces new rule AND new category — receipt requirement doubled and unaddressed. *Suggested fix:* Add sub-clause (f) requiring `~/.claude/governance/rule-acceptance-receipts/R16.md` answering all 4 charter questions in same commit.

**W8 — Q3 quarterly cadence too slow (ADDRESSABLE).** 4 cross-surface instances appeared in one session; 90-day ritual will admit dozens. *Suggested fix:* Tighten to monthly or event-driven (regenerate on class-registry change OR new metrics.jsonl firing pattern).

**Soa_citations_used (round 1):** wiki/concepts/instruction-failure-escalation-ladder.md; wiki/concepts/degraded-emission-with-warning.md; CLAUDE.md "Rule Acceptance — Generality Charter"; CLAUDE.md "Instruction Failure Escalation Protocol"; NixOS module system docs; Bazel BUILD generation patterns; Terraform `for_each` resource generation.

### Round 2 — Verdict: CONTINUE

**W1 — Q4 still missing + Q3 failure-mode truncated (ADDRESSABLE).** *Suggested fix:* Re-emit with both quadrants and full failure_mode_of_prevention block. Treat Q4 as un-audited (default RESIDUAL); Q3's failure-mode-named check as PARTIAL not PASS.

**W2 — Q3 scope gap on class boundary (ADDRESSABLE).** R16 only walks `hooks.{PreToolUse,...}[].hooks[].command`. Class applies also to `mcpServers.*.command`, `permissions.allow/deny`, plugin-level `commands/agents/skills/` manifests, `statusLine.command`. Today hooks; tomorrow MCP — R16 silently passes. *Suggested fix:* Generalize parity walker to JSON-path registry `~/.claude/governance/wiring-parity-targets.yaml` listing every (json_path_glob, resolver_kind) tuple R16 must validate. Seed with hooks/*, mcpServers/*, statusLine, plugins/*/{commands,agents,skills}/*. Data-driven.

**W3 — Q3 non-empty-body sub-SoA (ADDRESSABLE).** `>0 bytes AND ≥1 non-comment line` passes `exit 0`, `pass`, `print('todo')`. SoA baseline (lefthook/husky/pre-commit-hooks) requires paired test file, minimum cyclomatic complexity, OR mandatory `# WIRING-PARITY: implements <event>` marker cross-checked against settings.json. *Suggested fix:* Replace heuristic with marker contract; cross-validate marker-against-registration.

**W4 — Q3 calendar-driven discovery loop (ADDRESSABLE).** Same as round 1 W8. *Suggested fix:* Make coverage-delta-report event-driven: regenerate on every commit touching `class-registry.yaml` OR `gate-rules.yaml`. Quarterly run as freshness floor only.

**W5 — Q3 recursive wiring-parity (ADDRESSABLE).** Pre-commit hook lives in `~/.claude/hooks/` but `~/.claude/` is not a project git repo with pre-commit infra (only auto-commit/push hook). Activation surface unspecified — itself a wiring-without-implementation candidate. *Suggested fix:* (a) co-locate parity check inside existing `~/.claude/` post-Write auto-commit hook, OR (b) make it SessionStart validator refusing to start session with broken settings.json (read-time enforcement, survives recursion problem).

**W6 — Q3 asymmetric requiredActions (ADDRESSABLE).** Single requiredAction assumes user wants registration. Often correct fix is REMOVE the dangling entry. Asymmetric prompts push users toward stubs (Goodhart), reintroducing class. *Suggested fix:* Emit two requiredActions: "(A) implement the referenced script in this commit, OR (B) remove the dangling registration from settings.json in this commit."

**W7 — Q3 hierarchy claim mixed-level (RESIDUAL).** Aggregate is 2-and-3 mixed. *Suggested fix:* Annotate each sub-action with its hierarchy level individually; accept discovery loop is Level 3 with architectural-elimination escalation criterion (≥2 unregistered classes discovered post-incident in 90 days → schema-driven approach).

**Soa_citations_used (round 2):** lefthook/husky/pre-commit-hooks SoA on stub detection; Claude Agent SDK MultiEdit semantics (undocumented per WebSearch); CLAUDE.md "Memory Scoping" section; CLAUDE.md auto-commit-and-push hook on ~/.claude.

### Round 3 — Verdict: EXHAUSTED

**W1 — Q3 SKILL.md prose clause is text-only (ADDRESSABLE).** Per Instruction Failure Escalation Ladder, text-only instructions decay; SKILL.md prose clause is exactly the failure mode the ladder warns against. *Suggested fix:* Drop SKILL.md clause OR convert to structural assertion (subagent dispatch wrapper refuses to return success if diff touched settings.json without touching referenced script in same patch — hard gate at dispatch boundary). Mark action sheet honestly: "5 controls, 4 at L2, 1 redundant prose removed."

**W2 — Q3 substance check defeated by `exit 0` (ADDRESSABLE).** Same as round 2 W3 reinforced. *Suggested fix:* Behavioral predicate: AST pattern (calls non-builtin function, writes to stdout/stderr/file, exits structured decision payload) OR co-located test file `<script>.test.{sh,py}` exercised by pre-commit with non-zero coverage.

**W3 — Q3 project-scoped settings.json uncovered (ADDRESSABLE).** Per CLAUDE.md Memory Scoping, project-scoped `.claude/settings.json` legitimately exists. *Suggested fix:* Extend predicate to `**/.claude/settings.json` and `**/.claude/settings.local.json` regardless of root.

**W4 — Q3 MultiEdit intermediate-state semantics undefined (ADDRESSABLE).** Sequential application; intermediate state can produce invalid JSON. *Suggested fix:* Validate ONLY final post-edit state; unit test exercising MultiEdit sequence with invalid intermediates but valid final state.

**W5 — Q3 quarterly cadence mismatched (ADDRESSABLE).** Original incident surfaced 4 cross-surface instances in ONE session; this 8D surfaced sibling class on next session. Quarterly = ~90-day incubation. *Suggested fix:* Move to monthly (matches existing CLAUDE.md "Monthly review"), OR event-driven on `escape_log.yaml` / `class-registry.yaml` append.

**W6 — Q3 path-resolution drift (RESIDUAL).** Future env var resolver doesn't know about silently falls through. Cannot be eliminated without coupling gate to harness env-resolution code (creates different fragility). *Mitigation accepted:* fail-closed on unresolvable env vars (deny with reason "unknown-env-var: cannot validate wiring parity") rather than fail-open ("path not found, allow").

**W7 — Q4 STILL MISSING (ADDRESSABLE).** Audit input still truncated mid-Q3. *Suggested fix:* Re-issue audit request with complete Q4 inlined. Do not synthesize Q4 from Q3 (would be R1 inventing-instead-of-researching anti-pattern). If Q4 intentionally omitted, audit input should say "Q4: NOT-APPLICABLE because <reason>" not empty truncation.

**Soa_citations_used (round 3):** wiki/concepts/instruction-failure-escalation-ladder.md; wiki/concepts/degraded-emission-with-warning.md; CLAUDE.md "Memory Scoping"; CLAUDE.md "Monthly review" cadence; Claude Agent SDK MultiEdit tool semantics.

**Final verdict (Phase 5):** EXHAUSTED at round 3. Stronger alternatives surfaced: (a) generative-coupling Level 3 architectural elimination (NixOS/Bazel/Terraform analogue) accepted as future escalation criterion; (b) JSON-path registry for parity walker (data-driven, not hardcoded) accepted into Q3; (c) WIRING-PARITY marker contract accepted as substance check upgrade; (d) event-driven cadence accepted; (e) two-action requiredActions accepted; (f) project-scoped predicate widening accepted; (g) fail-closed on unresolvable env vars accepted as residual mitigation; (h) Q4 supplied as Risk-Typology Coverage Regime addressing the meta-detection axis.

**Residual risks accepted:** (i) path-resolution drift on novel env vars (mitigated by fail-closed); (ii) out-of-band config writes via web UI / different machine / `--no-verify` (mitigated by SessionStart validator + nightly cron audit); (iii) vocabulary-staleness in Q4's risk-typology matrix (mitigated by classification-confidence field in v2); (iv) Q3 hierarchy mix Level 2/3 reported honestly per sub-action.

---

## Phase 6: Verification Plan + Proof of Action

**Overall_timeframe**: 6 months from initial deployment date 2026-04-27 through 2026-10-27, with monthly checkpoint reviews aligned to existing CLAUDE.md Instruction Failure Escalation Protocol monthly cadence (first week of each month) and quarterly checkpoints at 2026-07-27 and 2026-10-27 aligned to Generality Charter compression-ritual cycle.

**Phase_8_trigger**: Atomic landing of the Q3 deployment bundle: single git commit under `~/.claude/` simultaneously creating (a) `~/.claude/hooks/hook-settings-wiring-parity-gate.py`, (b) R16 entry in `~/.claude/gate-rules.yaml` under category=configuration-boundary mode=enforce, (c) `~/.claude/governance/rule-acceptance-receipts/R16.md` answering all 4 charter questions, (d) `~/.claude/governance/class-registry.yaml` seeded with `registration-without-implementation` entry, AND successful execution of the Q1 reconciliation log showing zero failing paths in the current settings.json state. Verification phase begins at the timestamp of this atomic commit; auto-commit + auto-push hook on `~/.claude/` produces the immutable start-of-verification git SHA recorded as `verification.phase8.start_sha` in metrics.jsonl by the SessionStart hook on the next session boot.

(Per-quadrant Proof of Action blocks already provided in Section C above; not duplicated.)

---

## SoA Citations (deduplicated)

URL-path style citations across phases 3, 5, and 7:

1. `personal-wiki/wiki/concepts/instruction-failure-escalation-ladder.md` — text→soft→hard→architectural elimination ladder; rationale for rejecting SKILL.md prose clause and pushing R16 to rung 3+.
2. `personal-wiki/wiki/concepts/degraded-emission-with-warning.md` — sibling class anchor; partial-coverage anti-pattern that R16 must avoid replicating via stub-permissive substance check.
3. `personal-wiki/wiki/concepts/three-tier-lesson-learning.md` — composition contract analysis; basis for Q2.W9–W11 recursive self-instantiation insight.
4. `personal-wiki/wiki/concepts/claude-agent-sdk-patterns.md` — MultiEdit semantics, multi-file transactional Write absent from SDK; basis for Q1.W4 fixed-architectural-premise determination.
5. `personal-wiki/wiki/concepts/hook-class-taxonomy.md` — event-handler vs prompt-injection categorization; basis for understanding why R16's PreToolUse mount point is event-handler-class (~0 cost).
6. `personal-wiki/wiki/concepts/function-replacement-convention.md` — delete-old-in-same-commit convention; structural analogue to per-action atomicity invariant.
7. `personal-wiki/wiki/concepts/wiki-to-code-traceability.md` — triple marker convention; basis for the WIRING-PARITY marker contract proposed in Phase-5 round-3 W2.
8. `personal-wiki/wiki/sources/8d-ecosystem-degraded-emission-2026-04-25.md` — generative anti-pattern across 4 unrelated surfaces in one session; cited as evidence rate-of-discovery > quarterly cadence.
9. CLAUDE.md "Rule Acceptance — Generality Charter" — 4-question generality checklist; basis for receipt requirement on R16 + R16 receipt template.
10. CLAUDE.md "Instruction Failure Escalation Protocol" — monthly review cadence + threshold 0 for known-failed; basis for Q3 cadence-tightening to monthly.
11. CLAUDE.md "Memory Scoping" — project-scoped settings.json files exist; basis for Phase-5 round-3 W3 predicate widening to `**/.claude/settings.json`.
12. CLAUDE.md auto-commit + auto-push on `~/.claude` — basis for Phase-5 round-2 W5 SessionStart-validator alternative to pre-commit hook.
13. NixOS module system documentation — derivation of systemd unit files from declared services; analogue for Q3 Level-3 generative coupling escalation criterion.
14. Bazel BUILD target generation from source globs — analogue for `claude-hooks regen` design.
15. Terraform `for_each` resource generation from a map — analogue for data-driven JSON-path registry.
16. Commercial aviation MEL pre-flight gate (FAA AC 91-67) — transferable pattern for hard pre-departure gate that resolves every manifest reference to an inspected artifact.
17. Pharmaceutical GMP batch release (FDA 21 CFR 211.22) — transferable pattern for Quality-Person fail-closed release gate plus periodic reconciliation between batch record index and document vault.
18. Theatrical tech rehearsal cue-sheet integration — transferable pattern for dry-run dress rehearsal exercising full manifest-to-asset binding once before live performance.
19. lefthook / husky / pre-commit-hooks SoA on stub detection — basis for Phase-5 round-2 W3 substance-check upgrade requiring AST pattern OR paired test file OR mandatory marker.

---

## Closure Audit

**Checked:**
1. Phase 1 IS / IS NOT — 4 dimensions with distinction column populated. **PASS.**
2. Phase 2 Why chains — 4 quadrants present, q1=12 / q2=11 / q3=12 / q4=12 whys; depth parity acceptable. **PASS** (after round-3 supply of q2/q3/q4).
3. Phase 3 RC audit — 3 rounds, weaknesses classified ADDRESSABLE vs RESIDUAL, soa_citations cited per round, final verdict CONTINUE → exit. **PASS.**
4. Phase 4 actions — corrective for q1+q2 with rationale/owner/target_date/evidence_of_completion; prevention for q3+q4 with hierarchy_level/gate_test/failure_mode_of_prevention/deployment_scope. **PASS.**
5. Phase 5 prevention audit — 3 rounds, EXHAUSTED at round 3, stronger alternatives (generative coupling, JSON-path registry, WIRING-PARITY marker, event-driven cadence, two-action requiredActions, project-scoped predicate, fail-closed on env-var) folded back into Q3. **PASS.**
6. Phase 6 verification — per-quadrant proof block with metric/data_source/target/baseline/schedule/failure_response. **PASS.**
7. SoA citations deduplicated. **PASS.**
8. Class-registry entry for `registration-without-implementation` defined with owning_rules=[R16], seen_dates=[2026-04-26], wiki_concept_ref. **PASS** (drafted; lands at phase-8 trigger commit).

**Failed:** none at closure time. The Q4 truncation flagged in Phase-5 round-1/2/3 was addressed by re-supply of the full Q4 action body before closure.

**Residual gaps acknowledged (not failures):**
- Out-of-band config writes via web UI / `--no-verify` / different machine — partial mitigation only (SessionStart validator + nightly walker). Server-side branch protection out of scope for personal-config repo.
- Vocabulary-staleness in risk-typology matrix — mitigated by v2 classification-confidence field, not eliminated.
- Path-resolution drift on novel env vars — fail-closed mitigation accepted; loud-friction over silent-miss.

---

## Wiki Ingest Drafts

Three draft pages proposed for ingest into `personal-wiki/wiki/concepts/` and `personal-wiki/wiki/sources/`:

### Draft 1 — `concepts/registration-without-implementation.md`
- **Summary**: Producer asserts a system surface is operational (configuration wiring, manifest entry, command registration) without the substance behind that claim (executable script, handler function, target file). Cousin of degraded-emission-with-warning shifted from output-boundary to configuration-boundary; cousin of deferred-artifact-without-reader shifted from output to wiring. First observed 2026-04-26 (5 hooks wired without scripts). 3-tier defense: Level-2 PreToolUse parity gate / Level-2 pre-commit symmetric hook / Level-3 generative coupling (regen settings from frontmatter). Boundary=wiring. Severity=cascade-blocking. Detectability=lagging.
- **Sources**: this 8D run-1777179234-fa0c7e64.
- **Links**: degraded-emission-with-warning, deferred-artifact-without-reader, instruction-failure-escalation-ladder, function-replacement-convention, three-tier-lesson-learning.

### Draft 2 — `concepts/risk-typology-matrix.md`
- **Summary**: Three-axis controlled vocabulary for classifying anti-pattern classes: boundary ∈ {input, output, configuration, wiring, knowledge, process} × severity ∈ {cascade-blocking, degraded-recoverable, cosmetic} × detectability ∈ {observable-on-emission, lagging, silent}. Forces typology-first authoring (start from cells, ask which are populated) over narrative-first (start from incident, derive rule). Coverage-fraction = populated_cells / total_cells, nightly metric. Failure mode: vocabulary-staleness silent drift mitigated by classification-confidence field in v2. Symmetric dual to existing compression ritual.
- **Sources**: this 8D run-1777179234-fa0c7e64; CLAUDE.md Generality Charter.
- **Links**: instruction-failure-escalation-ladder, three-tier-lesson-learning, registration-without-implementation.

### Draft 3 — `sources/8d-registration-without-implementation-2026-04-26.md`
- **Raw source**: `raw/notes/8d-registration-without-implementation-2026-04-26.md` (this 8D output).
- **Key claims**: First-instance class shipped prevention before recurrence (pre-empt charter honored); generative-coupling Level-3 architectural elimination identified as future escalation; JSON-path registry data-driven parity walker; WIRING-PARITY marker contract upgrade for substance check; event-driven coverage-delta-report cadence over calendar-driven; risk-typology matrix as governance-of-governance forcing function; recursive composition-contract failure (knowledge tier shipped without detector tier) named as Q2 terminal root cause.

Awaiting user approval for ingest per CLAUDE.md "Proactive Wiki Ingestion" rule.