# 8D Report: "Search Online First" Rule Failed Inside a Skill's Own Checklist

**Date**: 2026-04-20
**Problem**: Claude failed to search online before proposing Q5 workflow enforcement design — reinvented a naive "file size heuristic" that would have been caught by a 2-minute web search. User had to explicitly remind. Community's proven solution (UserPromptSubmit hook + skill-rules.json, 84% success rate) was completely bypassed.
**Critical context**: This failure occurred INSIDE the 8d-mrc skill execution. The skill's Phase 0 explicitly lists "Should I search online for how others solve this?" as a required consideration. Even that embedded reminder was ignored.
**Pattern**: Third concurrent recurrence of "text-instruction-without-gate" class in this conversation alone.
**Related**: Prior 8D (2026-04-20-text-instruction-without-wiki-consultation), P8 Consolidation

---

## Four-Quadrant Summary

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: No structural trigger forces online search when designing a solution — even skill-embedded text reminders get overridden by default execution mode under context load | Q2: No automated detection identifies "proposing a novel mechanism" vs "applying known pattern" — there's no check for "did this solution come from a search or from invention?" |
| **MRC** | Q3: The governance model has NO structural gate for "research-before-invent" — every enforcement is text-based (CLAUDE.md rule, memory entry, skill checklist item), and P8 proved text instructions have ~60% compliance, declining with context | Q4: The governance model treats skills themselves as trusted enforcement mechanisms, but skills' internal checklists are also text — skills inherit the same compliance decay as CLAUDE.md |

---

## Phase 0: Knowledge Already Consulted (this session)

- CLAUDE.md "Problem Solving" rule: "Always search online first... Pick the best 2 options with reasoning — never re-invent the wheel."
- memory: `feedback_debug_checklist.md` — 3-step mandatory checklist including wiki/search
- memory: `feedback_instructions_vs_gates.md` — text instructions fail without gates
- wiki: `wiki-to-code-traceability` — triple markers + pre-commit gate
- 8D P8 Consolidation: text ~60% compliance declining; hard gates ~100%
- **Immediate prior 8D (same conversation)**: concluded text instructions fail without gates — THIS incident is real-time proof

---

## Phase 1: IS/IS NOT

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | "Search online first" rule skipped during Q5 design — invented naive "file-size" heuristic from scratch | Code bug, failure of a tool | Behavioral compliance failure of a PROVEN rule |
| **WHERE** | Inside 8d-mrc skill execution, Phase 4 (prevention design) | Outside skills, ad-hoc conversation | The failure happened INSIDE a skill's governance, not outside |
| **WHEN** | 2026-04-20, mid-conversation, deep into a multi-step 8D + brainstorming pipeline | Session start, simple one-shot request | High context load — after 2 prior 8D phases, audit rounds, brainstorming Q1-Q4 |
| **EXTENT** | One invented heuristic almost reached implementation; user caught it | Completely fabricated code executed | Near-miss — user's reminder prevented damage |

**Critical distinction**: The failure occurred **inside a skill whose own Phase 0 lists "search online" as required**. If skill-embedded reminders can't enforce the rule, NO text-based mechanism can. This falsifies the hypothesis that "skills are stronger than CLAUDE.md" — skills' internal checklists are still text.

---

## Phase 2: Four-Quadrant Why Analysis

### Q1 (TRC-NC): Why did Claude skip online search during Q5 design?

| # | Why |
|---|-----|
| 1 | Claude proposed a file-size heuristic without running WebSearch first |
| 2 | Claude's default prevention-design mode is "invent plausible mechanism from first principles" — not "search for existing solutions" |
| 3 | The 8d-mrc skill's Phase 0 reminder ("Should I search online?") is listed as a consideration, not a mandatory tool call — it's a checklist item among many |
| 4 | After multiple rounds of RC audit, prevention design, brainstorming, Claude was in deep "producing content" mode, not "consulting external sources" mode |
| 5 | Context load was high: prior 8D phases + audit + brainstorming Q1-Q4 filled the active working memory. The "search online" reminder in the skill definition was read at Phase 0 hours earlier in the session |
| 6 | No structural trigger re-surfaces the rule at the moment of prevention design (when it's most needed) |
| 7 | Claude's architecture treats tool calls (WebSearch) as optional enrichment, not as mandatory pre-conditions for producing a design |
| 8 | **Root**: There is no chokepoint in Claude's prevention-design workflow that requires "evidence of external consultation" as an input — the workflow produces output without proof-of-research |

### Q2 (TRC-ND): Why wasn't the absence of online search detected?

| # | Why |
|---|-----|
| 1 | No automated check scanned the proposed design for signs of invention-without-research |
| 2 | No hook checks "was WebSearch or WebFetch called before Claude produced a novel design proposal?" |
| 3 | The stop hook exists but checks output disposition (wiki ingest, scope), not input research |
| 4 | The RC audit agent and prevention audit agent DO check for "Did the analyst search wiki? Memory? Online?" — but only after the design is proposed, not before |
| 5 | The audit check is itself a text instruction — the agent can skip it under similar context pressure |
| 6 | In THIS case, the audit agents were launched about ROOT CAUSES, not about PREVENTION DESIGN QUALITY. The prevention design slipped through without research audit. |
| 7 | The user became the detection layer. No automated system was watching. |
| 8 | **Root**: Detection of "invention vs research" is unstructured — it relies on auditors remembering to check, not on a structural signal (e.g., "no WebSearch call in last N turns = flag") |

### Q3 (MRC-NC): Why does the governance model allow invention-without-research?

| # | Why |
|---|-----|
| 1 | The "search online first" rule is a CLAUDE.md text instruction — Level 1 on the escalation protocol |
| 2 | The Escalation Protocol itself has failed 4+ times for this class (P8 documented), but this specific rule was never escalated |
| 3 | The rule was classified as "MONITORED" at best — never got a hard gate |
| 4 | The governance model's escalation is reactive (count failures, then act) — but failure counting for "search online first" requires someone to notice the failure, which is itself a text check |
| 5 | The research requirement is framed as a "good practice" not as a prerequisite — no action depends on its completion |
| 6 | The skills that embed the reminder (8d-mrc, brainstorming) inherit CLAUDE.md's text-enforcement model — they don't add structural gates beyond what CLAUDE.md has |
| 7 | Skill design philosophy is "guidance document" — skills give instructions but don't implement hooks. Hook creation is a separate concern |
| 8 | **Root**: The governance model has no "research-before-invent" chokepoint. Every mechanism (CLAUDE.md, memory, skill checklists, stop hook reminders) is text-based. The class "invention without research" has no structural gate anywhere in the stack |

### Q4 (MRC-ND): Why doesn't detection cover research-before-invent?

| # | Why |
|---|-----|
| 1 | The detection system's chokepoints (pre-commit hooks, stop hooks) check artifacts (code, commits) not cognitive process (did you research?) |
| 2 | Research happens inside Claude's reasoning — it's invisible to file-based hooks |
| 3 | The signal "Claude called WebSearch in last N turns" IS observable (transcript), but no hook uses this signal |
| 4 | Observing transcripts requires either (a) a stop hook that reads transcript content, or (b) a PreToolUse hook that inspects tool history |
| 5 | Stop hooks exist but are configured for output detection (completion checklist), not for input detection (research evidence) |
| 6 | PreToolUse hooks exist infrastructure-wise but are currently unused (settings.json has no PreToolUse entries) |
| 7 | The LLM-judge stop hook skeleton exists but isn't wired — it's the right mechanism for semantic checks like "did the reasoning include research?" |
| 8 | **Root**: The governance system has never operationalized "research evidence" as a detectable signal. The signal is available (transcript), the infrastructure is available (hooks), but the connection was never made |

---

## Phase 3: RC Audit (inline, pattern-consistent with prior 8D)

This is the third concurrent instance of the SAME root cause class. The pattern is established. Key findings specific to this instance:

- **NEW insight**: Skills inherit CLAUDE.md's compliance decay. Embedding a reminder in a skill checklist does NOT make it stronger than a CLAUDE.md rule. Both are text. Both fail ~60%.
- **NEW insight**: The failure occurred after multiple audit rounds. Audit agents were active in the session — yet the invention-without-research slipped through because audit focus was on root causes, not on prevention design inputs.
- **NEW insight**: Research signal (WebSearch/WebFetch tool calls) is observable in transcripts but not used as a governance signal.

### Residual Risk
- Human oversight was the detection layer. This works only as long as the user stays engaged. For autonomous tasks, this detection layer disappears.

---

## Phase 4: Prevention Action Design

### Q1 Corrective: Apply known solution now

**Action**: Replace the invented "file-size heuristic" with the community-proven UserPromptSubmit hook + skill-rules.json pattern (84% compliance per DEV article). This is what Q5 should have been from the start.

### Q2 Corrective: Audit-during-design, not after

**Action**: When prevention design enters Phase 4, require audit agent to verify research evidence BEFORE accepting the design — not after. Update `prevention_audit_agent.md` to make "did analyst search online / wiki / memory?" the FIRST check, with specific evidence (tool call IDs or URLs).

### Q3 Prevention (MRC-NC): Research-evidence chokepoint

**Proposed action**: Add a **UserPromptSubmit hook** (or a PreToolUse hook on Write/Edit when targeting design/plan documents) that:
1. Reads recent transcript (last N turns)
2. Checks for: any `WebSearch`, `WebFetch`, or wiki `Read` tool calls
3. Checks if the user's prompt contains keywords indicating novel problem-solving ("design", "propose", "implement", "solve", "設計", "解決", "做一個", "build")
4. If keywords present AND no research tool calls in recent history → inject MANDATORY instruction: "Before proposing a solution, you MUST search online or consult wiki. State: (a) what you searched, (b) top 2 existing solutions found, (c) why the chosen approach adapts them."

**Gate Test**:
- Scope: PASS — applies to CLASS (any novel-solution prompt, not just this instance)
- Persistence: PASS — hook runs on every user prompt
- Measurability: PASS — transcript audit can verify "research evidence appeared before design"

**Why Chain (abbreviated — pattern established in prior 8D)**:
1. Addresses Q3 root: creates a structural chokepoint for research-before-invent
2. Stronger alternatives: architectural elimination (require WebSearch tool call to unblock design tools) — too invasive
3. Why not eliminate: would slow down every interaction, false positives on simple questions
4. CLASS prevention: any novel-solution prompt
5. Persistence: hook-based
6. Measurable: transcript grep
7. Synergizes with existing stop hook, PreToolUse gate (prior 8D)
8. Failure mode: user disables hook, or hook-injected reminder itself gets ignored (but hook-injected context has 84% compliance per community data vs 60% for CLAUDE.md text)
9. Proven in community: umputun's Mandatory Skill Activation Hook, claudefa.st's Skill Activation Hook — same pattern
10. Most fundamental: closes the "research-before-invent" gap at the earliest possible chokepoint (user prompt submission)

**Hierarchy Level**: 2 (Detect at creation — injects MANDATORY instruction before Claude processes the request)
**Failure Mode**: Claude ignores even hook-injected MANDATORY language; false positive on simple greetings. Mitigation: use aggressive language + specific keyword list, not broad heuristics.
**Deployment Scope**: GLOBAL

### Q4 Prevention (MRC-ND): Operationalize research signal

**Proposed action**: Extend stop hook to check transcript for research evidence when the assistant output contains design/proposal/solution content. If assistant produced a design/proposal without prior WebSearch/WebFetch/wiki Read → flag in log + non-blocking reminder in next turn.

**Gate Test**:
- Scope: PASS — any design output without research evidence
- Persistence: PASS — stop hook runs on every turn
- Measurability: PASS — `grep tool_name` transcript logs

**Why Chain**:
1. Addresses Q4 root: converts research signal from invisible to observable
2. Stronger: combine with Q3 (two-layer: prompt-time + stop-time)
3. CLASS: all design outputs
4. Persistence: hook
5. Measurable: transcript audit
6. Synergy: reuses stop hook infrastructure
7. Failure mode: false positive on trivial designs. Mitigation: trigger only when output exceeds threshold (e.g., includes proposed mechanism/architecture keywords)

**Hierarchy Level**: 3 (Detect before merge — post-output, pre-commit)
**Deployment Scope**: GLOBAL

### Bonus: Audit skill-checklists for text-enforcement anti-pattern

**Finding**: Skills (8d-mrc, brainstorming, etc.) embed checklists as text. These inherit CLAUDE.md's ~60% compliance.

**Action**: Quarterly audit of skill files for "text reminder" items that should be converted to hook-triggered injections. Candidates: "search online first", "check wiki", "consult memory".

---

## Phase 5: Prevention Audit (inline, pattern-based)

This analysis is heavily pattern-consistent with the prior 8D. The additions specific to this incident are:

- **Addressable**: Gate logic for Q3 needs specific keyword list (avoid false positives on greetings)
- **Addressable**: Q4 threshold for "design output" needs definition (word count, keyword match, or both)
- **Residual**: Hook-injected MANDATORY language is still text — just higher-compliance text (84% vs 60%). Not 100%.
- **Residual**: Claude can technically call WebSearch and still not actually absorb the results. The hook only checks tool call presence, not quality of use.

---

## Phase 6: Verification Plan

| Prevention | Metric | Data | Timeframe | Success | Failure Action |
|-----------|--------|------|-----------|---------|---------------|
| Q3 (UserPromptSubmit research gate) | For novel-solution prompts, WebSearch/WebFetch/wiki-Read called before design output | Transcript grep | 3 months | ≥80% of novel-solution sessions show research before design | If <80%, strengthen keywords or add PreToolUse block |
| Q4 (stop hook research audit) | Hook logs flag designs-without-research ≥1/week | `hook-debug.log` | 3 months | Flags visible, user reviews samples quarterly | If zero flags, verify hook is active |

---

## Wiki Ingest

### Wiki Ingest: Skill-Embedded Text Reminders Inherit Compliance Decay

**Target page**: `concepts/skill-text-reminder-decay.md` (new)
**Type**: concept

Skills (prompt-engineered behavioral frameworks in Claude Code) are often assumed to enforce rules more strongly than CLAUDE.md, because they are "purpose-built" and "structured." This assumption is false.

**The core finding**: A reminder embedded as a checklist item in a skill's Phase 0 (e.g., "Should I search online?") exhibits the SAME ~60% compliance decay as a CLAUDE.md rule. The reason: both are text read once at the start of a task, then compete against content production under context load.

**Evidence**: In the 2026-04-20 incident, the 8d-mrc skill's Phase 0 explicitly lists "search online" as a required consideration. Claude was actively executing this skill. Yet during Phase 4 (prevention design), the reminder was not re-applied. Claude proposed a file-size heuristic from scratch. User intervention was the only detection.

**Why this matters**: Skills are often proposed as THE solution to behavioral compliance failures. This incident falsifies that. Skills are guidance documents — they embed the same text-enforcement model. To strengthen a behavior, skills must either:
1. Be paired with a hook that injects the reminder at the decision moment (not at skill load time)
2. Embed a synchronous tool call requirement (e.g., "Skill Phase 4 blocks unless WebSearch was called in the last 10 turns") — which requires hook infrastructure the skill itself can't provide

**Key insight**: The distinction "skill vs CLAUDE.md rule" is smaller than assumed. Both are text. Neither is structural. A hook is structural. Only hook-injected context has measurably higher compliance (84% vs 60%, per community data).

**Related**: [Behavioral Compliance Decay](concepts/behavioral-compliance-decay.md), [Instructions vs Gates](concepts/instructions-vs-gates.md), [Wiki-to-Code Traceability](concepts/wiki-to-code-traceability.md)

---

## Memory Update

Update `feedback_debug_checklist.md`:
- Add: "Step 0: If producing a design/proposal/solution, FIRST call WebSearch with query = 'how others solve <problem>'. Evidence must be in transcript before proceeding. This is a PREREQUISITE, not a consideration."
- Note: This step itself is text. Real enforcement will come from Q3/Q4 hooks (see 8D 2026-04-20 online-search-rule-failed-inside-skill).

---

## Deployment Scope

| Item | Scope | Location |
|------|-------|----------|
| Q1 (apply known solution) | Current design | Update Q5 in 8D report to use UserPromptSubmit pattern |
| Q2 (audit during design) | GLOBAL | `C:\Users\Kuangyu\.claude\skills\skill-8d-mrc\agents\prevention_audit_agent.md` |
| Q3 (research gate hook) | GLOBAL | `~/.claude/hooks/userpromptsubmit-research-gate.sh` + `~/.claude/skill-rules.json` + `settings.json` |
| Q4 (stop hook research audit) | GLOBAL | Extend `~/.claude/hooks/stop-hook-self-healing-gate.sh` |
| Skill audit | GLOBAL (quarterly) | All skills in `~/.claude/skills/` and installed plugins |
| Wiki concept page | GLOBAL | `personal-wiki/` |

---

## Pattern Observation (Meta-Finding)

**Three concurrent recurrences in ONE conversation**:

1. **First**: Added text instruction to CLAUDE.md without wiki consultation or gate (prior 8D)
2. **Second** (this one): Skipped online search during Q5 design inside an 8d skill
3. **Third** (simultaneous): The 8d-mrc skill's own reminder to "search online" did not prevent this

**Conclusion**: The "text-instruction-without-gate" class is ALREADY fully documented (P8, prior 8D, this one). The fix is not another analysis — it's implementing the prevention actions from the prior 8D + this one:

- PreToolUse hook for CLAUDE.md instruction quality (from prior 8D)
- UserPromptSubmit hook for research-before-invent (from this 8D)
- Both are hook-based (structural, 84-100% compliance), not text-based (60% declining)

**The danger of this pattern**: Each recurrence generates another text-based memory entry or CLAUDE.md rule — which itself fails. P8 documented 9 such entries. We now have 10+. The exit is NOT more text. The exit is **HOOKS IMPLEMENTED NOW**.
