from unittest.mock import patch
from eightd.phases.phase_6_verification import phase_6_verification
from eightd.state import QUADRANTS


def test_phase_6_produces_unified_plan_with_4_quadrant_rows():
    """One call returns a plan containing all 4 quadrant metrics."""
    state = {
        "corrective_actions": {"q1_trc_nc": {"action": "c1"}, "q2_trc_nd": {"action": "c2"}},
        "prevention_actions": {"q3_mrc_nc": {"action": "p3"}, "q4_mrc_nd": {"action": "p4"}},
        "problem": "p",
    }

    def fake_call(**kw):
        return {
            "quadrants": [
                {"quadrant": q, "action_type": "corrective" if q.startswith("q1") or q.startswith("q2") else "prevention",
                 "metric": "count", "data_source": "log", "target": "zero",
                 "baseline": "5", "measurement_schedule": "daily",
                 "failure_response": "re-open"}
                for q in QUADRANTS
            ],
            "overall_timeframe": "6 months minimum",
            "phase_8_trigger": "next incident",
        }

    with patch("eightd.phases.phase_6_verification.call_claude", side_effect=fake_call) as m:
        result = phase_6_verification(state)

    # Single call (not 4)
    assert m.call_count == 1

    # Plan is stored
    assert result["verification_plan"]["overall_timeframe"]
    assert len(result["verification_plan"]["quadrants"]) == 4

    # Backward-compat dict keyed by quadrant
    assert set(result["proof_of_action"].keys()) == set(QUADRANTS)
    for q in QUADRANTS:
        assert "metric" in result["proof_of_action"][q]

    assert result["phase_6_complete"] is True
