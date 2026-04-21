from unittest.mock import patch
from eightd.phases.phase_4_actions import phase_4_actions, _normalize_action_dict
from eightd.state import QUADRANTS


def test_phase_4_produces_both_corrective_and_prevention_per_quadrant():
    state = {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"} for q in QUADRANTS},
    }

    def fake_call(model, system, user, parse_json=False, **kw):
        if "corrective" in system.lower():
            return {"quadrant": "x", "action": "fix this instance", "rationale": "..."}
        return {"quadrant": "x", "action": "prevent class", "gate_test": {"scope": "PASS"}, "hierarchy_level": 2}

    with patch("eightd.phases.phase_4_actions.call_claude", side_effect=fake_call):
        result = phase_4_actions(state)

    assert set(result["corrective_actions"].keys()) == set(QUADRANTS)
    assert set(result["prevention_actions"].keys()) == set(QUADRANTS)
    assert result["phase_4_complete"] is True


def test_phase_4_unwraps_list_wrapped_dict():
    """LLM sometimes returns [{...}] instead of {...}; normalizer unwraps it."""
    state = {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"} for q in QUADRANTS},
    }
    wrapped = [{"quadrant": "q3_mrc_nc", "action": "wrapped dict"}]

    with patch("eightd.phases.phase_4_actions.call_claude", return_value=wrapped):
        result = phase_4_actions(state)

    for q in QUADRANTS:
        pa = result["prevention_actions"][q]
        assert isinstance(pa, dict), f"{q}: expected dict, got {type(pa)}"
        assert pa.get("action") == "wrapped dict"


def test_phase_4_handles_unparseable_shape():
    """If LLM returns a string/number, wrap it so audit phase can still iterate."""
    state = {
        "problem": "p",
        "why_chains": {q: {"whys": [], "root": "r"} for q in QUADRANTS},
    }

    with patch("eightd.phases.phase_4_actions.call_claude", return_value="bare string output"):
        result = phase_4_actions(state)

    for q in QUADRANTS:
        pa = result["prevention_actions"][q]
        assert isinstance(pa, dict)
        assert "_parse_warning" in pa
        assert "bare string output" in pa["action"]


def test_normalize_action_dict_unit():
    assert _normalize_action_dict({"a": 1}) == {"a": 1}
    assert _normalize_action_dict([{"a": 1}]) == {"a": 1}
    # Multi-element list: fall through to wrap
    multi = _normalize_action_dict([{"a": 1}, {"b": 2}])
    assert "_parse_warning" in multi
    # String: wrap with truncated action
    s = _normalize_action_dict("hello")
    assert s == {"action": "hello", "_parse_warning": "expected dict, got str"}


def test_phase_5_audit_skips_non_dict_prevention_action():
    """Phase 5 audit must not crash when prevention_actions[q] is a list
    (e.g., checkpoint from an older run before normalization was added)."""
    from eightd.phases.phase_5_prevention_audit import phase_5_prevention_audit
    state = {
        "prevention_actions": {q: [{"action": "a"}] for q in QUADRANTS},  # list shape
        "phase_5_soa_research": [],
        "phase_5_attempt_count": 0,
    }

    def fake_call(model, system, user, parse_json=False, **kw):
        return {
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q1_trc_nc", "suggested_fix": "tighten metric"},
            ],
            "soa_citations_used": ["https://example.com"],
        }

    with patch("eightd.phases.phase_5_prevention_audit.call_claude", side_effect=fake_call):
        # Should not raise AttributeError even though prevention_actions[q] is a list.
        result = phase_5_prevention_audit(state)

    assert result["phase_5_complete"] is True
