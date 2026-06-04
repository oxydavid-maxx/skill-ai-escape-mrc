# MRC Identity Sanitize-Not-Raise Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the MRC pipeline from killing a finished run on a cosmetic identity check — replace fatal `raise` at all four identity-enforcement sites with sanitize-then-proceed, and drop the live-sibling-colliding `skill-8d-mrc` token from auto-action.

**Architecture:** Add one idempotent, token-boundary-safe `sanitize_legacy_identity()` in `validators.py`; route phase_4/5/7/9 through it; delete the raising identity path (function-replacement-convention).

**Tech Stack:** Python 3, pytest. Run python as `py -3`, tests as `py -3 -m pytest`.

---

## File Structure

- `ai_escape_mrc/validators.py` — denylist (drop `skill-8d-mrc`), `LEGACY_IDENTITY_RENAME_MAP`, new `sanitize_legacy_identity()`; remove the legacy check from `validate_phase9_plan`; delete/repurpose the raising validators after caller sweep.
- `ai_escape_mrc/phases/phase_4_actions.py`, `phase_5_prevention_audit.py`, `phase_7_report.py`, `phase_9_write_plan.py` — call `sanitize_legacy_identity()` instead of raising.
- `tests/test_identity_sanitize.py` (new) — unit tests for the sanitizer + no-raise behavior.

---

## Task 1: `sanitize_legacy_identity()` + denylist split

**Files:**
- Modify: `ai_escape_mrc/validators.py`
- Test: `tests/test_identity_sanitize.py`

- [ ] **Step 1: Write failing tests.**

```python
# tests/test_identity_sanitize.py
from ai_escape_mrc.validators import sanitize_legacy_identity, FORBIDDEN_LEGACY_IDENTITY_TERMS

def test_renames_six_tokens():
    assert sanitize_legacy_identity("run_8d and trigger_8d") == "run_ai_escape_mrc and trigger_ai_escape_mrc"
    assert sanitize_legacy_identity("see 8d-reports/x") == "see ai-escape-mrc-reports/x"
    assert sanitize_legacy_identity("pending-8d") == "pending-ai-escape-mrc"
    assert sanitize_legacy_identity("CLAUDE_EIGHTD=1") == "CLAUDE_AI_ESCAPE_MRC=1"

def test_eightd_prefix_and_bare():
    assert sanitize_legacy_identity("run eightd-closed-loop now") == "run aem-closed-loop now"
    assert sanitize_legacy_identity("the eightd tool") == "the aem tool"

def test_token_boundary_no_substring_corruption():
    # contrived word containing the substring must be untouched
    assert sanitize_legacy_identity("weightday") == "weightday"

def test_idempotent():
    once = sanitize_legacy_identity("run_8d eightd-x 8d-reports")
    assert sanitize_legacy_identity(once) == once

def test_skill_8d_mrc_not_rewritten():
    # live sibling skill reference must pass through unchanged (no rewrite)
    s = "the sibling skill skill-8d-mrc does X"
    assert sanitize_legacy_identity(s) == s

def test_skill_8d_mrc_not_in_denylist():
    assert "skill-8d-mrc" not in FORBIDDEN_LEGACY_IDENTITY_TERMS
```

Run: `py -3 -m pytest tests/test_identity_sanitize.py -v` → FAIL (no `sanitize_legacy_identity`).

- [ ] **Step 2: Implement in `validators.py`.** Drop `skill-8d-mrc` from `FORBIDDEN_LEGACY_IDENTITY_TERMS` (leaving the six). Add:

```python
import re, sys

# Ordered: prefixed/longer tokens before bare ones so partial rewrites can't happen.
LEGACY_IDENTITY_RENAME_MAP: tuple[tuple[str, str], ...] = (
    ("run_8d", "run_ai_escape_mrc"),
    ("trigger_8d", "trigger_ai_escape_mrc"),
    ("8d-reports", "ai-escape-mrc-reports"),
    ("pending-8d", "pending-ai-escape-mrc"),
    ("CLAUDE_EIGHTD", "CLAUDE_AI_ESCAPE_MRC"),
    ("eightd-", "aem-"),     # CLI prefix form, before bare 'eightd'
    ("eightd", "aem"),       # bare
)

#: Ambiguous token: names a LIVE sibling skill. Never auto-rewritten; warn only.
AMBIGUOUS_IDENTITY_TERM = "skill-8d-mrc"

def sanitize_legacy_identity(text: str) -> str:
    """Idempotently rewrite this skill's deprecated self-identity tokens to the
    active identity, on word boundaries (no substring corruption). The ambiguous
    `skill-8d-mrc` (a live sibling skill) is never rewritten — only a non-blocking
    warn is logged if present."""
    if not text:
        return text
    if AMBIGUOUS_IDENTITY_TERM in text:
        sys.stderr.write(
            f"[WARN] sanitize_legacy_identity: '{AMBIGUOUS_IDENTITY_TERM}' present; "
            "left unchanged (live sibling skill; not auto-rewritten)\n"
        )
    out = text
    for old, new in LEGACY_IDENTITY_RENAME_MAP:
        if old.endswith("-"):
            # prefix token: boundary before, literal hyphen consumed by 'old'
            out = re.sub(r"\b" + re.escape(old), new, out)
        else:
            out = re.sub(r"\b" + re.escape(old) + r"\b", new, out)
    return out
```

Run: `py -3 -m pytest tests/test_identity_sanitize.py -v` → PASS.

- [ ] **Step 3: Commit.** `git add ai_escape_mrc/validators.py tests/test_identity_sanitize.py && git commit -m "feat(validators): idempotent token-boundary sanitize_legacy_identity; drop skill-8d-mrc from denylist"`

## Task 2: Remove the raise-path (caller sweep + delete)

**Files:** Modify `ai_escape_mrc/validators.py`

- [ ] **Step 1: Sweep callers.** Run `grep -rn "validate_no_legacy_identity_terms\|validate_action_payload" ai_escape_mrc/` and list every site. Expected: phase_4, phase_5, phase_7, `validate_phase9_plan`.
- [ ] **Step 2: Remove the legacy check from `validate_phase9_plan`.** Delete the line `validate_no_legacy_identity_terms(content, artifact_name=str(plan_path))` (size + marker predicates stay). Phase 9 will sanitize before writing (Task 6).
- [ ] **Step 3: After Tasks 3–6 move every caller to `sanitize_legacy_identity`, delete `validate_no_legacy_identity_terms` and `validate_action_payload` (the raising functions).** If the sweep finds a non-pipeline caller that genuinely needs detection-without-raise, instead repurpose it to return a bool (no raise) — but do not leave any raising identity path callable from a phase.
- [ ] **Step 4: Run full suite** `py -3 -m pytest -q` and confirm no `NameError`/import errors from the deletion. Commit: `git commit -am "refactor(validators): delete raising identity path; phase_9 validator no longer checks identity"`

## Task 3: phase_4 — retry→sanitize

**Files:** Modify `ai_escape_mrc/phases/phase_4_actions.py`

- [ ] **Step 1:** In `_call_with_legacy_term_retry`, replace the `attempt == 2 → raise` fallback. On the second attempt, instead of re-raising, return `sanitize_legacy_identity`-cleaned content: serialize the result, sanitize, and (since results are dicts) re-parse or apply `sanitize_legacy_identity` to the JSON-serialized payload then `json.loads` back. Simplest correct form: sanitize the string fields by sanitizing the serialized JSON and reloading.

```python
import json
from ai_escape_mrc.validators import sanitize_legacy_identity
# ... after the retry loop, replacing the second-attempt raise:
        try:
            validate_clean(result)   # a non-raising check, or just always sanitize
            return result
        except _DirtyIdentity:
            if attempt == 2:
                cleaned = json.loads(sanitize_legacy_identity(json.dumps(result, ensure_ascii=False)))
                return cleaned
            ... # existing critique-injection retry
```

(Adapt to the actual control flow; the invariant: second attempt returns sanitized content, never raises.)
- [ ] **Step 2:** Remove the `except OutputIdentityContractError: raise` re-raise in `_corrective`/`_prevention` (no longer reachable; identity is sanitized, not raised).
- [ ] **Step 3:** Run `py -3 -m pytest tests/test_phase_4_actions.py -q`; update any test that asserted a raise to assert sanitized output instead. Commit.

## Task 4: phase_5 — retry→sanitize

**Files:** Modify `ai_escape_mrc/phases/phase_5_prevention_audit.py`

- [ ] **Step 1:** In the audit retry loop, on the second attempt replace `raise` with sanitize: `audit = json.loads(sanitize_legacy_identity(json.dumps(audit, ensure_ascii=False)))` then accept. Remove the `if attempt == 2: raise`.
- [ ] **Step 2:** Run `py -3 -m pytest tests/test_phase_5_prevention_audit.py -q`; fix any raise-asserting test. Commit.

## Task 5: phase_7 — sanitize the report

**Files:** Modify `ai_escape_mrc/phases/phase_7_report.py:51`

- [ ] **Step 1:** Replace `validate_no_legacy_identity_terms(rendered, artifact_name="report.md")` with `rendered = sanitize_legacy_identity(rendered)`. Update the import on line 11 (`validate_no_legacy_identity_terms` → `sanitize_legacy_identity`).
- [ ] **Step 2:** Run `py -3 -m pytest tests/test_phase_7_report.py -q` (if present) or import-smoke the module. Commit.

## Task 6: phase_9 — sanitize the plan

**Files:** Modify `ai_escape_mrc/phases/phase_9_write_plan.py:111-112`

- [ ] **Step 1:** Before `plan_path.write_text(plan_md, ...)`, add `plan_md = sanitize_legacy_identity(plan_md)`. Add `sanitize_legacy_identity` to the import on line 44. `validate_phase9_plan(plan_path)` stays (now size+markers only, per Task 2).
- [ ] **Step 2:** Run `py -3 -m pytest tests/test_phase_9.py -q`; update the identity-raise test to assert the plan is written + sanitized (no raise). Commit.

## Task 7: Integration test — the sota-gate death cannot recur

**Files:** `tests/test_identity_sanitize.py`

- [ ] **Step 1:** Add a test that drives `validate_phase9_plan` on a plan file containing `run_8d` after phase_9-style sanitize, asserting (a) the file is written, (b) `validate_phase9_plan` returns without raising, (c) the content reads `run_ai_escape_mrc`. And a test feeding `skill-8d-mrc` through phase_7/phase_9 sanitize asserting it is unchanged and no exception. Run, commit.

## Self-Review

- **Spec coverage:** spec §2 policy → Tasks 3-6; §2 denylist split + §3 map → Task 1; §4 delete raise-path → Task 2; §6 tests → Tasks 1,7. Covered.
- **Placeholder scan:** Task 3's code is marked "adapt to actual control flow" — the implementer must read the real `_call_with_legacy_term_retry` (already in repo) and apply the invariant (2nd attempt sanitizes, never raises). Not a TBD; an explicit adaptation instruction against existing code.
- **Type consistency:** `sanitize_legacy_identity(str)->str` used uniformly; dict payloads sanitized via JSON round-trip.
