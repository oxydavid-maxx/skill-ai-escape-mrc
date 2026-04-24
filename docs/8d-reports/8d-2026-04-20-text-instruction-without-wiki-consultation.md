# 8D Report: Text Instruction Added Without Wiki Consultation or Gate

**Date**: 2026-04-20
**Problem**: Claude added a text-only instruction to `~/.claude/CLAUDE.md` (Agent Task Workflow — Superpowers Pipeline) without consulting the wiki first and without pairing the instruction with an enforcement gate.
**Status**: Analysis complete — awaiting user review
**Related**: P8 Behavioral Compliance Consolidation (same root cause class)

---

## Four-Quadrant Summary

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: No quality checkpoint triggers when authoring instructions — Claude's default execution mode bypasses wiki consultation for non-code artifacts | Q2: `~/.claude/` auto-commit hook is transport-only; no quality gate checks instruction content before commit |
| **MRC** | Q3: Instruction authoring is not defined as a governed process — no requirement to classify enforcement level before deploying a new rule | Q4: Governance monitors Claude's code outputs but not Claude's self-modifications — `~/.claude/` edits are an unmonitored channel |

---

## Phase 0: Pre-Analysis — Knowledge Sources Consulted

| Source | What was found |
|--------|----------------|
| wiki: `wiki-to-code-traceability` | "Text instructions are corrective actions disguised as prevention — they've failed 4+ times." Pre-commit hook + triple markers enforce wiki consultation. |
| wiki: `self-healing-automation` | 4-layer architecture; Layer 3/4 for quality gates and escalation. Confirms gate-first design. |
| wiki: `compound-knowledge-effect` | "Errors also compound" — the instruction-vs-gates lesson was known but failed to prevent recurrence in a new domain (instruction authoring). Compound error. |
| memory: `feedback_instructions_vs_gates` | "CLAUDE.md rules and memory entries are TEXT INSTRUCTIONS — they can be ignored under cognitive pressure." Always pair with automated enforcement. |
| memory: `feedback_debug_checklist` | 3-step checklist: (1) check wiki, (2) check self-healing code, (3) verify with tools. Step 1 was violated. |
| memory: `feedback_completion_checklist` | Consolidated 7 entries: output quality, email, wiki ingest, scope, fix now, skills, audit quality |
| 8D: P8 Consolidation | Documented this exact root cause class: text instructions ~60% compliance declining. Hard gates ~100%. "Instructions about following instructions is infinite regress." |
| **Critical finding**: escalation_log | The "instructions without gates" entry is gated by "Escalation Protocol in global CLAUDE.md + this log" — which is ITSELF a text instruction. Circular gate failure. |

---

## Phase 1: IS/IS NOT Problem Definition

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Text-only instruction added to CLAUDE.md without wiki consultation or gate tag | Code bug, runtime error, incorrect logic | Behavioral compliance failure during instruction authoring |
| **WHERE** | `~/.claude/CLAUDE.md` (global config, outside pre-commit scope) | Project-level source files (which have pre-commit hooks) | Global config file — different hook infrastructure |
| **WHEN** | 2026-04-20, simple single-step task (add a section) | During complex multi-step task or debugging session | Low cognitive load — default execution mode, not load-induced decay |
| **EXTENT** | 1 instruction written without gate; 0 wiki pages consulted; user caught it | Multiple instructions drifting; automated detection | Complete protocol failure on a simple task |

**Key distinction**: This happened under LOW cognitive load. P8 documented compliance decay under load — but here the failure is NOT load-induced. Claude's default execution mode lacks deliberation checkpoints: low-load tasks get LESS scrutiny, not more, because no friction triggers reflection.

---

## Phase 2: Four-Quadrant Why Analysis

*Revised after RC Audit — 3 rounds of adversarial challenge. Rephrases removed, MRC chains cleaned, urgency bias reframed.*

### Q1 (TRC-NC): Why did Claude add a text-only instruction without wiki consultation?

| # | Why | Evidence |
|---|-----|----------|
| 1 | Claude didn't read wiki pages before making the edit | No `Read` call to wiki pages occurred before the `Edit` |
| 2 | Claude categorized "add section to CLAUDE.md" as "simple text editing" — not as "work in a wiki-documented domain" | The edit was treated as a write task, not a design task |
| 3 | The wiki consultation trigger is scoped to "source files" in project CLAUDE.md, not to global config. Editing CLAUDE.md (which documents the instructions-vs-gates protocol) didn't trigger self-referential compliance. | CLAUDE.md says "Before modifying source files, check wiki/index.md" — `~/.claude/CLAUDE.md` is not a "source file"; pre-commit hook only trains wiki habit for code |
| 4 | Claude's default execution mode lacks deliberation checkpoints — low-load tasks get LESS scrutiny because no friction triggers reflection | Under low load, Claude doesn't add deliberation; the absence of friction (no hook, no checklist) means execution mode dominates regardless of load |
| 5 | No mechanism maps "I'm adding a new behavioral instruction" → "check if wiki has guidance on instruction design" | The connection requires semantic understanding; no structural trigger exists |
| 6 | Task framing was "fulfill user request" not "produce high-quality instruction" — design triggers consultation, delivery triggers execution | The task was framed as delivery, not design |
| 7 | **Root**: The instruction-authoring process has no quality checkpoint — no mechanism triggers wiki consultation or gate classification when creating a new rule | Instruction creation is an uncontrolled, frictionless process |

### Q2 (TRC-ND): Why wasn't the missing wiki consultation caught before delivery?

| # | Why | Evidence |
|---|-----|----------|
| 1 | No automated check flagged the missing consultation | No hook fired during the CLAUDE.md edit |
| 2 | Pre-commit hook (wiki consultation enforcement) only covers project repos, not `~/.claude/` | `~/.claude/` uses auto-commit hook (transport), not quality gates |
| 3 | Auto-commit hook for `~/.claude/` is a TRANSPORT mechanism (commit+push), not a QUALITY mechanism | `auto-commit-claude-config.sh` doesn't validate content quality |
| 4 | Stop hook (Gate 3/P8) checks post-output disposition (wiki ingest, scope) but not pre-edit consultation — and it's non-blocking | Even if it fired, it only prints a reminder for output, not input compliance |
| 5 | No detection layer exists between "Claude decides to edit" and "edit is auto-committed" for `~/.claude/` files | The gap: plan → edit → auto-commit, zero quality checks |
| 6 | LLM-judge stop hook (semantic compliance detector) exists as skeleton but isn't wired | `stop-hook-llm-judge.py` in hooks dir but not in `settings.json` |
| 7 | User is the ONLY detection layer for instruction quality — single point of detection, no redundancy | User caught it; no automated backup |
| 8 | **Root**: Detection system covers code artifacts (project repos with pre-commit hooks) but not instruction artifacts (`~/.claude/CLAUDE.md` with transport-only hook) | Scope gap at the instruction layer |

### Q3 (MRC-NC): Why does the process allow text-only instructions without enforcement gates?

| # | Why | Evidence |
|---|-----|----------|
| 1 | Adding a new instruction to CLAUDE.md has no quality review process | Claude can add any `##` section at any escalation level without review |
| 2 | The Escalation Protocol defines levels but doesn't enforce at creation time — it's reactive (escalate after failure), not proactive (prevent weak instructions at authoring) | Protocol waits for failure, then escalates — but creation is uncontrolled |
| 3 | The Escalation Protocol is itself a text instruction — "instructions about following instructions" is infinite regress (P8 documented) | The meta-gate for instruction quality is itself an ungated instruction |
| 4 | No process requires instruction authors to classify enforcement level (`<!-- GATE: -->` or `<!-- MONITORED: -->`) before deploying a new rule | GATE tags are voluntary labels with no enforcement |
| 5 | Governance treats instruction creation as a TRUSTED operation — Claude is trusted to self-regulate instruction quality | P8 shows ~60% compliance, declining with session length |
| 6 | The cost of creating a low-quality instruction is zero (no friction, no review, no gate) — vs code which has tests, linting, hooks | Investment asymmetry: code quality >> instruction quality |
| 7 | **Root**: Instruction authoring is not defined as a governed process in the management system — there is no requirement to classify enforcement level, consult knowledge base, or obtain review before deploying a new rule | Category error: instructions treated as trivial text, not as design artifacts |

### Q4 (MRC-ND): Why doesn't the detection system cover instruction-level compliance?

| # | Why | Evidence |
|---|-----|----------|
| 1 | Detection mechanisms (pre-commit hooks, stop hooks) were designed for code changes in project repos | Pre-commit hooks check Python files; stop hook checks conversation behavior |
| 2 | `~/.claude/CLAUDE.md` is in `~/.claude/` — different repo with different hook infrastructure (auto-commit only, no quality gates) | `~/.claude/` has auto-commit + push; projects have pre-commit + stop hooks |
| 3 | Auto-commit hook for `~/.claude/` was designed for CONVENIENCE (auto-save), not QUALITY | Purpose mismatch: transport hook ≠ quality gate |
| 4 | Instruction quality was never identified as a risk category — the governance system assumed compliance is ensured by Claude's training + text instructions | This assumption has failed repeatedly (P8: 9 instances documented) |
| 5 | No simpler grep-based alternative was designed for instruction quality (grep for `<!-- GATE:` or `<!-- MONITORED:` after new `##` sections would work) | Technical gap: feasible detection never designed |
| 6 | The governance system's detection scope is "what Claude commits to code repos" — Claude's self-modifications (`~/.claude/` edits) are an unmonitored channel | Blind spot: the governance model assumes Claude is a tool that produces artifacts, not a self-configuring agent |
| 7 | **Root**: The governance model monitors Claude's outputs but does not treat Claude's self-configuration as a governed activity — `~/.claude/` has no change management process (no review, no quality gate) | Self-modification is an unmonitored, ungoverned channel |

---

## Phase 3: RC Audit Summary

**3 challenge rounds conducted by independent RC audit agent.**

### Addressed During Audit
- Q1 Why 6-7 (original): "Urgency bias from Don't Ask Just Do" contradicted low-load context → reframed as "default execution mode lacks deliberation checkpoints"
- Q1 Why 4, 9 (original): Rephrases of Why 3 → collapsed
- Q2 Why 7 (original): Rephrase of Why 5 → removed
- Q3 Why 4-5 (original): Technical observations in MRC chain → restructured as process gaps ("no requirement to classify enforcement level")
- Q4 Why 5 (original): Unsupported attributed belief → reframed as "instruction quality never identified as risk category"
- Phase 0: Added `compound-knowledge-effect` consultation (errors compound — known lesson failed to prevent recurrence in new domain)
- **Critical finding**: Escalation log entry for "instructions without gates" is gated by text instructions (Escalation Protocol + log) — circular gate failure

### Residual Risks
- Q4 root could go deeper: governance model assumes Claude is tool, not self-configuring agent → architectural redesign out of scope; current root actionable enough
- Q1 root could go deeper: bad instructions fail silently, failure attributed to execution not design → design principle to carry forward, not a gap to close now
- Alternative framing: "Claude cannot introspect on artifact type" → capability limitation of model; external gates are the correct compensating control

---

## Phase 4: Prevention Action Design

*Revised after Prevention Audit — 3 rounds of adversarial challenge. Original proposals rejected: gate logic bug, async hook can't block, Q3/Q4 identical.*

### Q1 Corrective Action (TRC-NC): Fix this instance

**Action**: Revise the "Agent Task Workflow" instruction in `~/.claude/CLAUDE.md`:
1. Add `<!-- MONITORED: escalation_pending -->` tag
2. Consult wiki (instructions-vs-gates, wiki-to-code-traceability) and apply findings to instruction design

**This fixes the immediate instance only.**

### Q2 Corrective Action (TRC-ND): Backfill existing untagged sections

**Action**: Add `<!-- GATE: -->` or `<!-- MONITORED: -->` tags to all 14 existing untagged `##` sections in `~/.claude/CLAUDE.md`. This is a prerequisite for Q3 — a gate that checks for tags is useless if 14/17 sections are already missing them.

### Q3 Prevention Action (MRC-NC): PreToolUse hook blocks ungated instructions at write time

**Proposed action**: Add a **PreToolUse synchronous hook** on Write/Edit that fires when the target is `**/CLAUDE.md`. The hook:
1. Examines the proposed content (available in `tool_input`)
2. Checks if any new `##` section lacks a `<!-- GATE: -->` or `<!-- MONITORED: -->` tag within 2 lines
3. If missing: **blocks the write** (exit 2) with a message requiring enforcement level classification

**Why PreToolUse, not auto-commit**: The prevention audit found that the auto-commit hook is async (PostToolUse, `"async": true`) — warnings are invisible to Claude and the commit proceeds regardless. A PreToolUse hook is synchronous and runs BEFORE the content reaches the file. This is Level 2 (detect at creation), not Level 4 (detect after deployment).

**Gate Test**:
- Scope: PASS — prevents the CLASS (any `##` section without gate tag, in any CLAUDE.md, in any project)
- Persistence: PASS — structural gate in `settings.json`, cannot be bypassed by cognitive pressure
- Measurability: PASS — count sections vs tags; any gap = hook is broken or bypassed

**Prevention Why Chain**:

| # | Why | Answer |
|---|-----|--------|
| 1 | Why this action? | Addresses Q3 root: instruction authoring becomes a governed process — impossible to deploy a rule without classifying its enforcement level |
| 2 | Is there a stronger action? | Architectural elimination: structured YAML/schema CLAUDE.md where each rule REQUIRES an `enforcement` field. Stronger but high migration cost. |
| 3 | Why not eliminate entirely? | CLAUDE.md is natural language by design (Claude reads it). Constraint is real. The PreToolUse hook achieves equivalent safety without format migration. |
| 4 | Prevents the CLASS or just this instance? | CLASS — any new `##` section in any CLAUDE.md, anywhere |
| 5 | Works without individual effort? | Yes — hook fires automatically, synchronously, before the write lands |
| 6 | Can a third-party auditor verify in 6 months? | Yes — count `##` sections, count `GATE`/`MONITORED` tags, compare; also check `settings.json` for hook presence |
| 7 | Conflicts with existing mechanisms? | No conflict. Synergizes: extends the GATE tag convention from voluntary to enforced. |
| 8 | Failure mode? | (a) Hook deleted from `settings.json` — mitigated by governance audit. (b) User edits CLAUDE.md outside Claude Code — acceptable, user is governance authority. (c) `<!-- MONITORED: -->` used as rubber stamp — mitigated by quarterly audit of tag quality. |
| 9 | Tried before? | PreToolUse hooks: infrastructure exists but not used for this. Pre-commit hooks for code: proven ~100% compliance (P8). Same principle, new application. |
| 10 | Most fundamental prevention? | Yes — blocks at the earliest possible point (before write), short of architectural elimination |

**Prevention Hierarchy Level**: 2 (Detect at creation — write is blocked before content reaches file)
**Failure Mode**: Hook removal from settings.json; external edit; rubber-stamp MONITORED tags. All mitigatable.
**Deployment Scope**: GLOBAL — `settings.json` hook matcher uses `**/CLAUDE.md` pattern, protecting all CLAUDE.md files.

### Q4 Prevention Action (MRC-ND): Governed file manifest for `~/.claude/`

**Proposed action**: Create `~/.claude/.governed-files` — a manifest listing authorized files in `~/.claude/` with their governance classification. The auto-commit hook validates that only listed files are committed; new files require explicit manifest entry with classification.

**Why a separate mechanism from Q3**: The prevention audit correctly identified that Q3 and Q4 must be DISTINCT. Q3 gates instruction CONTENT quality (tag enforcement). Q4 gates the CHANNEL itself — ensuring `~/.claude/` as a whole is monitored, not just CLAUDE.md.

**Manifest format**:
```
# ~/.claude/.governed-files
# Each line: <file-glob> <governance-level> <description>
CLAUDE.md          GATED         Global instruction file — PreToolUse hook enforces gate tags
settings.json      MONITORED     Hook config — changes affect all sessions
hooks/*.sh         MONITORED     Hook scripts — quality reviewed quarterly
projects/*/memory/ MONITORED     Project memory — currently unstructured
```

**Gate Test**:
- Scope: PASS — any new file or unauthorized file in `~/.claude/` is flagged, not just CLAUDE.md content
- Persistence: PASS — embedded in auto-commit hook, runs automatically
- Measurability: PASS — `diff <(git ls-files) .governed-files` reveals untracked or unclassified files

**Prevention Why Chain**:

| # | Why | Answer |
|---|-----|--------|
| 1 | Why this action? | Addresses Q4 root: `~/.claude/` becomes a governed artifact repository with explicit classification |
| 2 | Is there a stronger action? | Full schema validation for every file type in `~/.claude/`. Stronger but over-engineering for current scale. |
| 3 | Why not full schema? | `~/.claude/` contains diverse file types (JSON, Markdown, shell scripts). Per-type schema validation would be fragile and hard to maintain. The manifest is lightweight. |
| 4 | Prevents the CLASS or just this instance? | CLASS — any self-modification (new file, new hook, new memory) must be classified in the manifest |
| 5 | Works without individual effort? | Yes — auto-commit hook checks manifest automatically |
| 6 | Can a third-party auditor verify in 6 months? | Yes — compare `git ls-files` against `.governed-files` — any unlisted file = governance gap |
| 7 | Conflicts with existing mechanisms? | No — auto-commit hook already runs on every Write/Edit; this adds a validation step |
| 8 | Failure mode? | (a) Manifest itself becomes stale — mitigated by hook warning on unlisted files. (b) Auto-commit hook is async, so warnings for new files may not block — but the AWARENESS of the manifest as governance is the primary defense. |
| 9 | Tried before? | File manifests (CODEOWNERS, .gitattributes) are standard practice for governance. Applying it to `~/.claude/` is novel. |
| 10 | Most fundamental prevention? | Yes — transforms `~/.claude/` from "opaque auto-save directory" to "governed artifact repository with explicit classification" |

**Prevention Hierarchy Level**: 3 (Detect before merge — auto-commit hook validates at commit time)
**Failure Mode**: Async hook means warnings may not block Claude. Primary value is governance structure + audit trail, not real-time blocking. Blocking comes from Q3 (PreToolUse on CLAUDE.md content).
**Deployment Scope**: GLOBAL — `~/.claude/` is global infrastructure.

### Fix: Circular gate in escalation log

**Finding from RC audit**: The escalation log entry for "instructions without gates" is gated by "Escalation Protocol in global CLAUDE.md + this log" — which is itself a text instruction. Circular.

**Action**: After implementing Q3, update the escalation log entry's `gate` field to reference the PreToolUse hook. The circular reference is broken by a hard gate.

---

## Phase 5: Prevention Audit Summary

**3 challenge rounds conducted by independent prevention audit agent.**

### Critical Findings (addressed in revised Phase 4)

| # | Original Weakness | Fix Applied |
|---|-------------------|-------------|
| A1 | Gate logic bug: `grep '^+##' \| grep -v 'GATE:'` would false-positive on every section (tags on separate lines) | Replaced with PreToolUse hook that examines full proposed content, not diff lines |
| A2 | Async PostToolUse hook cannot block writes or surface warnings to Claude | Changed to synchronous PreToolUse hook (blocks BEFORE write) |
| A3 | Non-blocking warning = text instruction = known ~60% compliance | PreToolUse hook is blocking (exit 2) from day 1 |
| A4 | Q3 and Q4 were identical actions | Q3 = content gate (PreToolUse on CLAUDE.md). Q4 = channel gate (governed file manifest for `~/.claude/`) |
| A5 | Hook log has no consumer | Q3 no longer relies on logs (blocking gate). Q4 manifest enables audit-by-diff, not log review. |
| A6 | Escalation log self-reference circularity | Post-implementation: update gate field to reference PreToolUse hook |

### Residual Risks (accepted)

| # | Risk | Mitigation |
|---|------|-----------|
| R1 | User manual edits bypass all hooks | Acceptable — user is the governance authority; their edits are intentional |
| R2 | `<!-- MONITORED: -->` tag used as rubber stamp without real monitoring | Quarterly audit: verify each tag references an active hook or has a realistic escalation plan |
| R3 | Memory entries (`~/.claude/projects/*/memory/`) are unmonitored by Q3 | Future scope: extend PreToolUse hook to memory files. Current mitigation: governed-files manifest classifies them as MONITORED. |

### Verdict: EXHAUSTED — no more addressable weaknesses remain

---

## Phase 6: Verification Plan

| Prevention | Metric | Data Source | Timeframe | Success | Failure Action |
|-----------|--------|------------|-----------|---------|---------------|
| Q2 (backfill tags) | All `##` sections in `~/.claude/CLAUDE.md` have `GATE`/`MONITORED` tag | `grep -c '##' CLAUDE.md` vs `grep -c 'GATE:\|MONITORED:' CLAUDE.md` | Immediate | Count match (0 gap) | Backfill missed sections |
| Q3 (PreToolUse gate) | Write/Edit to CLAUDE.md with new `##` section without tag is BLOCKED | Intentional test: try adding a tagless section | After implementation | Write is rejected with clear message | Hook is broken or missing from settings.json — debug |
| Q4 (governed manifest) | All files in `~/.claude/` git repo are listed in `.governed-files` | `diff <(git ls-files) <(awk '{print $1}' .governed-files)` | 6 months | No unlisted files | Add missing files to manifest with classification |
| Circular gate fix | Escalation log entry references PreToolUse hook, not text instruction | `governance/escalation_log.yaml` | Immediate | `gate` field references `PreToolUse-claudemd-gate` | N/A — verify after implementation |

---

## Wiki Ingest Recommendations

### Wiki Ingest: Self-Modification Governance Gap

**Target page**: `concepts/self-modification-governance.md` (new)
**Type**: concept

LLM agents that can modify their own configuration (CLAUDE.md rules, memory entries, hook scripts) introduce a governance blind spot: the governance system monitors the agent's OUTPUTS (code, commits, reports) but not its SELF-MODIFICATIONS.

**The gap**: When Claude edits `~/.claude/CLAUDE.md`, it is simultaneously the author and the governed party. Traditional governance assumes these roles are separate (human writes rules → tool follows them). Self-modification breaks this separation. The result: unreviewed, ungated changes to the instruction set that governs ALL future behavior.

**Why it matters**: A bad code change affects one project. A bad CLAUDE.md change affects ALL projects, ALL future sessions. The blast radius of self-modification is global by definition.

**Detection pattern**: Treat `~/.claude/` as a governed artifact repository, not a convenience auto-save. Add quality gates (GATE/MONITORED tags, structural checks) to the auto-commit hook. The same patterns that work for code quality (pre-commit hooks, structural grep) work for instruction quality — they just need to be applied.

**Anti-pattern**: "Instructions about following instructions" — when the meta-rule for instruction quality is itself an ungated text instruction, you get infinite regress. The only exit is a structural gate at a chokepoint.

**Related**: [Behavioral Compliance Decay](concepts/behavioral-compliance-decay.md), [Wiki-to-Code Traceability](concepts/wiki-to-code-traceability.md), [Self-Healing Automation](concepts/self-healing-automation.md)

---

## Memory Update Recommendations

- Update `feedback_instructions_vs_gates.md`: add note about self-modification governance gap — instructions about CLAUDE.md editing are doubly dangerous (global blast radius + no gate)
- Update `escalation_log.yaml`: fix circular gate reference for "instructions without gates" entry

---

## Deployment Scope

| Item | Scope | Location |
|------|-------|----------|
| Q1 corrective (add MONITORED tag to new section) | GLOBAL | `~/.claude/CLAUDE.md` |
| Q2 corrective (backfill 14 untagged sections) | GLOBAL | `~/.claude/CLAUDE.md` |
| Q3 prevention (PreToolUse gate for CLAUDE.md writes) | GLOBAL | `~/.claude/settings.json` (PreToolUse hook) + `~/.claude/hooks/pretooluse-claudemd-gate.sh` (new) |
| Q4 prevention (governed file manifest) | GLOBAL | `~/.claude/.governed-files` (new) + `~/.claude/hooks/auto-commit-claude-config.sh` (extended) |
| Circular gate fix | GLOBAL | `governance/escalation_log.yaml` |
| Wiki concept page | GLOBAL | `personal-wiki/` |
