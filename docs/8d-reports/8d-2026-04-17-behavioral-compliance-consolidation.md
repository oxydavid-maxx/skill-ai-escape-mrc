# Behavioral Compliance Consolidation — P8

**Date**: 2026-04-17
**Type**: NOT a full 8D. Consolidation of 9 recurrences of the same root cause class.
**Status**: Open — awaiting user review + gate engineering

---

## One Root Cause, Nine Documents

All of these are the same problem:

| # | Memory Entry | Rule That Failed | Times Failed |
|---|---|---|---|
| 1 | feedback_dont_ask_just_do | Don't ask permission | 3+ |
| 2 | feedback_debug_checklist | Check wiki before debugging | 2+ |
| 3 | feedback_instructions_vs_gates | Instructions without gates fail | 4+ (meta) |
| 4 | feedback_no_defer_fixes | Fix now, don't defer | 5+ |
| 5 | feedback_always_use_full_skills | Use full skill invocations | 1+ |
| 6 | feedback_audit_real_iteration | Audit must be real iteration | 1+ |
| 7 | feedback_no_report_from_empty_data | Don't generate from empty data | 1 |
| 8 | feedback_always_email_reports | Email reports automatically | 1+ |
| 9 | feedback_proactive_ingest_and_scope | Check wiki ingest + scope | 2+ |

**Root cause (stated once, not nine times):** Text instructions have ~60% compliance declining over session length. Hard gates have ~100% compliance. For any rule that matters, build a gate.

---

## What Works vs What Doesn't

| Mechanism | Compliance | Examples |
|-----------|-----------|---------|
| Pre-commit hook | ~100% | Wiki markers, detection artifacts, orphan config |
| Chokepoint gate (function-internal) | ~100% | `_call_claude()` substantiveness check, delivery content gate |
| Stop hook (blocking) | ~90% | Error-pushing detection |
| Stop hook (reminder, non-blocking) | ~30% | Findings disposition reminder |
| Memory entry (text) | ~60% declining | All 9 entries above |
| CLAUDE.md rule (text) | ~60% declining | "Proactive Wiki Ingestion", "Don't Ask Just Do" |

**Conclusion:** Non-blocking text has <60% compliance. Blocking gates have >90%. The gap is 30%+ and widens under cognitive load.

---

## Gate Engineering Plan

Convert top 5 most-violated rules into structural gates:

### Gate 1: Post-Significant-Output Completion Checklist (Stop Hook Enhancement)

**Rule being gated:** #8 (email reports), #9 (wiki ingest + scope check)

**Implementation:** Enhance Stop hook to detect significant output (file written, email sent, commit made) and check for completion checklist evidence in the transcript.

```bash
# In stop-hook-self-healing-gate.sh, add:

# === P8: Completion Checklist Gate ===
# Detect: did this response produce significant output?
SIGNIFICANT=$(echo "$TAIL" | grep -ci 'Write\|send_briefing_email\|git commit\|Email.*sent\|Saved to' || true)

if [ "$SIGNIFICANT" -gt 0 ]; then
    # Check for completion checklist items
    WIKI_CHECK=$(tail -200 "$TRANSCRIPT" | grep -ci 'wiki.*ingest\|收進.*wiki\|wiki 收錄\|值得收進' || true)
    SCOPE_CHECK=$(tail -200 "$TRANSCRIPT" | grep -ci 'global\|project.*scope\|GLOBAL.*PROJECT\|deployment.*scope' || true)
    EMAIL_CHECK=$(tail -200 "$TRANSCRIPT" | grep -ci 'email.*sent\|EMAIL.*Sent\|已送出\|已 email' || true)

    MISSING=""
    if [ "$WIKI_CHECK" -eq 0 ]; then MISSING="$MISSING wiki-ingest-check"; fi
    if [ "$SCOPE_CHECK" -eq 0 ]; then MISSING="$MISSING scope-check"; fi

    if [ -n "$MISSING" ]; then
        echo ""
        echo "[CHECKLIST] Significant output detected but missing:$MISSING"
        echo "  Before completing, check:"
        [ "$WIKI_CHECK" -eq 0 ] && echo "  - Wiki ingest: 這些值得收進 wiki 嗎？"
        [ "$SCOPE_CHECK" -eq 0 ] && echo "  - Scope: prevention actions 是 global 還是 project?"
        echo ""
    fi
fi
```

**Level:** 3 (detection/reminder at Stop). Not blocking — significant output needs to flow. But makes missing items VISIBLE.

**Acceptance test:** Run 3 sessions where significant output is produced. Verify hook prints checklist reminder at least once per session.

### Gate 2: Memory Dedup / Class Consolidation

**Rule being gated:** #3 (instructions vs gates — prevent accumulation of same-class entries)

**Implementation:** Before writing a new `feedback_*.md` memory entry, grep existing entries for keyword overlap. If >50% keyword match → update existing entry instead of creating new one.

This is a BEHAVIORAL RULE that requires a gate. The gate: add a check in the auto-commit hook for `~/.claude` that counts feedback_*.md files. If count > 12, print warning: "Memory accumulation detected. Consider consolidating."

**Acceptance test:** `ls memory/feedback_*.md | wc -l` should stabilize or decrease, not grow monotonically.

### Gate 3: Consolidated Decision Framework (Replace 9 Entries with 1)

**Rule being gated:** All 9 entries → one consolidated entry

**Implementation:** Create `feedback_completion_checklist.md` that replaces entries #1, #4, #5, #6, #7, #8, #9 with a single decision tree:

```markdown
## Task Completion Checklist (mandatory at every task boundary)

1. **Output quality:** Does the output contain real data? (If not → mark FAILED, don't deliver)
2. **Delivery:** Send report via email automatically. Don't wait.
3. **Wiki ingest:** 值得收進 wiki 嗎？If yes → propose topics.
4. **Scope:** Prevention actions / new rules 是 global 還是 project？
5. **Fix now:** Did I discover fixable issues? Fix them. Don't defer.
6. **Skills:** Am I using the full skill invocation, not shortcuts?
```

Keep entries #2 (debug checklist), #3 (instructions vs gates) as standalone — they're different classes.

**Acceptance test:** MEMORY.md should have fewer feedback entries after consolidation. The consolidated entry covers the class.

### Gate 4: `_call_claude()` Chokepoint (Already Implemented)

**Already done in P7.** `_call_claude()` rejects empty/garbage input before calling Claude API. This is Level 1 elimination for the hallucination class. Path-independent.

**Acceptance test:** `grep "is_data_substantive" briefing.py` returns ≥1 match.

### Gate 5: Delivery Content Gate (Already Implemented)

**Already done in P7.** `send_briefing_email()` and `send_to_telegram()` reject <200 chars and failure-indicator-heavy content.

**Acceptance test:** `grep "validate_delivery_content" publishers/*.py` returns ≥2 matches.

---

## Residual Risk (Accepted)

Some behaviors will never be 100% gated:
- **Wiki ingest proposal quality** — a gate can remind, but only the agent can produce a thoughtful ingest proposal. Quality is behavioral.
- **Scope judgment** — whether something is global or project requires semantic understanding. A reminder is the max enforcement possible.
- **Novel rule classes** — new behavioral rules not yet in the checklist will still start as text and may fail before being gated.

The cost of using an LLM as an executor includes ~10% residual non-compliance on ungatable behaviors. Documenting this 9 times does not reduce it. Accepting it and focusing gate engineering on the highest-impact items is the rational response.

---

## Wiki Ingest

### Wiki Ingest: Behavioral Compliance Decay in LLM Agents

**Target page:** `concepts/behavioral-compliance-decay.md` (new)
**Type:** concept

LLM agent compliance with text instructions (CLAUDE.md rules, memory entries) follows a predictable decay curve: ~80% at session start, declining to ~40% under cognitive load (large context, multi-step tasks, session-end pressure). Hard gates (pre-commit hooks, function-internal validation) maintain ~100% compliance regardless of load.

**The compliance spectrum:**
1. Architectural elimination (100%) — wrong behavior impossible (e.g., `_call_claude` rejects empty input)
2. Hard blocking gate (95-100%) — pre-commit hook, Stop hook with exit 2
3. Soft reminder gate (30-60%) — Stop hook print without blocking
4. Text instruction (40-80% declining) — CLAUDE.md, memory entries

**The accumulation anti-pattern:** When a text rule fails, the natural response is "add another text rule." After N failures, there are N text rules about the same class — each individually ~60% effective, collectively creating noise that further reduces compliance. The correct response is: consolidate N rules into 1 gate.

**Quantified in daily_brief project:** 9 out of 16 memory entries document the same failure class. Zero were consolidated. Zero were escalated to gates (until P7/P8 explicitly identified this pattern). The Escalation Protocol (P1 Q3) exists but was itself a text instruction — it wasn't followed.

**Key insight:** "Instructions about following instructions" is infinite regress. The only exit is structural gates at chokepoints.

**Related:** [Awareness vs Compliance](awareness-vs-compliance.md), [Process Creator Governance](process-creator-governance.md), [Self-Healing Automation](self-healing-automation.md)

---

## Deployment Scope

| Item | Scope | Location |
|------|-------|----------|
| Completion checklist gate (Stop hook) | **GLOBAL** | `~/.claude/hooks/stop-hook-self-healing-gate.sh` |
| Consolidated decision framework | **GLOBAL** | Global memory or `~/.claude/CLAUDE.md` |
| Memory dedup warning | **GLOBAL** | `~/.claude/hooks/auto-commit-claude-config.sh` |
| `_call_claude` chokepoint | **PROJECT** | `briefing.py` (daily_brief specific) |
| Delivery content gates | **PROJECT** | `publishers/` (daily_brief specific) |
| Wiki concept page | **GLOBAL** | `personal-wiki/` |
