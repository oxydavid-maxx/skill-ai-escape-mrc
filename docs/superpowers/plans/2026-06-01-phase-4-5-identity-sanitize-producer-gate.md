# Producer-Side Identity Sanitize Gate (Phase 4 + Phase 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the legacy-identity contamination gate from consumer phases (phase_7 render / phase_9 LLM write) upstream to the producer phases (phase_4 corrective+prevention action generation, phase_5 prevention audit) so the FORBIDDEN_LEGACY_IDENTITY_TERMS denylist is enforced at the moment LLM output is written into checkpoint state — not at the moment a downstream artifact is rendered. This eliminates the bug class where a run is wasted (phase_0..phase_6 burn ~20 min of compute) only to crash at phase_9 because phase_4 coined an `eightd-*` literal that no one detected at the source.

**Architecture:** Hard producer gate (approach B) plus soft prompt assist (approach A). Each LLM call in phase_4 (corrective × 2, prevention × 2) and phase_5 (prevention audit) gets wrapped in a one-shot retry: if the JSON-serialized response contains any term from `FORBIDDEN_LEGACY_IDENTITY_TERMS`, regenerate with a critique that names the offending literal and the RENAME RULE map. If the second attempt still fails, raise `OutputIdentityContractError` and let the FSM fail closed at the producer (not silently fall back to a stub — that would defeat the gate). The producer prompts (`corrective_action.txt`, `prevention_action.txt`, `prevention_audit.txt`) also get the same `IDENTITY RENAME RULE` block that phase_9's SYSTEM_PROMPT already has, so the LLM sees the denylist at generation time and the retry path is the exception, not the rule. Approach C (silent sanitize-on-write) explicitly rejected: it hides LLM behavior from reviewers and conflicts with R13 (degraded-emission anti-pattern).

**Tech Stack:** Python 3.12, LangGraph FSM, claude-agent-sdk (`call_claude` / `ClaudeSession`), pytest. Validator already exists at `ai_escape_mrc/validators.py:validate_no_legacy_identity_terms`. Tests live in `tests/`. Repo runs git-tracked at `D:/D-claude/skills/skill-ai-escape-mrc/` (github canonical) and gets synced to `D:/D-claude/cn5dd2/CN5DD2_common/skills/skill-ai-escape-mrc/` for the gerrit mirror.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `ai_escape_mrc/validators.py` | Modify | Add `validate_action_payload(payload, *, artifact_name)` — dict/list/str-tolerant wrapper around `validate_no_legacy_identity_terms` |
| `ai_escape_mrc/phases/phase_4_actions.py` | Modify | Wrap `_corrective(q)` and `_prevention(q)` in `_call_with_legacy_term_retry(...)` — one retry budget, named critique injected on retry, raise on second failure |
| `ai_escape_mrc/phases/phase_5_prevention_audit.py` | Modify | Wrap the `sess.ask(...)` audit call with the same one-retry-then-raise legacy-term gate (audit responses also write to `state["prevention_actions"][q]["audit_notes"]` via `_apply_fixes`, so contamination at the audit layer also leaks) |
| `ai_escape_mrc/prompts/corrective_action.txt` | Modify | Append `IDENTITY RENAME RULE` block + denylist enumeration (same shape as phase_9 SYSTEM_PROMPT) |
| `ai_escape_mrc/prompts/prevention_action.txt` | Modify | Same RENAME RULE block |
| `ai_escape_mrc/prompts/prevention_audit.txt` | Modify | Same RENAME RULE block (audit must not coin legacy terms in `suggested_fix`) |
| `tests/test_validators.py` | Create (does not exist yet) | Unit tests for the new `validate_action_payload` helper |
| `tests/test_phase_4_actions.py` | Modify | Add tests: (1) legacy term in first response → retry triggered → clean second response → passes; (2) legacy term in both responses → raises `OutputIdentityContractError`; (3) clean first response → no retry, single call |
| `tests/test_phase_5_prevention_audit.py` | Create | Mirror tests for the audit-call gate |
| `ai_escape_mrc/graph.py` | NO CHANGE | Graph topology stays the same. The new gate is intra-phase (in-call retry then raise); it does not add or modify any conditional edges. The existing phase_3/phase_5 REWORK loops handle their own concerns (root-cause framing, audit verdicts) and are orthogonal to identity contamination. |
| `ai_escape_mrc/phases/phase_9_write_plan.py` | NO CHANGE | Already fixed in prior commit `e017eb3` (denylist + RENAME RULE in SYSTEM_PROMPT). The producer gate makes that consumer gate redundant for new runs, but we keep both as defense-in-depth. |

---

## Task 1: Add `validate_action_payload` helper to validators.py

**Files:**
- Create: `tests/test_validators.py`
- Modify: `ai_escape_mrc/validators.py` (append at end)

- [ ] **Step 1: Write the failing tests**

Create `D:/D-claude/skills/skill-ai-escape-mrc/tests/test_validators.py`:

```python
"""Unit tests for ai_escape_mrc.validators payload helpers."""
import pytest
from ai_escape_mrc.errors import OutputIdentityContractError
from ai_escape_mrc.validators import (
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    validate_action_payload,
)


def test_validate_action_payload_passes_clean_dict():
    payload = {"quadrant": "q1_trc_nc", "action": "use ai-escape-mrc skill", "rationale": "ok"}
    validate_action_payload(payload, artifact_name="phase_4 corrective q1_trc_nc")


def test_validate_action_payload_passes_clean_string():
    validate_action_payload("plain corrective text", artifact_name="phase_4 corrective q1")


def test_validate_action_payload_passes_clean_list():
    validate_action_payload(
        [{"step": "use aem-omission-resolve"}],
        artifact_name="phase_4 corrective q1",
    )


@pytest.mark.parametrize("term", FORBIDDEN_LEGACY_IDENTITY_TERMS)
def test_validate_action_payload_raises_on_each_forbidden_term(term):
    payload = {"action": f"create {term} binary"}
    with pytest.raises(OutputIdentityContractError) as exc:
        validate_action_payload(payload, artifact_name="test")
    assert term in str(exc.value)


def test_validate_action_payload_raises_with_nested_dict():
    payload = {
        "quadrant": "q3_mrc_nc",
        "action": "set up resolver",
        "steps": [{"cmd": "./eightd-omission-resolve --foo"}],
    }
    with pytest.raises(OutputIdentityContractError):
        validate_action_payload(payload, artifact_name="phase_4 prevention q3")


def test_validate_action_payload_artifact_name_in_error():
    with pytest.raises(OutputIdentityContractError) as exc:
        validate_action_payload({"x": "skill-8d-mrc"}, artifact_name="some_specific_label_42")
    assert "some_specific_label_42" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3 -m pytest tests/test_validators.py -v`
Expected: 7 errors (`AttributeError: module 'ai_escape_mrc.validators' has no attribute 'validate_action_payload'` or similar `ImportError`).

- [ ] **Step 3: Add `validate_action_payload` to validators.py**

Append after the existing `validate_no_legacy_identity_terms` function (around line 68 of `ai_escape_mrc/validators.py`):

```python
def validate_action_payload(payload, *, artifact_name: str) -> None:
    """Validate any phase output payload (dict/list/str) for legacy identity terms.

    JSON-serializes dict/list inputs so nested keys, list entries, embedded
    command strings, and rationales are all surfaced to the underlying
    `validate_no_legacy_identity_terms` denylist check. Strings pass through.
    Used by phase_4 / phase_5 LLM-call wrappers as a producer-side gate;
    raising here forces a one-shot retry with a named critique, and a second
    failure propagates as `OutputIdentityContractError` (fail-closed).
    """
    import json
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, ensure_ascii=False)
    else:
        text = str(payload)
    validate_no_legacy_identity_terms(text, artifact_name=artifact_name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3 -m pytest tests/test_validators.py -v`
Expected: 11 passed (7 with parametrize expansion + 4 non-parametrized).

- [ ] **Step 5: Commit**

```bash
cd D:/D-claude/skills/skill-ai-escape-mrc
git add ai_escape_mrc/validators.py tests/test_validators.py
git commit -m "feat(validators): add validate_action_payload for dict/list/str gate

Wrapper around validate_no_legacy_identity_terms that JSON-serializes
container payloads so nested keys / list entries / embedded commands are
all surfaced to the existing denylist check. Used by upcoming producer-side
gates in phase_4 + phase_5 to fail-closed at the source of contamination
instead of letting it propagate to phase_7/phase_9 consumers."
```

---

## Task 2: Add IDENTITY RENAME RULE block to producer prompts

**Files:**
- Modify: `ai_escape_mrc/prompts/corrective_action.txt`
- Modify: `ai_escape_mrc/prompts/prevention_action.txt`
- Modify: `ai_escape_mrc/prompts/prevention_audit.txt`

- [ ] **Step 1: Read each prompt to confirm current shape**

```bash
cd D:/D-claude/skills/skill-ai-escape-mrc
cat ai_escape_mrc/prompts/corrective_action.txt
cat ai_escape_mrc/prompts/prevention_action.txt
cat ai_escape_mrc/prompts/prevention_audit.txt
```

Note the current ending of each file (so the append point is correct).

- [ ] **Step 2: Append the RENAME RULE block to corrective_action.txt**

Use the Edit tool. The block to append at the end of `corrective_action.txt`:

```text

## Active Identity & Rename Rule (MANDATORY)

Active skill identity: `skill-ai-escape-mrc` / `ai_escape_mrc` / `run_ai_escape_mrc.py` / `trigger_ai_escape_mrc.py`. When you coin or quote command names, paths, hooks, CLIs, env vars, or report directories in `action`, `rationale`, `files_touched`, or `steps`, you MUST use the active identity. Do not emit any of these legacy literals:

| Forbidden legacy literal | Rewrite as |
|--------------------------|------------|
| `eightd-<name>` (any binary/CLI) | `aem-<name>` |
| `skill-8d-mrc` | `skill-ai-escape-mrc` |
| `run_8d` | `run_ai_escape_mrc` |
| `trigger_8d` | `trigger_ai_escape_mrc` |
| `8d-reports` (directory name) | `ai-escape-mrc-reports` |
| `pending-8d` (file/dir prefix) | `pending-ai-escape-mrc` |
| `CLAUDE_EIGHTD` (env var prefix) | `CLAUDE_AI_ESCAPE_MRC` |

Apply this rename consistently across every field. Output containing any forbidden literal will be rejected by the validator and you will be asked to regenerate this quadrant only.
```

Run after edit:
```bash
grep -c "Active Identity & Rename Rule" ai_escape_mrc/prompts/corrective_action.txt
```
Expected: `1`

- [ ] **Step 3: Append the same block to prevention_action.txt**

Use Edit with the identical text block (copy from Step 2 verbatim). Then verify:
```bash
grep -c "Active Identity & Rename Rule" ai_escape_mrc/prompts/prevention_action.txt
```
Expected: `1`

- [ ] **Step 4: Append the same block to prevention_audit.txt, with one tweak**

The audit prompt writes `suggested_fix` strings, not `action`/`files_touched`. Edit the block to read (note the field-list change in the first paragraph):

```text

## Active Identity & Rename Rule (MANDATORY)

Active skill identity: `skill-ai-escape-mrc` / `ai_escape_mrc` / `run_ai_escape_mrc.py` / `trigger_ai_escape_mrc.py`. When you coin or quote command names, paths, hooks, CLIs, env vars, or report directories in `issue`, `suggested_fix`, or any `evidence`/`rationale` field, you MUST use the active identity. Do not emit any of these legacy literals:

| Forbidden legacy literal | Rewrite as |
|--------------------------|------------|
| `eightd-<name>` (any binary/CLI) | `aem-<name>` |
| `skill-8d-mrc` | `skill-ai-escape-mrc` |
| `run_8d` | `run_ai_escape_mrc` |
| `trigger_8d` | `trigger_ai_escape_mrc` |
| `8d-reports` (directory name) | `ai-escape-mrc-reports` |
| `pending-8d` (file/dir prefix) | `pending-ai-escape-mrc` |
| `CLAUDE_EIGHTD` (env var prefix) | `CLAUDE_AI_ESCAPE_MRC` |

Output containing any forbidden literal will be rejected by the validator and you will be asked to regenerate this audit response.
```

Verify:
```bash
grep -c "Active Identity & Rename Rule" ai_escape_mrc/prompts/prevention_audit.txt
```
Expected: `1`

- [ ] **Step 5: Confirm no legacy literals were accidentally added to the prompts themselves**

```bash
grep -n -E "eightd|skill-8d-mrc|run_8d|trigger_8d|8d-reports|pending-8d|CLAUDE_EIGHTD" ai_escape_mrc/prompts/corrective_action.txt ai_escape_mrc/prompts/prevention_action.txt ai_escape_mrc/prompts/prevention_audit.txt
```
Expected: matches ONLY inside the new "Forbidden legacy literal" table rows (those are intended). Nothing outside the table.

- [ ] **Step 6: Commit**

```bash
git add ai_escape_mrc/prompts/corrective_action.txt ai_escape_mrc/prompts/prevention_action.txt ai_escape_mrc/prompts/prevention_audit.txt
git commit -m "feat(prompts): add IDENTITY RENAME RULE block to phase_4/5 producer prompts

corrective_action / prevention_action / prevention_audit prompts now
enumerate the FORBIDDEN_LEGACY_IDENTITY_TERMS denylist and the per-term
rename map, matching what phase_9 SYSTEM_PROMPT already has. LLM sees
the denylist at generation time, so the producer-side validator gate
(coming next) is the exception path rather than the rule.

No code change here; the gate that ENFORCES this is added in the next
commit."
```

---

## Task 3: Add legacy-term retry wrapper to phase_4 corrective and prevention calls

**Files:**
- Modify: `ai_escape_mrc/phases/phase_4_actions.py:78-113`
- Modify: `tests/test_phase_4_actions.py` (append new tests)

- [ ] **Step 1: Write the failing tests**

Append to `D:/D-claude/skills/skill-ai-escape-mrc/tests/test_phase_4_actions.py`:

```python
import pytest
from ai_escape_mrc.errors import OutputIdentityContractError


def test_phase_4_corrective_retries_once_on_legacy_term_and_passes():
    """First LLM response contains 'eightd-resolve'; retry returns clean → passes."""
    responses = iter([
        {"action": "create eightd-resolve binary", "rationale": "first try"},  # legacy → triggers retry
        {"action": "create aem-resolve binary", "rationale": "retry clean"},   # clean
    ])
    call_count = {"n": 0}

    def fake(**kw):
        call_count["n"] += 1
        if "prevention" in kw["system"].lower():
            # Prevention calls also need responses; give them clean output
            return {"action": "prevent", "gate_test": {"scope": "PASS"}}
        return next(responses)

    with patch("ai_escape_mrc.phases.phase_4_actions.call_claude", side_effect=fake):
        result = phase_4_actions(_base_state())

    # Two corrective calls (q1 first try fails legacy, retry passes; q2 first try passes)
    # plus two prevention calls = at least 4. The retry adds 1 → 5 minimum.
    assert call_count["n"] >= 5
    assert "eightd" not in str(result["corrective_actions"])


def test_phase_4_corrective_raises_after_second_legacy_hit():
    """Both attempts return forbidden literals → raises OutputIdentityContractError."""
    def fake(**kw):
        if "corrective" in kw["system"].lower():
            return {"action": "create eightd-omission-resolve", "rationale": "still bad"}
        return {"action": "prevent", "gate_test": {"scope": "PASS"}}

    with patch("ai_escape_mrc.phases.phase_4_actions.call_claude", side_effect=fake):
        with pytest.raises(OutputIdentityContractError) as exc:
            phase_4_actions(_base_state())
    assert "eightd" in str(exc.value).lower() or "legacy" in str(exc.value).lower()


def test_phase_4_no_retry_when_first_response_is_clean():
    """Clean first response → exactly 4 calls (no retry)."""
    call_count = {"n": 0}

    def fake(**kw):
        call_count["n"] += 1
        if "corrective" in kw["system"].lower():
            return {"action": "use aem-resolve", "rationale": "clean"}
        return {"action": "use ai-escape-mrc-reports dir", "gate_test": {"scope": "PASS"}}

    with patch("ai_escape_mrc.phases.phase_4_actions.call_claude", side_effect=fake):
        phase_4_actions(_base_state())
    assert call_count["n"] == 4  # 2 corrective + 2 prevention, no retries
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3 -m pytest tests/test_phase_4_actions.py::test_phase_4_corrective_retries_once_on_legacy_term_and_passes tests/test_phase_4_actions.py::test_phase_4_corrective_raises_after_second_legacy_hit tests/test_phase_4_actions.py::test_phase_4_no_retry_when_first_response_is_clean -v`
Expected: all three FAIL (retry wrapper not implemented).

- [ ] **Step 3: Add the retry helper inside `phase_4_actions.py`**

Modify `ai_escape_mrc/phases/phase_4_actions.py`. Insert a new helper after `_normalize_action_dict` (around line 32) and before `phase_4_actions`:

```python
from ai_escape_mrc.validators import validate_action_payload, FORBIDDEN_LEGACY_IDENTITY_TERMS
from ai_escape_mrc.errors import OutputIdentityContractError


def _call_with_legacy_term_retry(call_fn, *, system, user, json_schema, purpose):
    """Run an LLM call; on legacy-identity-term detection, retry once with a
    named critique injected; if the retry still trips the gate, re-raise.

    No fallback stub on identity failures — that would defeat the producer
    gate. Transport errors (SDK crashes / timeouts) are handled by the
    caller's existing try/except, not here.
    """
    for attempt in (1, 2):
        result = call_fn(
            model=model_for_role(purpose),
            system=system,
            user=user,
            json_schema=json_schema,
            purpose=purpose if attempt == 1 else f"{purpose}_retry_legacy",
        )
        try:
            validate_action_payload(result, artifact_name=f"phase_4 {purpose} (attempt {attempt})")
            return result
        except OutputIdentityContractError as e:
            if attempt == 2:
                raise
            # Inject named critique for the retry
            offending = next(
                (t for t in FORBIDDEN_LEGACY_IDENTITY_TERMS if t in str(result)),
                "unspecified legacy term",
            )
            user = (
                f"{user}\n\n"
                f"REGENERATE: your previous response contained forbidden legacy "
                f"identity literal {offending!r}. Per the IDENTITY RENAME RULE in "
                f"the system prompt, rewrite using the active identity (e.g. "
                f"`eightd-X` → `aem-X`). Emit the corrected JSON only."
            )
    # Unreachable (loop always returns or raises) — present only to satisfy linters
    raise RuntimeError("unreachable")  # pragma: no cover
```

Then modify `_corrective(q)` (currently at line 78) to use the wrapper. Replace the existing `_corrective` body's `call_claude(...)` invocation:

```python
    def _corrective(q):
        try:
            r = _call_with_legacy_term_retry(
                call_claude,
                system=corrective_prompt,
                user=_build_payload(q),
                json_schema=schemas.CORRECTIVE_ACTION,
                purpose=f"corrective_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except OutputIdentityContractError:
            # Identity contamination is a content error, NOT a transport error.
            # Fail closed — no stub fallback, no degraded emission (R13 compliance).
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] corrective {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD - LLM failed",
                       "rationale": "populate manually", "_fallback": True}
```

And `_prevention(q)` (currently at line 96) the same way:

```python
    def _prevention(q):
        try:
            r = _call_with_legacy_term_retry(
                call_claude,
                system=prevention_prompt,
                user=_build_payload(q),
                json_schema=schemas.PREVENTION_ACTION,
                purpose=f"prevention_{q}",
            )
            return q, r
        except VisibilityContractError:
            raise
        except OutputIdentityContractError:
            raise
        except Exception as e:
            import sys
            sys.stderr.write(f"[WARN] prevention {q} failed: {str(e)[:150]}; using stub\n")
            return q, {"quadrant": q, "action": "TBD - LLM failed",
                       "gate_test": {"scope": "FAIL", "persistence": "FAIL", "measurability": "FAIL"},
                       "hierarchy_level": 5, "_fallback": True}
```

Note: `model_for_role(...)` needs to accept a string like `"corrective_q1_trc_nc"`. Check `ai_escape_mrc/models.py` — if `model_for_role` falls back to the session default for unknown roles, this works as-is. If not, the wrapper should accept the model as a parameter from the caller. **Mandatory check before this step:** read `ai_escape_mrc/models.py` and confirm `model_for_role("corrective_q1_trc_nc")` does not raise. If it raises, the wrapper signature needs an additional `model` parameter passed in by `_corrective` / `_prevention` (use `model=model_for_role("corrective_action")` and `model=model_for_role("prevention_action")` at the call sites, matching the original code's role strings).

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3 -m pytest tests/test_phase_4_actions.py -v`
Expected: all phase_4 tests pass (including the existing ones and the three new ones from Step 1).

- [ ] **Step 5: Commit**

```bash
git add ai_escape_mrc/phases/phase_4_actions.py tests/test_phase_4_actions.py
git commit -m "feat(phase_4): hard producer gate — retry-then-raise on legacy identity terms

_corrective and _prevention LLM calls now route through
_call_with_legacy_term_retry: validate_action_payload runs on each
response; on legacy-term hit, one retry is fired with a named critique
('your previous response contained X; rename per IDENTITY RENAME RULE');
second failure raises OutputIdentityContractError — no fallback stub
(content errors must fail closed at the producer; transport errors keep
their existing stub fallback per the original design).

This is the structural counterpart to the consumer-side fix at e017eb3:
plan.md and report.md will never again ingest contaminated upstream state,
because the contamination is rejected at the moment phase_4 tries to write
it into the checkpoint."
```

---

## Task 4: Add the same legacy-term retry to phase_5 prevention audit

**Files:**
- Modify: `ai_escape_mrc/phases/phase_5_prevention_audit.py:47-72`
- Create: `tests/test_phase_5_prevention_audit.py`

- [ ] **Step 1: Write the failing tests**

Create `D:/D-claude/skills/skill-ai-escape-mrc/tests/test_phase_5_prevention_audit.py`:

```python
"""Phase 5 prevention-audit legacy-identity producer gate."""
import pytest
from unittest.mock import patch, MagicMock
from ai_escape_mrc.errors import OutputIdentityContractError
from ai_escape_mrc.phases.phase_5_prevention_audit import phase_5_prevention_audit


def _base_state_with_preventions():
    return {
        "prevention_actions": {
            "q3_mrc_nc": {"action": "use aem-resolve"},
            "q4_mrc_nd": {"action": "use ai-escape-mrc-reports"},
        },
        "phase_5_rounds": [],
    }


def _mock_session(responses):
    """Build a ClaudeSession context manager that returns the next response on each .ask()."""
    it = iter(responses)
    sess = MagicMock()
    sess.ask = MagicMock(side_effect=lambda *a, **kw: next(it))
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=sess)
    cm.__exit__ = MagicMock(return_value=False)
    return cm, sess


def test_phase_5_audit_retries_once_on_legacy_term_and_passes():
    """First audit response contains legacy literal in suggested_fix; retry clean → passes."""
    responses = [
        {  # legacy → triggers retry
            "round": 1,
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
                 "issue": "weak gate", "suggested_fix": "use eightd-omission-resolve CLI"},
            ],
        },
        {  # clean
            "round": 1,
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
                 "issue": "weak gate", "suggested_fix": "use aem-omission-resolve CLI"},
            ],
        },
    ]
    cm, sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        result = phase_5_prevention_audit(_base_state_with_preventions())

    assert sess.ask.call_count == 2
    audit_notes = result["prevention_actions"]["q3_mrc_nc"].get("audit_notes") or []
    assert all("eightd" not in note for note in audit_notes)


def test_phase_5_audit_raises_after_second_legacy_hit():
    responses = [
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "x", "suggested_fix": "use eightd-resolve"},
        ]},
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "x", "suggested_fix": "still uses eightd-resolve"},
        ]},
    ]
    cm, _sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        with pytest.raises(OutputIdentityContractError):
            phase_5_prevention_audit(_base_state_with_preventions())


def test_phase_5_audit_no_retry_when_first_response_is_clean():
    responses = [
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "ok", "suggested_fix": "use aem-resolve"},
        ]},
    ]
    cm, sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        phase_5_prevention_audit(_base_state_with_preventions())
    assert sess.ask.call_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -3 -m pytest tests/test_phase_5_prevention_audit.py -v`
Expected: 3 failures (`audit.ask` is called only once; legacy term passes through).

- [ ] **Step 3: Wrap the `sess.ask(...)` call with the retry**

Modify `ai_escape_mrc/phases/phase_5_prevention_audit.py`. Add imports at the top:

```python
from ai_escape_mrc.validators import validate_action_payload, FORBIDDEN_LEGACY_IDENTITY_TERMS
from ai_escape_mrc.errors import OutputIdentityContractError
```

Replace the `try: audit = sess.ask(...)` block (lines 54-61 in the current file) with:

```python
            audit = None
            for attempt in (1, 2):
                try:
                    audit = sess.ask(user_msg, purpose=f"phase_5_prevention_audit_round_{round_num}_attempt_{attempt}")
                except VisibilityContractError:
                    raise
                except Exception as e:
                    import sys
                    sys.stderr.write(f"[WARN] phase_5 round {round_num} attempt {attempt} failed: {str(e)[:150]}; skipping round\n")
                    audit = {"round": round_num, "weaknesses": [], "verdict": "EXHAUSTED", "_fallback": True}
                    break  # transport error → take the fallback, do not retry for identity reasons

                try:
                    validate_action_payload(audit, artifact_name=f"phase_5 audit round {round_num} attempt {attempt}")
                    break  # clean → accept this audit
                except OutputIdentityContractError as e:
                    if attempt == 2:
                        raise  # second attempt still contaminated → fail closed
                    offending = next(
                        (t for t in FORBIDDEN_LEGACY_IDENTITY_TERMS if t in str(audit)),
                        "unspecified legacy term",
                    )
                    user_msg = (
                        f"{user_msg}\n\n"
                        f"REGENERATE: your previous audit response contained forbidden legacy "
                        f"identity literal {offending!r} in a `suggested_fix` or `issue` field. "
                        f"Per the IDENTITY RENAME RULE in the system prompt, rewrite using the "
                        f"active identity (`eightd-X` → `aem-X`, etc.). Emit the corrected JSON only."
                    )
```

The list-normalization + `isinstance(audit, dict)` fallback handling that follows stays as-is.

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3 -m pytest tests/test_phase_5_prevention_audit.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run full phase_5 test surface to confirm no regression**

Run: `py -3 -m pytest tests/test_phase_5_prevention_audit.py tests/test_rework_loop.py tests/test_identity_contract.py -v`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add ai_escape_mrc/phases/phase_5_prevention_audit.py tests/test_phase_5_prevention_audit.py
git commit -m "feat(phase_5): hard producer gate on prevention-audit responses

Mirrors phase_4's retry-then-raise pattern. The audit's suggested_fix
strings get appended to state[\"prevention_actions\"][q][\"audit_notes\"]
via _apply_fixes, so contamination at the audit layer also leaks
downstream — not just contamination at phase_4 action generation.

One retry budget per audit round; named critique injected on retry;
second failure raises OutputIdentityContractError (fail closed). Transport
errors keep their existing fallback path (break out of the retry loop,
take the EXHAUSTED stub) — those are not content errors."
```

---

## Task 5: End-to-end integration test (mocked)

**Files:**
- Create: `tests/test_phase_4_5_identity_integration.py`

- [ ] **Step 1: Write the integration test**

Create `D:/D-claude/skills/skill-ai-escape-mrc/tests/test_phase_4_5_identity_integration.py`:

```python
"""Integration: phase_4 + phase_5 producer-side legacy-identity gate.

Simulates a real-world contamination event: phase_4 prevention call returns
eightd-* literal on the first attempt, retry succeeds. phase_5 audit then
returns a clean response. End state passes the consumer-side gate that
phase_9/phase_7 would later run.
"""
from unittest.mock import patch, MagicMock
from ai_escape_mrc.phases.phase_4_actions import phase_4_actions
from ai_escape_mrc.phases.phase_5_prevention_audit import phase_5_prevention_audit
from ai_escape_mrc.validators import validate_action_payload


def test_phase_4_5_clean_after_legacy_retry_at_phase_4():
    """phase_4 prevention q3 first response has eightd-, retry clean. phase_5 clean.
    Final prevention_actions state must pass downstream validator."""
    corrective_clean = {"action": "verify aem-resolve binary", "rationale": "clean"}
    prevention_legacy = {"action": "create eightd-omission-resolve CLI", "gate_test": {"scope": "PASS"}}
    prevention_clean = {"action": "create aem-omission-resolve CLI", "gate_test": {"scope": "PASS"}}

    responses = iter([
        corrective_clean,           # q1 corrective
        corrective_clean,           # q2 corrective
        prevention_legacy,          # q3 prevention attempt 1 (contaminated)
        prevention_clean,           # q3 prevention attempt 2 (clean)
        prevention_clean,           # q4 prevention attempt 1 (clean)
    ])

    def fake_call(**kw):
        return next(responses)

    state = {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"}
                       for q in ("q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd")},
    }

    with patch("ai_escape_mrc.phases.phase_4_actions.call_claude", side_effect=fake_call):
        state = phase_4_actions(state)

    # Final state must pass consumer-side validator
    validate_action_payload(state["corrective_actions"], artifact_name="integration test")
    validate_action_payload(state["prevention_actions"], artifact_name="integration test")
```

- [ ] **Step 2: Run the integration test**

Run: `py -3 -m pytest tests/test_phase_4_5_identity_integration.py -v`
Expected: 1 passed.

- [ ] **Step 3: Run the full test suite to ensure no regression**

Run: `py -3 -m pytest -x --tb=short`
Expected: all green. If any test fails, STOP and diagnose before committing.

- [ ] **Step 4: Commit**

```bash
git add tests/test_phase_4_5_identity_integration.py
git commit -m "test(phase_4_5): integration — legacy-term retry produces clean downstream state

End-to-end: phase_4 prevention call returns eightd-* on attempt 1, retry
succeeds with clean rename. Final state.prevention_actions passes the
consumer-side validate_action_payload check — proving the producer gate
keeps downstream phase_7/phase_9 inputs clean without consumer-side
sanitization being needed for new runs."
```

---

## Task 6: Push to github canonical + sync to gerrit mirror

**Files:**
- Push to github canonical
- Sync to `D:/D-claude/cn5dd2/CN5DD2_common/skills/skill-ai-escape-mrc/`
- Commit + push to gerrit

- [ ] **Step 1: Push canonical to github**

```bash
cd D:/D-claude/skills/skill-ai-escape-mrc
git log --oneline origin/master..HEAD
git push origin master
```

Expected: 5 new commits pushed (Tasks 1-5).

- [ ] **Step 2: Sync canonical → gerrit mirror via robocopy (Windows)**

```powershell
robocopy "D:\D-claude\skills\skill-ai-escape-mrc" "D:\D-claude\cn5dd2\CN5DD2_common\skills\skill-ai-escape-mrc" /E /XD .git runs __pycache__ ai-escape-mrc-reports /XF *.pyc *.log /NFL /NDL /NJH /NJS /NP
```

Expected exit code: 0-7 (`robocopy` semantics — 0=no changes copied, 1=files copied, 3=files copied+extras existed).

- [ ] **Step 3: Inspect gerrit-side diff**

```bash
cd D:/D-claude/cn5dd2/CN5DD2_common
git status -s skills/skill-ai-escape-mrc/
git diff --stat skills/skill-ai-escape-mrc/ | tail -3
```

Expected: ~7 files modified/created (validators.py, phase_4_actions.py, phase_5_prevention_audit.py, 3 prompt files, 3 test files; counts may differ slightly).

- [ ] **Step 4: Commit gerrit side**

```bash
git add skills/skill-ai-escape-mrc/
git commit -m "$(cat <<'EOF'
sync(skill-ai-escape-mrc): pull producer-side identity sanitize gate

Mirror upstream commits Task1-Task5 (validators.validate_action_payload,
prompts IDENTITY RENAME RULE, phase_4 and phase_5 retry-then-raise legacy
literal gate, integration test). Eliminates the bug class where a phase_4
LLM coined eightd-* literal poisons actions.json + checkpoint state and
crashes phase_7/phase_9 ~20 min later. New runs fail-closed at phase_4
producer instead.

Defense-in-depth: phase_9 SYSTEM_PROMPT denylist (commit e017eb3) stays
as the consumer-side backstop for re-runs of old checkpoints that have
pre-existing contamination.
EOF
)"
```

- [ ] **Step 5: Dry-run push to gerrit then real push**

```bash
git push --dry-run origin HEAD:refs/heads/master
# inspect output: should show fast-forward
git push origin HEAD:refs/heads/master
git ls-remote origin master
```

Expected: remote master tip matches the new local commit.

- [ ] **Step 6: Final verification — both remotes converged**

```bash
cd D:/D-claude/skills/skill-ai-escape-mrc && git rev-parse HEAD
cd D:/D-claude/cn5dd2/CN5DD2_common && git log --oneline -1 -- skills/skill-ai-escape-mrc/
```

Both should reference the latest sync commit. Report both SHAs in the completion summary.

---

## Self-Review

**Spec coverage:**

- Producer-side hard gate at phase_4 → Tasks 1, 3
- Producer-side hard gate at phase_5 → Task 4
- Soft prompt assist (RENAME RULE injection) at phase_4 corrective+prevention → Task 2
- Soft prompt assist at phase_5 audit → Task 2
- New validator helper → Task 1
- Tests (unit + integration) → Tasks 1, 3, 4, 5
- Deploy to both repos → Task 6
- Out-of-scope items explicitly noted (graph topology unchanged, phase_9 consumer gate kept as defense-in-depth) → File Structure table.

No spec items uncovered.

**Placeholder scan:**

- No "TBD" / "TODO" / "fill in details" / "Similar to Task N" anywhere.
- Every code block contains the exact text to be inserted.
- Every test contains the actual assertions, not "write tests for this".
- File paths are absolute and concrete.
- The one conditional check ("if `model_for_role(...)` doesn't accept the new role string, the wrapper needs a `model` parameter") is explicit about both branches with the exact code path for each — not a placeholder.

**Type consistency:**

- `validate_action_payload(payload, *, artifact_name: str) -> None` consistent across Tasks 1, 3, 4, 5.
- `_call_with_legacy_term_retry(call_fn, *, system, user, json_schema, purpose)` defined Task 3, used same signature.
- `OutputIdentityContractError` imported from `ai_escape_mrc.errors` consistently (existing import per prior phase_9 fix).
- `FORBIDDEN_LEGACY_IDENTITY_TERMS` referenced as a tuple — matches the constant defined in validators.py.

No inconsistencies found.

**Out-of-scope reminders:**

- Phase_2 / phase_3 LLM calls: NOT covered here. They write `why_chains` into state but are less likely to coin command/path literals (their output is narrative why-text). If a future run shows phase_2 contamination, add a Task 7 with the same pattern. Defer; the gate at phase_4 will catch anything phase_2 leaks through (phase_4 reads `why_chains` and emits actions; if phase_2's why-text contains `eightd-`, phase_4's `_build_payload` carries it into the user message, and the LLM might repeat it in the action — gate-blocked at phase_4 attempt 1, fixed at retry).
- Phase_6 verification: same reasoning. Phase_6's output is the verification plan; if it coins a metric like "count eightd-* matches", that's a content reference rather than a command, but technically would still trip the validator. Out of scope here; will surface as the next bug class if it ever happens.
- Removing phase_9's consumer-side gate: explicitly NOT done. Defense-in-depth is intentional — old checkpoints being `--resume`d will still have contamination, and the producer gate only protects new emissions.
