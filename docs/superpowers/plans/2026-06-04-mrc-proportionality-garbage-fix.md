# MRC Proportionality Garbage-Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Stop the MRC pipeline from manufacturing over-engineered "garbage" prevention (e.g. "每三個月檢查一次") by (a) routing local one-off incidents to corrective-only instead of force-filling MRC quadrants, (b) adding a proportionality axis to the prevention gate, and (c) letting the Phase-5 audit CUT over-scoped controls.

**Architecture:** Default-ANALYZE incident-class router (fail-safe), threaded through phases via `active_quadrants(state)`; a 4th `gate_test` axis grounded in hierarchy-of-controls; an `OVER_SCOPED` audit verdict that prunes.

**Tech Stack:** Python 3 (`py -3`), pytest.

---

## Task 1: state — mrc_applicable + active-quadrant helpers

**Files:** Modify `ai_escape_mrc/state.py`; Test `tests/test_active_quadrants.py`

- [ ] **Step 1: Failing test.**
```python
# tests/test_active_quadrants.py
from ai_escape_mrc.state import active_quadrants, active_prevention_quadrants
def test_default_all_four():
    assert active_quadrants({}) == ["q1_trc_nc","q2_trc_nd","q3_mrc_nc","q4_mrc_nd"]
    assert active_prevention_quadrants({}) == ["q3_mrc_nc","q4_mrc_nd"]
def test_mrc_not_applicable_drops_mrc():
    s = {"mrc_applicable": False}
    assert active_quadrants(s) == ["q1_trc_nc","q2_trc_nd"]
    assert active_prevention_quadrants(s) == []
def test_mrc_applicable_true_keeps_all():
    assert active_quadrants({"mrc_applicable": True}) == ["q1_trc_nc","q2_trc_nd","q3_mrc_nc","q4_mrc_nd"]
```
Run `py -3 -m pytest tests/test_active_quadrants.py -v` → FAIL.

- [ ] **Step 2: Implement in `state.py`.** Add to `AiEscapeMrcState` (after the Phase-1 block): `mrc_applicable: bool` and `mrc_applicability_justification: str`. Add module-level:
```python
MRC_QUADRANTS = ["q3_mrc_nc", "q4_mrc_nd"]
TRC_QUADRANTS = ["q1_trc_nc", "q2_trc_nd"]

def active_quadrants(state: dict) -> list[str]:
    """Quadrants to analyze. Default = all four. MRC quadrants are dropped ONLY
    when the router positively set mrc_applicable=False (fail-safe: any missing/
    truthy/None value keeps MRC)."""
    if state.get("mrc_applicable") is False:
        return list(TRC_QUADRANTS)
    return list(QUADRANTS)

def active_prevention_quadrants(state: dict) -> list[str]:
    """Prevention quadrants (MRC only). Empty when MRC not applicable."""
    return [q for q in MRC_QUADRANTS if q in active_quadrants(state)]
```
Run → PASS. Commit.

## Task 2: schemas — proportionality axis + OVER_SCOPED

**Files:** Modify `ai_escape_mrc/schemas.py`; Test `tests/test_schema_proportionality.py`

- [ ] **Step 1: Failing test.**
```python
from ai_escape_mrc import schemas
def test_proportionality_in_gate_test():
    gt = schemas.PREVENTION_ACTION["properties"]["gate_test"]
    assert "proportionality" in gt["properties"]
    assert "proportionality" in gt["required"]
def test_over_scoped_verdict():
    assert "OVER_SCOPED" in schemas.PREVENTION_AUDIT["properties"]["verdict"]["enum"]
```
Run → FAIL.

- [ ] **Step 2:** In `schemas.py` `PREVENTION_ACTION.gate_test.properties` add `"proportionality": {"type":"string","enum":["PASS","FAIL"]}` and `"proportionality_evidence": {"type":"string"}`; append `"proportionality"` to that object's `required`. In `PREVENTION_AUDIT.verdict.enum` add `"OVER_SCOPED"`. If the audit weakness object has a `classification` enum, add `"OVER_SCOPED"` there too.
Run → PASS. Commit.

## Task 3: phase_1 — emit the router classification (default True)

**Files:** Modify `ai_escape_mrc/phases/phase_1_is_isnt.py`; `ai_escape_mrc/schemas.py` (small classification schema); Test `tests/test_router_classification.py`

- [ ] **Step 1: Failing test** (mock `call_claude` so no network): patch `phase_1_is_isnt.call_claude` to return a classification dict; assert `state["mrc_applicable"]` is set; assert an exception in the classify call leaves `mrc_applicable=True` (fail-safe).
```python
import ai_escape_mrc.phases.phase_1_is_isnt as p1
def test_router_sets_false_for_local(monkeypatch):
    monkeypatch.setattr(p1, "call_claude", lambda **k: {"mrc_applicable": False, "justification": "local one-off"} if k.get("purpose")=="mrc_applicability" else {"what":{"is":"x","is_not":"y","distinction":"z"},"where":{},"when":{},"extent":{}})
    s = p1.phase_1_is_isnt({"problem":"a one-off typo"})
    assert s["mrc_applicable"] is False
def test_router_failsafe_true_on_error(monkeypatch):
    def boom(**k):
        if k.get("purpose")=="mrc_applicability": raise RuntimeError("x")
        return {"what":{"is":"x","is_not":"y","distinction":"z"}}
    monkeypatch.setattr(p1, "call_claude", boom)
    s = p1.phase_1_is_isnt({"problem":"p"})
    assert s.get("mrc_applicable") is True
```
Run → FAIL.

- [ ] **Step 2:** Add `schemas.MRC_APPLICABILITY = {"type":"object","properties":{"mrc_applicable":{"type":"boolean"},"justification":{"type":"string"}},"required":["mrc_applicable","justification"]}`.
- [ ] **Step 3:** In `phase_1_is_isnt`, AFTER the is_isnt_table is set, add a classification call wrapped fail-safe:
```python
    # Incident-class router: does this incident plausibly have a MANAGEMENT-SYSTEM
    # root cause, or is it a local/non-recurring one-off? Default True (analyze).
    mrc_applicable, justification = True, "default: analyze (router not conclusive)"
    try:
        cls = call_claude(
            model=model_for_role("is_isnt_extraction"),
            system=(
                "Classify whether this incident plausibly has a MANAGEMENT-SYSTEM "
                "(policy/ownership/process) root cause worth a prevention action, or "
                "is a LOCAL, NON-RECURRING one-off (single technical/behavioral slip, "
                "no systemic gap). Return mrc_applicable=false ONLY if you can justify "
                "it is local AND non-recurring AND has no plausible management gap. "
                "If it recurs, spans surfaces, or matches a prior class -> true. "
                "When unsure -> true."
            ),
            user=f"Problem:\n{state['problem']}\n\nIS/IS NOT:\n{result}",
            json_schema=schemas.MRC_APPLICABILITY,
            purpose="mrc_applicability",
        )
        if isinstance(cls, dict) and isinstance(cls.get("mrc_applicable"), bool):
            mrc_applicable = cls["mrc_applicable"]
            justification = cls.get("justification", "")[:500]
    except Exception as e:
        sys.stderr.write(f"[WARN] phase_1 mrc-router failed: {str(e)[:150]}; default mrc_applicable=True\n")
    state["mrc_applicable"] = mrc_applicable
    state["mrc_applicability_justification"] = justification
```
Run → PASS. Commit.

## Task 4: phase_2 + phase_3 — iterate active quadrants

**Files:** Modify `phases/phase_2_why_analysis.py`, `phases/phase_3_rc_audit.py`

- [ ] **Step 1:** In `phase_2_why_analysis`, import `active_quadrants` from `state` and replace every use of the module-level `QUADRANTS` with `active_quadrants(state)` (the non-rework branch's `parallel_map(..., QUADRANTS, ...)` and the rework `to_run`/`_critiqued_quadrants` set intersection). Reuse-of-prior-chain logic unchanged; just the universe shrinks.
- [ ] **Step 2:** In `phase_3_rc_audit.py`, scope the audit to `active_quadrants(state)` (read it; if it iterates QUADRANTS, swap). Read the actual file and apply the same swap; do not audit dropped quadrants.
- [ ] **Step 3:** Tests: extend `tests/test_active_quadrants.py` or the phase tests — with `mrc_applicable=False`, `phase_2` produces only `q1_trc_nc,q2_trc_nd` keys in `why_chains` (mock `_run_quadrant`). Run, commit.

## Task 5: phase_4 — corrective-only when MRC N/A

**Files:** Modify `phases/phase_4_actions.py`

- [ ] **Step 1:** Replace the module constant use `PREVENTION_QUADRANTS` with `active_prevention_quadrants(state)` (import from state). When it's empty, the prevention task list is empty → only Q1/Q2 corrective run; `state["prevention_actions"]` stays `{}`. Keep the phase_5-rework branch logic, intersected with the active set.
- [ ] **Step 2:** Test: with `mrc_applicable=False`, `phase_4` (mock `call_claude`) sets `corrective_actions` for q1/q2 and `prevention_actions == {}`; no prevention LLM call made. Run, commit.

## Task 6: phase_5 — OVER_SCOPED cuts, not appends

**Files:** Modify `phases/phase_5_prevention_audit.py`

- [ ] **Step 1:** In `_apply_fixes`, add handling: for a weakness with `classification == "OVER_SCOPED"` and a `quadrant` in `prevention_actions`, REPLACE the action's control with the auditor's `suggested_fix` (record the original under `pa["downscoped_from"]` and set `pa["action"] = suggested_fix` or `pa.setdefault("downscope", []).append(...)` with the cut recorded) — do NOT merely append to `audit_notes`. Keep ADDRESSABLE behavior (append) unchanged.
- [ ] **Step 2:** The verdict handling: `OVER_SCOPED` rounds are real audits (not `_fallback`); ensure the early-exit/`_has_addressable` logic still terminates (treat OVER_SCOPED like ADDRESSABLE for loop continuation, i.e. it can trigger a rework/cut pass).
- [ ] **Step 3:** If `mrc_applicable=False` (no prevention actions), `phase_5` must no-op gracefully (empty `preventions` dict → skip the audit, set verdict EXHAUSTED). Add a guard at the top.
- [ ] **Step 4:** Tests: an audit round with an `OVER_SCOPED` weakness for `q3_mrc_nc` → that action's control is replaced/recorded-as-cut (assert `downscoped_from` present and `action` changed); and `phase_5` with empty prevention_actions → no exception, verdict EXHAUSTED. Run, commit.

## Task 7: prompts + report rendering

**Files:** Modify `prompts/prevention_action.txt`, `prompts/prevention_audit.txt`, `phases/phase_7_report.py` (or render)

- [ ] **Step 1:** `prevention_action.txt`: add the proportionality axis to the gate-test instructions (verbatim from spec §2b) and require `proportionality` + `proportionality_evidence` in `gate_test`. Add to the hierarchy note: "a scheduled-review / periodic-audit / new-standing-ritual control for a one-off or low-severity incident FAILS proportionality; prefer Rung 1-3 structural controls."
- [ ] **Step 2:** `prevention_audit.txt`: instruct the auditor to return `verdict: OVER_SCOPED` (or an OVER_SCOPED weakness) when a prevention fails proportionality (e.g. a standing ritual where a one-line structural gate suffices), and to supply a proportionate `suggested_fix`.
- [ ] **Step 3:** `phase_7_report.py` / render: when `state.get("mrc_applicable") is False`, render the MRC section as "MRC quadrants: N/A — {mrc_applicability_justification}" instead of empty/blank. Read the actual render path and apply. Commit.

## Task 8: integration regression + anti-garbage tests

**Files:** `tests/test_proportionality_integration.py`

- [ ] **Step 1:** **Safety regression** — a recurring/cross-surface synthetic problem → `phase_1` router returns `mrc_applicable=True` (mock the classify call to True) → `active_quadrants` == all four (assert NO behavior change vs today for systemic incidents).
- [ ] **Step 2:** **Local-one-off path** — `mrc_applicable=False` → end-to-end (stub LLMs) phase_2→4 produce corrective-only, `prevention_actions == {}`, report shows the N/A justification.
- [ ] **Step 3:** **Anti-garbage** — a prevention action whose `action` is a quarterly-review ritual with `hierarchy_level=5` for a one-off → the gate's `proportionality` is FAIL (assert the schema+prompt contract surfaces it; test the validator/shape, not the LLM).
- [ ] **Step 4:** Run full suite `py -3 -m pytest -q`; confirm green (note pre-existing unrelated failures separately). Commit.

## Self-Review

- **Spec coverage:** §2a router → Tasks 1,3,4; threading → Task 4 (phase_2/3), 5; §2b proportionality → Tasks 2,7; §2c OVER_SCOPED → Tasks 2,6,7; §3 report N/A → Task 7; §6 tests → Task 8.
- **Safety:** router default True everywhere (`active_quadrants` fail-safe; phase_1 fail-safe on error); the systemic-incident regression test (Task 8 Step 1) guards the MRC's core purpose.
- **Type consistency:** `active_quadrants`/`active_prevention_quadrants` signatures match across phases; `mrc_applicable` is the single source of truth.
