from unittest.mock import patch
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.state import QUADRANTS


def test_phase_6_produces_proof_for_all_4_quadrants():
    state = {
        "corrective_actions": {q: {"action": "c"} for q in QUADRANTS},
        "prevention_actions": {q: {"action": "p"} for q in QUADRANTS},
    }

    def fake_call(model, system, user, parse_json=False, **kw):
        return {
            "quadrant": "x",
            "metric": "count",
            "data_source": "log",
            "target": "zero",
            "baseline": "5",
            "measurement_schedule": "daily",
            "failure_response": "re-open",
        }

    with patch("eightd.phases.phase_6_verification.call_claude", side_effect=fake_call):
        result = phase_6_verification(state)

    assert set(result["proof_of_action"].keys()) == set(QUADRANTS)
    for q in QUADRANTS:
        assert "metric" in result["proof_of_action"][q]
        assert "target" in result["proof_of_action"][q]
    assert result["phase_6_complete"] is True
