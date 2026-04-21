"""Phase 4 — 2 corrective (Q1,Q2) + 2 prevention (Q3,Q4) = 4 parallel calls."""
from unittest.mock import patch
from eightd.phases.phase_4_actions import (
    phase_4_actions, _normalize_action_dict,
    CORRECTIVE_QUADRANTS, PREVENTION_QUADRANTS,
)


def _base_state():
    all_q = CORRECTIVE_QUADRANTS + PREVENTION_QUADRANTS
    return {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"} for q in all_q},
    }


def test_phase_4_corrective_only_for_q1_q2():
    def fake(**kw):
        if "corrective" in kw["system"].lower():
            return {"action": "fix", "rationale": "..."}
        return {"action": "prevent", "gate_test": {"scope": "PASS"}}

    with patch("eightd.phases.phase_4_actions.call_claude", side_effect=fake):
        result = phase_4_actions(_base_state())

    assert set(result["corrective_actions"].keys()) == {"q1_trc_nc", "q2_trc_nd"}
    assert "q3_mrc_nc" not in result["corrective_actions"]
    assert "q4_mrc_nd" not in result["corrective_actions"]


def test_phase_4_prevention_only_for_q3_q4():
    def fake(**kw):
        if "corrective" in kw["system"].lower():
            return {"action": "fix"}
        return {"action": "prevent"}

    with patch("eightd.phases.phase_4_actions.call_claude", side_effect=fake):
        result = phase_4_actions(_base_state())

    assert set(result["prevention_actions"].keys()) == {"q3_mrc_nc", "q4_mrc_nd"}
    assert "q1_trc_nc" not in result["prevention_actions"]
    assert "q2_trc_nd" not in result["prevention_actions"]


def test_phase_4_makes_exactly_4_calls():
    """Not 8 (prior bug). Corrective x 2 + Prevention x 2."""
    call_count = {"n": 0}

    def fake(**kw):
        call_count["n"] += 1
        return {"action": "x"}

    with patch("eightd.phases.phase_4_actions.call_claude", side_effect=fake):
        phase_4_actions(_base_state())

    assert call_count["n"] == 4


def test_phase_4_unwraps_list_wrapped_dict():
    wrapped = [{"action": "wrapped"}]
    with patch("eightd.phases.phase_4_actions.call_claude", return_value=wrapped):
        result = phase_4_actions(_base_state())
    for q in CORRECTIVE_QUADRANTS:
        assert result["corrective_actions"][q] == {"action": "wrapped"}
    for q in PREVENTION_QUADRANTS:
        assert result["prevention_actions"][q] == {"action": "wrapped"}


def test_phase_4_handles_unparseable_shape():
    with patch("eightd.phases.phase_4_actions.call_claude", return_value="bare string"):
        result = phase_4_actions(_base_state())
    for q in CORRECTIVE_QUADRANTS:
        assert "_parse_warning" in result["corrective_actions"][q]
    for q in PREVENTION_QUADRANTS:
        assert "_parse_warning" in result["prevention_actions"][q]


def test_normalize_action_dict_unit():
    assert _normalize_action_dict({"a": 1}) == {"a": 1}
    assert _normalize_action_dict([{"a": 1}]) == {"a": 1}
    multi = _normalize_action_dict([{"a": 1}, {"b": 2}])
    assert "_parse_warning" in multi
    s = _normalize_action_dict("hello")
    assert s == {"action": "hello", "_parse_warning": "expected dict, got str"}


def test_phase_5_audit_skips_non_dict_prevention_action():
    from eightd.phases.phase_5_prevention_audit import phase_5_prevention_audit
    state = {
        "prevention_actions": {
            "q3_mrc_nc": [{"action": "a"}],  # list shape (from older checkpoint)
            "q4_mrc_nd": [{"action": "b"}],
        },
    }

    def fake(**kw):
        return {
            "round": 1,
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
                 "suggested_fix": "tighten"},
            ],
        }

    with patch("eightd.phases.phase_5_prevention_audit.call_claude", side_effect=fake):
        result = phase_5_prevention_audit(state)

    # Should not crash even with list-shaped prevention_actions.
    assert result["phase_5_complete"] is True
