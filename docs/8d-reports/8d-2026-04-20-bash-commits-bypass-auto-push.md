# 8D Report: Bash `git commit` Bypassed Auto-Push Hook

**Date**: 2026-04-20 (late — same day as the prior three)
**Problem**: Claude used Bash `git commit` directly in `~/.claude/` during the hook-based-governance implementation. Two commits landed locally but were never auto-pushed. User detected the gap by asking about push status.
**Criticality**: The governance system was specifically designed to prevent "new workflows bypassing checkpoints" — and Claude did exactly that while implementing the prevention. Meta-irony, fourth recurrence of same root cause class in one day.
**Related**: Prior three 2026-04-20 8Ds (text-instruction-without-wiki, online-search-inside-skill, hook-based-governance implementation)

---

## Four-Quadrant Summary

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Claude chose Bash `git commit` because commit message customization (WIKI-CONSULTED markers, multi-line structure) required flags the auto-commit hook doesn't expose | Q2: No detection mechanism exists for "commits created without the auto-commit hook path" — the gap is silent |
| **MRC** | Q3: Hook matcher scope is defined by TOOL TYPE (Write\|Edit), not by EFFECT TYPE (mutation of governed files). Bash is an unmonitored side-channel for `~/.claude/` mutations | Q4: The governance system has no end-of-session invariant check. "All `~/.claude/` local commits are pushed" is an invariant that should hold but is never verified |

---

## Phase 0: Knowledge Consulted

- Prior 8Ds this session (all 3 on text-instruction-without-gate class)
- wiki: `wiki-to-code-traceability`, `self-healing-automation`
- memory: `feedback_instructions_vs_gates`, `feedback_completion_checklist`
- `auto-commit-claude-config.sh` source read
- `settings.json` hooks section read — confirmed matcher = "Write|Edit" only
- **NEW insight from this incident**: Hook matcher = tool name, not target-file-scope. Any workflow that mutates governed files via unmatched tool (Bash, future Task tool, future MCP tool) bypasses the hook silently.

---

## Phase 1: IS/IS NOT

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Bash `git commit` in `~/.claude/` created commits without triggering auto-push | Write/Edit to `~/.claude/` files (those DO auto-push) | Tool-type discrimination: hook sees Write/Edit, not Bash |
| **WHERE** | `~/.claude/` repo — the auto-commit+auto-push exempted location | Project repos (which do NOT have auto-push anyway) | The exemption relies on hook firing; hook doesn't fire for Bash |
| **WHEN** | Today, during hook-based-governance implementation | Not the first time — any past Bash commit in `~/.claude/` had the same gap | Recurring silent gap, never detected until user asked |
| **EXTENT** | 2 commits (verification infra + gitignore update) sat local-only ~20min | All Write/Edit commits auto-pushed correctly | Scope: every Bash-triggered `~/.claude/` commit, since hook creation |

**Key distinction**: This is not a new bug — it's a permanent structural hole. The auto-commit hook has ALWAYS been Bash-blind. Nobody noticed because previous sessions mostly used Write/Edit, or the user manually pushed. The just-completed governance work happened to use Bash heavily for commit-message customization, making the gap visible.

---

## Phase 2: Four-Quadrant Why Analysis

### Q1 (TRC-NC): Why did Claude use Bash `git commit`?

1. Commit messages needed structured content (WIKI-CONSULTED/FINDING/ACTION markers, multi-paragraph why, HEREDOC formatting)
2. Auto-commit hook generates mechanical messages (`auto: update <file>`) — no way to customize
3. The only tool Claude has for custom git commit messages is Bash
4. Claude is trained to run git commands in Bash; no alternative presented itself
5. The auto-commit hook is designed for "incidental save" not "deliberate commit" — a different use case
6. No documentation/reminder tells Claude "if you want a custom commit message, use Write to touch a file + let the hook commit + amend later"
7. No tool exists that wraps "custom commit message + auto-push" into a single Claude-callable interface
8. **Root**: Claude's commit workflow has two paths (Write-triggered vs Bash-triggered) with asymmetric hook coverage, and no workflow mandates the covered path

### Q2 (TRC-ND): Why wasn't the missing push detected?

1. After Bash `git commit`, nothing checks if a push followed
2. No exit hook on Bash that watches for "git commit" pattern
3. The stop hook checks output disposition (wiki ingest, scope) but not git state
4. The canary, compliance, recurrence scripts all check hook compliance — none checks git sync state
5. No invariant "local = remote" is enforced or verified anywhere
6. User was the detection layer (asked "git push 了嗎？")
7. Session ended normally with no indicator of the gap
8. **Root**: The detection system monitors hooks but not the STATE they're supposed to produce. Auto-push is supposed to keep `~/.claude/` in sync with remote; nothing verifies the actual sync

### Q3 (MRC-NC): Why is hook matcher scope defined by tool type?

1. Claude Code's hook API takes a `matcher` field that matches tool names
2. The matcher is a technical mechanism to reduce noise (don't fire hook on every Read)
3. When auto-commit was designed, the assumption was "Claude modifies files via Write/Edit" — Bash as a file-mutation tool wasn't considered
4. The design defines "what triggers the hook" but not "what the hook is responsible for maintaining"
5. No distinction between IMPERATIVE coverage (which tools are watched) vs DECLARATIVE coverage (what effects are guaranteed)
6. The governance model for hook design is: "pick a trigger, implement handler" — no "enumerate all channels that can cause the effect"
7. When a new tool is added (future Bash-git workflow, MCP tool, Task tool), it's a new unmonitored channel by default
8. **Root**: The hook architecture is trigger-oriented (which tools) rather than effect-oriented (which file states). Any effect-level invariant (e.g., "local = remote") cannot be expressed as a single hook; it needs an end-of-work verification

### Q4 (MRC-ND): Why no end-of-session invariant check?

1. The Stop hook exists but is oriented toward conversation behavior (error-pushing, wiki ingest, completion checklist)
2. Git state is treated as a runtime concern (handled per-tool-use) not a session-end invariant
3. No "session invariant" concept exists in the governance model — no list of things that must be true when the session ends
4. Adding invariant checks to Stop hook was never specified
5. The prior 8D's "weekly recurrence check" watches commit patterns across days, but not within-session git state
6. Compliance report is monthly — too slow to catch 20-minute gaps
7. No one asked "what must be true when I hand control back to the user?" — it was implicit
8. **Root**: The governance model lacks a "session invariants" layer — a list of state-level facts that must hold at Stop, independent of which tool caused the mutation

---

## Phase 3: RC Audit (inline, pattern-consistent)

This 8D is tightly coupled to prior ones. Key new findings:

- **Trigger-oriented hooks are structurally blind to new channels.** Effect-level invariants cannot be enforced by per-tool hooks alone.
- **Bash is the universal side-channel.** Any future tool that emits shell commands (future MCP tools, new built-ins) will have the same blindness.
- **"Session invariants" is a missing architectural layer.** Without it, any per-tool-use hook leaves a silent window.

### Residual Risks
- Hook API may not support a "session invariants" concept natively — we must implement via Stop hook content inspection.
- Some invariants are expensive to check (e.g., "all tests pass") — we focus on cheap ones first (git sync state).

---

## Phase 4: Prevention Action Design

### Q1 Corrective: Push the stuck commits (already done)

Already completed: `git push` manually. Remote now in sync.

### Q2 Corrective: Add fallback Bash-git detector

Add a Bash PostToolUse hook that detects `git commit` in `~/.claude/` and runs `git push` after it.

### Q3 Prevention (MRC-NC): Effect-oriented hook coverage

**Action**: Add a Bash PostToolUse hook (`posttooluse-bash-git-autopush.sh`) that:
1. Inspects Bash command for `git commit` pattern inside `~/.claude/`
2. If detected → run `git push` from `~/.claude/`
3. Logs action to `hook-debug.log`

This extends the effect "push on commit" to cover Bash channel, not just Write/Edit.

**Gate Test**:
- Scope: PASS — covers any Bash-created commit in `~/.claude/`, not just this instance
- Persistence: PASS — hook fires automatically
- Measurability: PASS — `grep 'bash-git-autopush' hook-debug.log` audits triggers

**Prevention Hierarchy Level**: 3 (Detect before merge — right after commit, before session ends)
**Failure Mode**: Bash command with nonstandard git form (e.g., `git -c user.name="x" commit`) may not match regex. Mitigation: broad regex + fallback in Q4 invariant check.
**Deployment Scope**: GLOBAL

### Q4 Prevention (MRC-ND): Session-end invariants layer

**Action**: Extend Stop hook with invariant checks. First invariant: `~/.claude/` has no unpushed commits at session end.

**Logic**:
```bash
cd ~/.claude
UNPUSHED=$(git log origin/master..HEAD --oneline 2>/dev/null | wc -l)
if [ "$UNPUSHED" -gt 0 ]; then
    # Auto-push; if that fails, alert
    git push 2>&1 | tee -a hook-debug.log
    # Verify
    UNPUSHED2=$(git log origin/master..HEAD --oneline 2>/dev/null | wc -l)
    if [ "$UNPUSHED2" -gt 0 ]; then
        # Alert via Telegram diagnostics
        ...
    fi
fi
```

**Gate Test**:
- Scope: PASS — catches any unpushed state at session end, regardless of how it got there
- Persistence: PASS — runs on every Stop
- Measurability: PASS — hook-debug.log records every check

**Prevention Hierarchy Level**: 2-3 (catches at end; near-impossible to miss unless Stop hook fails)
**Failure Mode**: Stop hook is bypassed (Claude crashes, user kills process). Mitigation: canary test can extend to check git state daily.
**Deployment Scope**: GLOBAL

### Bonus: Update .governed-files to include skill-rules.json observation

After adding user-frustration rule, verify `.governed-files` correctly lists `skill-rules.json` as MONITORED (yes, already done).

---

## Phase 5: Prevention Audit (inline)

- **Addressable**: Regex for `git commit` in Bash should match both `git commit` and `git commit -m "..."` and variants with `--no-gpg-sign`, `--amend`, etc. Also capture path context — only act if CWD is `~/.claude/` or command contains `cd ~/.claude`.
- **Addressable**: Invariant check in Stop hook must be fast (<500ms) — otherwise slows every session end. `git log origin/master..HEAD` is local and fast.
- **Residual**: If remote auth fails during auto-push, Stop hook's auto-push retry will also fail. Alert is best we can do — user must fix auth.
- **Residual**: Stop hook doesn't fire on abnormal termination. Canary daily test mitigates.

Verdict: EXHAUSTED

---

## Phase 6: Verification Plan

| Prevention | Metric | Data | Timeframe | Success | Failure |
|-----------|--------|------|-----------|---------|---------|
| Q3 (Bash-git autopush) | Bash-created commits in `~/.claude/` always pushed within 60s | `hook-debug.log` grep for 'bash-git-autopush' | 1 month | ≥1 trigger AND zero unpushed at any Stop | Review matcher regex |
| Q4 (Session invariant) | Every session end leaves `~/.claude/` at `origin/master` | Stop hook log | 1 month | 100% of sessions show UNPUSHED=0 at end | Investigate Stop hook miss |

---

## Wiki Ingest

### Wiki Ingest: Trigger-Oriented vs Effect-Oriented Hook Design

**Target page**: `concepts/trigger-vs-effect-hooks.md` (new)
**Type**: concept

Claude Code hooks use a **matcher** field keyed to tool names (Write, Edit, Bash, etc.). This creates TRIGGER-ORIENTED coverage: the hook knows which tool fired but not which effect was produced. Any workflow that produces the same effect via a different tool bypasses the hook.

**Case**: A hook watches Write|Edit to auto-commit ~/.claude/ changes. If Claude uses Bash `git commit` directly, the commit happens but the hook never fires. The effect (new commit) is real; the coverage is missing.

**Solution layers**:
1. **Broaden trigger**: Add Bash matcher to the same hook (Q3 above). Fast but trigger-list grows forever.
2. **Effect-oriented invariant**: Check at Stop (session end) that the desired state holds, regardless of which tool caused mutations. Slow but channel-agnostic.

**Anti-pattern**: Believing "hook on Write|Edit = coverage on all file changes." Bash, Task, MCP tools can all mutate files. Each is a separate channel.

**Related**: [Wiki-to-Code Traceability](wiki-to-code-traceability.md), [Self-Healing Automation](self-healing-automation.md)

---

## Deployment Scope

| Item | Scope | Location |
|------|-------|----------|
| Q3 (Bash autopush hook) | GLOBAL | `~/.claude/hooks/posttooluse-bash-git-autopush.sh` + settings.json |
| Q4 (Stop hook invariant) | GLOBAL | Extend `~/.claude/hooks/stop-hook-self-healing-gate.sh` |
| Wiki concept page | GLOBAL | `personal-wiki/` |

---

## Meta-Observation

This is the **fourth** concurrent instance of the root cause class "text-instruction-without-gate / Claude invents workflow that bypasses gate" in a single conversation on 2026-04-20. Specifically, the failure happened **while implementing the prevention for this exact class**.

This confirms the pattern's depth: even Claude's active engagement with the prevention effort is NOT enough to stop the pattern. Only structural coverage (hooks on every channel + end-of-session invariants) will close the gap.

The user-frustration trigger rule added to `skill-rules.json` is now the meta-gate: any future frustration from the user auto-triggers 8d-mrc, ensuring we never again slide past a checkpoint silently.
