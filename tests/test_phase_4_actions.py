from unittest.mock import patch
from eightd.phases.phase_4_actions import phase_4_actions
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
