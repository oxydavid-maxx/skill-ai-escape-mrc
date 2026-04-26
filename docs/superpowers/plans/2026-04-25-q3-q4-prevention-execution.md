# Q3+Q4 Prevention Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land all 4 deferred Q3+Q4 prevention items from ecosystem 8D 2026-04-25 (R13 hook fix + Predicate-Generality charter + Q4 Discovery Function + quarterly cron) so today's degraded-emission-with-warning anti-pattern is structurally impossible at the policy-engine level.

**Architecture:** Item 1 (debug fix) unlocks PreToolUse R13 enforcement. Item 2 (governance) prevents future rule-explosion via mandatory charter + owners. Item 3 (Q4 Discovery) automates novel-pattern capture (escape_log) + cross-surface aggregation (claude-hooks discover) + Stop-hook-driven capture-or-block (escape-capture). Item 4 (cron) closes the discipline loop with calendar-enforced quarterly fresh-context audit.

**Tech Stack:** Python 3.12 (hooks, claude-hooks CLI), Bash (pre-commit + Stop hooks), YAML (charter, escape_log, gate-rules, patterns), Mermaid (no — text spec). Wires existing scaffolding: stop-hook-llm-judge.py skeleton (currently unwired per CLAUDE.md note), gate-rules.yaml v2 R13, ~/.claude/governance/{owners,escape_log,audit-r13}.

---

## File Structure

| Path | Status | Responsibility |
|---|---|---|
| `~/.claude/hooks/hook-r13-output-boundary.py` | Restore (currently `.disabled-pending-fix`) | PreToolUse R13 enforcement; UTF-8 stdin fix |
| `~/.claude/settings.json` | Modify | Re-register R13 hook in PreToolUse |
| `~/.claude/CLAUDE.md` | Modify | Add "Rule Acceptance — Generality Charter" section |
| `~/.claude/governance/rule-acceptance.md` | Create | 4-question checklist |
| `~/.claude/governance/owners.yaml` | Create | ecosystem-conformance-owner role |
| `~/.claude/governance/discovery-charter.yaml` | Create | Q4 schema (provisional rule set, concern_axes, last_audit_date) |
| `~/.claude/hooks/pre-commit-discovery-charter.sh` | Create | Block commit if charter absent/stale |
| `~/.claude/hooks/stop-hook-escape-capture.py` | Create | Detect "you missed X" patterns; block Stop until escape_log append or EXEMPT |
| `~/.claude/bin/claude-hooks` | Modify | Add `discover` subcommand |
| Cron trigger | Create via `CronCreate` | Quarterly fresh-context audit |

---

## Task 1: Fix R13 hook stdin UTF-8 encoding

**Files:**
- Modify: `~/.claude/hooks/hook-r13-output-boundary.py.disabled-pending-fix` (rename in step 3)
- Modify: `~/.claude/settings.json` (re-register in step 4)
- Test: smoke via real Edit attempt

**Bug:** `sys.stdin.read()` on Windows defaults to cp1252; Claude Code sends UTF-8 with non-ASCII content; cp1252 decode mangles → `json.loads` fails at byte ~544.

- [ ] **Step 1: Add UTF-8 stdin wrapper to hook**

Edit (or PowerShell if R8 fires) `~/.claude/hooks/hook-r13-output-boundary.py.disabled-pending-fix`. Find the `def main()` block. Replace:
```python
def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
```
with:
```python
def main() -> int:
    try:
        # Force UTF-8 on stdin — Windows default cp1252 mangles non-ASCII content
        # in Claude Code's JSON payload (smart quotes, paths with Unicode, CJK
        # in user prompts). Bug observed 2026-04-25: json.loads failed at line 1
        # col 545 in real session. Fix per ecosystem 8D Q1 corrective.
        if hasattr(sys.stdin, "buffer"):
            stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
            raw = stdin.read()
        else:
            raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
```

Add `import io` at top of file if not already there.

- [ ] **Step 2: Verify Python syntax**

Run:
```bash
py -3 -m py_compile ~/.claude/hooks/hook-r13-output-boundary.py.disabled-pending-fix
```
Expected: silent success (exit 0).

- [ ] **Step 3: Rename hook file back to active name**

```bash
mv ~/.claude/hooks/hook-r13-output-boundary.py.disabled-pending-fix ~/.claude/hooks/hook-r13-output-boundary.py
```

- [ ] **Step 4: Re-register R13 hook in settings.json PreToolUse**

Use PowerShell to insert the registration block (avoids R8 thrashing on settings.json):
```powershell
$path = "$HOME\.claude\settings.json"
$content = [IO.File]::ReadAllText($path)
$old = "            ""command"": ""py -3 ~/.claude/hooks/pretooluse-pipeline-gate.py""`n          }`n        ]`n      }`n    ],"
$new = "            ""command"": ""py -3 ~/.claude/hooks/pretooluse-pipeline-gate.py""`n          }`n        ]`n      },`n      {`n        ""matcher"": ""Write|Edit|Bash|mcp__.*"",`n        ""hooks"": [`n          {`n            ""type"": ""command"",`n            ""command"": ""py -3 ~/.claude/hooks/hook-r13-output-boundary.py""`n          }`n        ]`n      }`n    ],"
[IO.File]::WriteAllText($path, $content.Replace($old, $new))
Get-Content $path -Raw | ConvertFrom-Json | Out-Null
Write-Host "settings.json valid; R13 registered"
```

- [ ] **Step 5: Smoke test — synthetic stdin payload that previously broke**

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"echo hello — and 你好 — and an em dash"},"transcript_path":"","session_id":"test"}' | py -3 ~/.claude/hooks/hook-r13-output-boundary.py
echo "exit=$?"
```
Expected: exit=0 (no R13 patterns matched in the test payload). NO `R13 hook integrity error: stdin parse failed` message.

- [ ] **Step 6: Smoke test — pattern-match denial**

```bash
echo '{"tool_name":"Write","tool_input":{"content":"diagrams render in VS Code — view it elsewhere"},"transcript_path":"","session_id":"test"}' | py -3 ~/.claude/hooks/hook-r13-output-boundary.py
echo "exit=$?"
```
Expected: exit=2 (deny); JSON output with `permissionDecision: "deny"` and `R13 (degraded-emission-with-warning)` reason.

- [ ] **Step 7: Run audit-r13.sh expecting 6/6**

```bash
bash ~/.claude/governance/audit-r13.sh
```
Expected: `=== Result: 6/6 checks passed ===` (was 5/6 before fix).

- [ ] **Step 8: Auto-commit picks up via PostToolUse hook**

```bash
git -C ~/.claude log -2 --oneline -- hooks/hook-r13-output-boundary.py settings.json
```
Expected: 2 recent commits.

---

## Task 2: Predicate-Generality Review charter (3 files in one commit)

**Files:**
- Modify: `~/.claude/CLAUDE.md` (add new section ~25 lines)
- Create: `~/.claude/governance/rule-acceptance.md`
- Create: `~/.claude/governance/owners.yaml`

- [ ] **Step 1: Create owners.yaml**

```yaml
# Owners — accountability roles for ecosystem governance.
# Per ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) Q3 prevention.

version: 1
updated: 2026-04-25

roles:
  ecosystem-conformance-owner:
    primary: kuangyu
    deputy: null  # Reserved per Round 3 audit residual: single-owner SPOF; deputy field
                  # exists for future when a second accountable identity is available.
                  # Until then, owner == author == sole gatekeeper.
    responsibilities:
      - Reviews every new rule entering ~/.claude/gate-rules.yaml against the
        4-question checklist in ~/.claude/governance/rule-acceptance.md
      - Runs the quarterly compression ritual (walks gate-rules.yaml, answers
        "which N rules share a generative class and should be merged?")
      - Triages ~/.claude/governance/escape_log.yaml monthly
      - Signs off on rule-acceptance-receipts/<ruleid>.md when present (v2)
    rotation: null  # Quarterly rotation reserved for v2 (multi-owner)
    last_review: 2026-04-25

  discovery-owner:
    primary: kuangyu  # Same person as ecosystem-conformance-owner for now.
                      # Round 3 audit flagged this as residual ("decorative-without-capacity").
                      # Mitigation: quarterly fresh-context sub-agent does the actual
                      # discovery work (separate process = closest thing to role separation
                      # the architecture allows today).
    responsibilities:
      - Owns ~/.claude/governance/discovery-charter.yaml
      - Reviews escape_log.yaml entries quarterly
      - Approves or rejects draft rules emitted by `claude-hooks discover`
    last_review: 2026-04-25
```

Write file:
```bash
mkdir -p ~/.claude/governance
# (content above written to ~/.claude/governance/owners.yaml)
```

- [ ] **Step 2: Create rule-acceptance.md**

```markdown
# Rule Acceptance — Generality Charter

Source: ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) Q3 prevention.
Authoritative document for the rule-acceptance process; the section in
~/.claude/CLAUDE.md is a pointer to this file.

## Why this exists

Without a generality review, the policy engine's failure mode is "monotonic-
additive rule growth": every new observed instance adds a narrow rule, none
generalize, and after 6 months the engine is a bag of regex patches instead
of a principled gate. The 8D's Round 3 audit flagged this as the systemic
non-conformance root cause (Q3 quadrant). The charter is the structural
prevention.

## When this applies

Any change to ~/.claude/gate-rules.yaml that ADDS a new rule (R1..R99) or
EXTENDS an existing rule's predicate to a new pattern set MUST be accompanied
by a receipt at ~/.claude/governance/rule-acceptance-receipts/<ruleid>.md
answering all four questions below. The receipt is required before the
gate-rules.yaml edit can land. (Enforcement: hook-rule-acceptance-gate.py;
v2 — currently text-only requirement.)

## The 4 questions

Every new rule MUST answer these four questions in its receipt file:

### 1. Does this predicate cover a CLASS or only this instance?

Required content:
- Identify the generative mechanism that produced the observed instance.
- State explicitly which other instances (observed or plausible) the same
  mechanism would produce.
- If the answer is "this exact instance only," explain why broader coverage
  is impossible AND log the residual gap to escape_log.yaml.

### 2. Which existing rules R{n} could be compressed into this one?

Required content:
- List ≥1 existing rule ID that shares the generative class, OR
- Explain in ≥40 words why no existing rule applies (per Round 2 audit
  recommendation — substance-not-presence enforcement).
- The "no existing rule applies" answer is allowed but rare; default
  expectation is that NEW rules MERGE with EXISTING.

### 3. Is the surface input-boundary, process-boundary, or output-boundary?

Required content:
- One of the three surface labels exactly. If a fourth taxonomy entry is
  needed, propose it AND open a discovery-charter.yaml axis update.
- Existing labels:
  - input-boundary: user prompt content (UserPromptSubmit hooks)
  - process-boundary: tool invocation pre-conditions (PreToolUse, R1..R11)
  - output-boundary: artifact emission (R13, hook-r13-output-boundary.py)

### 4. What is the failure mode if this rule's predicate is too narrow?

Required content:
- Name the next-likely surface where the same generative mechanism could
  emerge with novel phrasing (per the four 2026-04-25 instances all using
  novel phrasing).
- State the mitigation: pattern set extensibility (externalized YAML),
  semantic detection (LLM-judge), or default-deny posture.

## Bypass

If the rule is genuinely a one-off (e.g., emergency hotfix, experimental
rule in audit mode only), include `EXEMPT charter: <reason>` in the
commit message. The bypass is logged to ~/.claude/metrics.jsonl with
the rule ID and reason; weekly digest reviews bypasses.

## Quarterly compression ritual

Once per calendar quarter, ecosystem-conformance-owner walks
~/.claude/gate-rules.yaml and answers:

> Which N rules share a generative class and should be merged into R(k)?

Output committed to ~/.claude/governance/compression-log.md as a dated
section. If no rules can be merged, the entry MUST justify why (per
audit-charter cycle).

## Anti-patterns

- **Receipt rubber-stamping** — copy-paste 4-line stock answers. Mitigation
  per Round 1 audit: substance check (≥40 words for "no existing rule"
  answer, ≥1 rule ID for the merge question).
- **Self-attested checklist** — same agent that drafted the rule writes
  the receipt. Per Round 2 audit recommendation: receipt should be
  authored by SEPARATE agent invocation (fresh context, no memory of
  drafting rationale). Currently text-only requirement; v2 enforces via
  hook-rule-acceptance-gate.py with sub-agent dispatch.
- **Monotonic addition** — each new rule lands solo without compressing.
  Mitigation: compression ritual quarterly + Question 2's required answer.

## Owner

ecosystem-conformance-owner (see ~/.claude/governance/owners.yaml).
```

- [ ] **Step 3: Add charter section to CLAUDE.md**

Edit `~/.claude/CLAUDE.md`. Add after the existing "Active Hook Rules" section (which @imports CLAUDE-rules-summary.md):

```markdown

## Rule Acceptance — Generality Charter

Any change to `~/.claude/gate-rules.yaml` that adds a new rule or extends an
existing rule to a new pattern set MUST be accompanied by a receipt answering
the 4-question generality checklist before landing. See
`~/.claude/governance/rule-acceptance.md` for the full charter.

The four questions:
1. Does this predicate cover a CLASS or only this instance?
2. Which existing rules R{n} could be compressed into this one?
3. Is the surface input-boundary / process-boundary / output-boundary?
4. What is the failure mode if this rule's predicate is too narrow?

Receipt path: `~/.claude/governance/rule-acceptance-receipts/<ruleid>.md`.
Owner: `ecosystem-conformance-owner` per `~/.claude/governance/owners.yaml`.

Bypass: include `EXEMPT charter: <reason>` in the commit message; logged
to `metrics.jsonl`; weekly digest reviews.

Quarterly compression ritual: ecosystem-conformance-owner walks
`gate-rules.yaml` and answers "which rules share a generative class and
should be merged?" — output to `~/.claude/governance/compression-log.md`.

Source: ecosystem 8D 2026-04-25 Q3 prevention.

```

- [ ] **Step 4: Verify settings + lint**

```bash
py -3 ~/.claude/hooks/validate-rules.py
```
Expected: `[validate-rules] OK`.

```bash
py -3 ~/.claude/bin/claude-hooks lint
```
Expected: exit 0.

- [ ] **Step 5: Auto-commit picks up all 3 files**

```bash
git -C ~/.claude log -1 --stat | head -20
```
Expected: commits visible touching CLAUDE.md, governance/rule-acceptance.md, governance/owners.yaml.

---

## Task 3: Q4 Discovery Function (4 sub-pieces)

**Files:**
- Create: `~/.claude/governance/discovery-charter.yaml`
- Create: `~/.claude/hooks/pre-commit-discovery-charter.sh`
- Create: `~/.claude/hooks/stop-hook-escape-capture.py`
- Modify: `~/.claude/bin/claude-hooks` (add `discover` subcommand)

### Task 3a — discovery-charter.yaml

- [ ] **Step 1: Write discovery-charter.yaml**

```yaml
# Discovery Charter — provisional rule set with required orthogonal taxonomy.
# Per ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) Q4 prevention.

version: 1
updated: 2026-04-25
discovery_owner: kuangyu  # Per ~/.claude/governance/owners.yaml
last_audit_date: 2026-04-25

# Concern axes — orthogonal dimensions that any new anti-pattern must be
# classified along. The *-emerging axis is REQUIRED per Round 3 audit
# recommendation: novel surfaces must have a default classification slot
# rather than being silently dropped.

concern_axes:
  runtime:
    - python
    - bash
    - powershell
    - mcp
    - llm
    - emerging  # Reserved for runtimes added in future

  scope:
    - per-instance
    - per-skill
    - per-project
    - ecosystem
    - emerging

  concern:
    - emission-discipline       # degraded-emission-with-warning class
    - degraded-fallback         # silent staleness, fallback-without-refusal
    - cross-surface-pattern     # same anti-pattern on multiple surfaces
    - retry-thrash              # same as R8
    - process-skip              # same as R2/R3/R4/R5
    - knowledge-gap             # same as R6/R7
    - skill-ignored             # same as R1/R9
    - scope-leak                # same as R11
    - completion-discipline     # same as R12
    - emerging                  # Reserved for novel concerns

# Provisional rules — declared as such so the charter knows itself to be
# provisional and the quarterly audit can surface "should this be promoted
# from provisional?" questions.
provisional_rules:
  - R13  # output-boundary, added 2026-04-25; PreToolUse hook to be re-wired
         # after stdin-UTF-8 fix lands

# Audit cadence
audit_cadence_days: 90
last_quarterly_audit_path: null  # Path to most recent governance/audits/discovery-audit-YYYY-Q.md
                                  # populated by the cron when it runs
```

- [ ] **Step 2: Verify YAML valid**

```bash
py -3 -c "import yaml; yaml.safe_load(open('$HOME/.claude/governance/discovery-charter.yaml'))"
echo "exit=$?"
```
Expected: exit=0.

### Task 3b — pre-commit-discovery-charter.sh

- [ ] **Step 1: Write pre-commit-discovery-charter.sh**

```bash
#!/bin/bash
# pre-commit-discovery-charter.sh
# Block commits to ~/.claude when discovery-charter.yaml is absent, missing
# required fields, or last_audit_date is older than 100 days.
# Per ecosystem 8D 2026-04-25 Q4 prevention.

set -u

CHARTER="$HOME/.claude/governance/discovery-charter.yaml"
STALE_DAYS=100
fail_count=0

say() { echo "[pre-commit-discovery-charter] $*" >&2; }

if [ ! -f "$CHARTER" ]; then
    say "FAIL: $CHARTER does not exist"
    exit 1
fi

# Check required fields
for field in "discovery_owner" "concern_axes" "last_audit_date"; do
    if ! grep -qE "^${field}:" "$CHARTER"; then
        say "FAIL: required field '$field' missing"
        fail_count=$((fail_count + 1))
    fi
done

# Check concern_axes is non-empty
axes_lines=$(awk '/^concern_axes:/,/^[a-z_]+:[^_]/{print}' "$CHARTER" | grep -cE '^\s+-')
if [ "$axes_lines" -lt 3 ]; then
    say "FAIL: concern_axes has fewer than 3 entries (got $axes_lines)"
    fail_count=$((fail_count + 1))
fi

# Check *-emerging wildcard present (per Round 3 audit)
if ! grep -q -- '- emerging' "$CHARTER"; then
    say "FAIL: concern_axes missing required '- emerging' wildcard (per Round 3 audit)"
    fail_count=$((fail_count + 1))
fi

# Check last_audit_date staleness
last_date=$(grep -E "^last_audit_date:" "$CHARTER" | sed 's/last_audit_date:[[:space:]]*//' | tr -d '"')
if [ -z "$last_date" ]; then
    say "FAIL: last_audit_date empty"
    fail_count=$((fail_count + 1))
else
    today_epoch=$(date +%s)
    last_epoch=$(date -d "$last_date" +%s 2>/dev/null || echo 0)
    if [ "$last_epoch" -gt 0 ]; then
        diff_days=$(( (today_epoch - last_epoch) / 86400 ))
        if [ "$diff_days" -gt "$STALE_DAYS" ]; then
            say "FAIL: last_audit_date is $diff_days days old (threshold $STALE_DAYS); run quarterly audit"
            fail_count=$((fail_count + 1))
        fi
    fi
fi

if [ "$fail_count" -eq 0 ]; then
    say "OK"
    exit 0
else
    say "Failed $fail_count check(s)"
    exit 1
fi
```

- [ ] **Step 2: chmod + smoke test**

```bash
chmod +x ~/.claude/hooks/pre-commit-discovery-charter.sh
bash ~/.claude/hooks/pre-commit-discovery-charter.sh
echo "exit=$?"
```
Expected: `[pre-commit-discovery-charter] OK` and exit=0.

### Task 3c — stop-hook-escape-capture.py

- [ ] **Step 1: Write stop-hook-escape-capture.py**

```python
"""Stop-hook: detect 'you missed X' / 'why didn't you' / 'again you' patterns
in user transcripts. Block Stop until escape_log.yaml has a corresponding
entry OR user prompt contains EXEMPT escape-capture: <reason>.

Per ecosystem 8D 2026-04-25 (run-1777092777-6e277c0c) Q4 prevention. Wires
the existing skeleton at ~/.claude/hooks/stop-hook-llm-judge.py.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from pathlib import Path

ESCAPE_LOG = Path.home() / ".claude" / "governance" / "escape_log.yaml"
LOG = Path.home() / ".claude" / "hooks" / "hook-debug.log"

# Conservative regex set — high precision, lower recall is acceptable here
# because false negatives just mean the user has to log the escape manually.
# False positives are more painful (block Stop unnecessarily).
ESCAPE_PATTERNS_EN = [
    r"you\s+(missed|skipped|forgot|ignored|bypass(ed)?)\s+",
    r"why\s+(didn['’]?t|wasn['’]?t|isn['’]?t)\s+(you|it|the)\s+\w+",
    r"again\s+you\s+(missed|skipped|forgot)",
    r"how\s+come\s+(you|the)\s+\w+\s+(didn['’]?t|wasn['’]?t)",
    r"(no\s+action|action\s+missing)\s+from",
]
ESCAPE_PATTERNS_ZH = [
    r"你.{0,15}(又|再次|一直).{0,15}(忘|跳過|漏|沒|忽略)",
    r"為什麼(沒|沒有|沒觸發|又)",
    r"沒有主動",
]

EXEMPT_PATTERN = re.compile(r"EXEMPT\s+escape-capture\s*:\s*([^\n]{4,200})", re.IGNORECASE)


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} stop-hook-escape-capture: {msg}\n")
    except Exception:
        pass


def find_escape_signal(transcript_path: str) -> tuple[bool, str | None, str | None]:
    """Return (matched, matching_phrase, exempt_reason).

    Scan last 50 user prompts for escape-pattern matches. Also check for
    EXEMPT escape-capture: marker.
    """
    if not transcript_path:
        return (False, None, None)
    p = Path(transcript_path)
    if not p.exists():
        return (False, None, None)

    all_patterns = [(re.compile(rx, re.IGNORECASE), rx) for rx in ESCAPE_PATTERNS_EN]
    all_patterns += [(re.compile(rx), rx) for rx in ESCAPE_PATTERNS_ZH]

    try:
        events = []
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        log(f"transcript read error: {e}")
        return (False, None, None)

    user_events = [e for e in events if e.get("type") == "user"][-50:]
    matched_phrase = None
    exempt_reason = None
    for ev in user_events:
        msg = ev.get("message", {}) or {}
        content = msg.get("content", "")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for b in content:
                if isinstance(b, dict):
                    text += b.get("text", "") or ""

        # Check exempt first
        em = EXEMPT_PATTERN.search(text)
        if em:
            exempt_reason = em.group(1).strip()

        # Check escape patterns
        if not matched_phrase:
            for compiled, rx in all_patterns:
                m = compiled.search(text)
                if m:
                    matched_phrase = m.group(0)[:200]
                    break

    return (matched_phrase is not None, matched_phrase, exempt_reason)


def has_recent_escape_log_entry() -> bool:
    """Check if escape_log.yaml was modified in the last 30 minutes — proxy for
    'user (or agent) just appended an entry in this session'."""
    if not ESCAPE_LOG.exists():
        return False
    mtime = ESCAPE_LOG.stat().st_mtime
    return (time.time() - mtime) < 30 * 60


def main() -> int:
    try:
        if hasattr(sys.stdin, "buffer"):
            stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
            raw = stdin.read()
        else:
            raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
    except Exception as e:
        log(f"stdin parse error (failing open): {e}")
        return 0  # Fail-open: Stop hooks should NEVER block on infrastructure error

    transcript_path = data.get("transcript_path", "")
    matched, phrase, exempt_reason = find_escape_signal(transcript_path)

    if not matched:
        return 0

    log(f"escape signal detected: '{phrase}'; exempt={exempt_reason!r}")

    if exempt_reason:
        log(f"EXEMPT escape-capture applied: {exempt_reason[:100]}")
        return 0

    if has_recent_escape_log_entry():
        log("recent escape_log.yaml mtime; treating as logged")
        return 0

    # Block Stop
    block_msg = (
        f"Stop hook: detected 'you missed X' / similar pattern in user transcript "
        f"(matched: {phrase!r}) but no recent ~/.claude/governance/escape_log.yaml "
        f"entry. Per ecosystem 8D 2026-04-25 Q4 prevention, this is a candidate "
        f"escape that must be logged before session end. Either: (a) append an "
        f"entry to escape_log.yaml documenting what existing rules should have "
        f"caught it, or (b) include 'EXEMPT escape-capture: <reason>' in your "
        f"prompt if this is a false positive."
    )
    print(json.dumps({"decision": "block", "reason": block_msg, "hookSpecificOutput": {"hookEventName": "Stop"}}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Syntax check**

```bash
py -3 -m py_compile ~/.claude/hooks/stop-hook-escape-capture.py
```
Expected: silent success.

- [ ] **Step 3: Smoke test — escape detected, no EXEMPT, no recent log entry → block**

This requires a synthetic transcript JSONL. Skip a unit test; integration-test it by triggering a Stop event with a known phrase (e.g., the user says "you missed X" and I attempt to end the session). If hook blocks, ✅. If not, debug the regex.

- [ ] **Step 4: Wire into settings.json Stop hooks via PowerShell**

```powershell
$path = "$HOME\.claude\settings.json"
$content = [IO.File]::ReadAllText($path)
$old = "        ""command"": ""bash ~/.claude/hooks/stop-hook-no-handoff-gate.sh""`n          }`n        ]`n      }`n    ],"
$new = "        ""command"": ""bash ~/.claude/hooks/stop-hook-no-handoff-gate.sh""`n          },`n          {`n            ""type"": ""command"",`n            ""command"": ""py -3 ~/.claude/hooks/stop-hook-escape-capture.py""`n          }`n        ]`n      }`n    ],"
[IO.File]::WriteAllText($path, $content.Replace($old, $new))
Get-Content $path -Raw | ConvertFrom-Json | Out-Null
Write-Host "stop-hook-escape-capture wired"
```

### Task 3d — claude-hooks discover subcommand

- [ ] **Step 1: Locate subcommand registration in claude-hooks**

```bash
grep -n "def cmd_" ~/.claude/bin/claude-hooks
```
Expected: list of `cmd_show`, `cmd_stats`, `cmd_lint`, `cmd_simulate`, `cmd_mode`, `cmd_promote`. The `discover` subcommand goes alongside.

- [ ] **Step 2: Add cmd_discover function and argparse subparser**

Append to `~/.claude/bin/claude-hooks` (before `if __name__ == "__main__":`):

```python
def cmd_discover(args) -> int:
    """Read escape_log.yaml + metrics.jsonl; emit draft rule when ≥2 distinct
    surfaces appear in escape_log within rolling 30-day window.
    """
    import yaml
    from collections import defaultdict

    escape_log = Path.home() / ".claude" / "governance" / "escape_log.yaml"
    if not escape_log.exists():
        print("no escape_log.yaml; nothing to discover")
        return 0
    try:
        doc = yaml.safe_load(escape_log.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"escape_log.yaml parse error: {e}", file=sys.stderr)
        return 1

    escapes = doc.get("escapes", []) or []
    cutoff_ts = time.time() - 30 * 86400
    recent = []
    from datetime import datetime
    for e in escapes:
        date_str = str(e.get("date", ""))
        try:
            ts = datetime.fromisoformat(date_str).timestamp()
        except Exception:
            continue
        if ts >= cutoff_ts:
            recent.append(e)

    # Group by surfaces
    surface_to_escapes = defaultdict(list)
    for e in recent:
        for surf in (e.get("surfaces_touched") or []):
            surface_to_escapes[surf].append(e)

    distinct_surfaces = len(surface_to_escapes)
    print(f"=== claude-hooks discover (rolling 30d, cutoff {datetime.fromtimestamp(cutoff_ts).date()}) ===")
    print(f"  total recent escapes: {len(recent)}")
    print(f"  distinct surfaces:    {distinct_surfaces}")

    if distinct_surfaces < 2:
        print("  → below threshold for draft rule emission (need ≥2 surfaces)")
        return 0

    # Cross-surface pattern: emit draft
    print()
    print("=== Draft rule (≥2 surfaces in 30d → cross-surface generative class likely) ===")
    print()
    print(f"# Draft R??? — cross-surface pattern detected from {len(recent)} escapes across {distinct_surfaces} surfaces")
    print(f"# Surfaces: {sorted(surface_to_escapes.keys())}")
    print(f"# Rule-acceptance receipt required at ~/.claude/governance/rule-acceptance-receipts/R???.md")
    print()
    print("- id: R???")
    print("  category: cross-surface-pattern  # candidate; ecosystem-conformance-owner reviews")
    print("  author: discover-cli")
    print(f"  created: {datetime.now().date()}")
    print("  owner: ecosystem-conformance-owner")
    print(f"  last_reviewed: {datetime.now().date()}")
    print("  mode: audit  # start in audit mode; promote via 'claude-hooks promote' after 7d metrics")
    print("  retirement_criteria: |")
    print("    Promote or retire after 90d of audit data + ecosystem-conformance-owner review.")
    print("  reason: |")
    print("    Cross-surface anti-pattern detected. See escape_log.yaml entries:")
    for e in recent:
        print(f"      - {e.get('id')}: {(e.get('user_phrase') or '').strip().splitlines()[0][:100]}")
    print("  trigger:")
    print("    event: PreToolUse  # candidate; refine to Stop/UserPromptSubmit per surface analysis")
    print("    tools: [Write, Edit, Bash]  # candidate; refine")
    print("  predicate:")
    print("    kind: never_satisfied  # candidate; replace with the actual generative-class predicate")
    print("  enforcement:")
    print("    deny:")
    print("      reason: '{reason}'")
    print("      required_actions:")
    print("        - 'Address the underlying generative class identified in escape_log entries above.'")
    print()
    print("=== End draft rule ===")
    print(f"Required next step: ecosystem-conformance-owner reviews + writes receipt at ")
    print(f"  ~/.claude/governance/rule-acceptance-receipts/R???.md (4-question checklist)")
    print(f"  per ~/.claude/governance/rule-acceptance.md")
    return 0
```

And in the argparse setup, add:
```python
sp = sub.add_parser("discover", help="Detect cross-surface patterns from escape_log; emit draft rule")
sp.set_defaults(func=cmd_discover)
```

- [ ] **Step 3: Smoke test discover subcommand**

```bash
py -3 ~/.claude/bin/claude-hooks discover
```
Expected: output shows 3 escapes (all from 2026-04-25), spans 3+ surfaces (today's escapes do span multiple surfaces), emits a draft rule.

---

## Task 4: Quarterly fresh-context discovery audit cron

**Files:**
- Create via `CronCreate` — no file in repo, lives in scheduling system

- [ ] **Step 1: Load CronCreate tool**

Use ToolSearch with `select:CronCreate` to load the tool schema.

- [ ] **Step 2: Create the cron trigger**

Call `CronCreate` with:
- schedule: `0 9 1 */3 *` (9am day-1 of Jan/Apr/Jul/Oct) OR equivalent every-90-day cadence
- prompt: A self-contained prompt for a fresh-context sub-agent. The prompt MUST explicitly forbid inheriting prior session context. Example body:

```
Quarterly Discovery Audit (fresh context, no prior session memory).

You are a freshly-instantiated sub-agent with NO memory of any prior
session, no access to other agents' state, and no inherited assumptions.
Your job:

1. Read ~/.claude/governance/escape_log.yaml — review every entry from
   the last 90 days. For each: what surfaces touched, what existing rules
   missed it, what was the resolution.

2. Read ~/.claude/metrics.jsonl — survey rule firing counts, decision
   distributions, EXEMPT bypass rates per rule.

3. Read ~/.claude/governance/discovery-charter.yaml. Ask yourself:
   "Are the concern_axes still complete, OR is there a NEW orthogonal
   axis that the recent 90 days of escapes/metrics suggest?" 

4. Output a report at
   ~/.claude/governance/audits/discovery-audit-{YYYY}-Q{N}.md including:
   - Summary of escapes by surface and concern
   - Proposed NEW concern axis (≥1 required) OR explicit attestation
     that the axis space is complete with reasoning
   - 3 highest-leverage rule-improvement recommendations
   - Update last_audit_date in discovery-charter.yaml to today

5. Post the audit report path + 3-line summary to the claude_daily
   Telegram diagnostics topic.

DO NOT skip step 4. An empty audit ('no new axis needed') is allowed
only with substantive reasoning explaining why the existing axes cover
the observed escapes. Default expectation: at least one new axis or
sharpening per quarter.
```

- [ ] **Step 3: Verify CronList shows the trigger**

Use `CronList` tool. Expected: new entry visible with the schedule.

---

## Self-Review

**Spec coverage:**
- ✅ Item 1: Tasks 1.1–1.8 cover R13 hook UTF-8 fix + re-register + smoke test + audit
- ✅ Item 2: Tasks 2.1–2.5 cover all 3 required files + lint + auto-commit
- ✅ Item 3a–3d: Tasks 3.1–3.5 cover charter + pre-commit + Stop hook + claude-hooks discover
- ✅ Item 4: Tasks 4.1–4.3 cover CronCreate + verify
- Spec out-of-scope items (LLM-judge tuning beyond v1, hook-rule-acceptance-gate.py, inverted MCP filter) confirmed not in plan

**Placeholder scan:**
- "TBD" / "TODO" / "implement later" — none in plan steps. The plan does mention the spec's "v2 enhancement" deferrals; those are spec-acknowledged out-of-scope, not plan placeholders.

**Type/path consistency:**
- Hook file paths consistent across tasks
- escape_log.yaml referenced consistently as `~/.claude/governance/escape_log.yaml`
- discovery-charter.yaml referenced consistently
- claude-hooks subcommand `discover` consistent

**Plan complete and saved to `D:/D-claude/skills/skill-8d-mrc/docs/superpowers/plans/2026-04-25-q3-q4-prevention-execution.md`.**
