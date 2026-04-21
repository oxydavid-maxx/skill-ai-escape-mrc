"""Phase 3 audit — 3 sequential rounds in one invocation, no outer loop."""
from unittest.mock import patch
from eightd.phases.phase_3_rc_audit import phase_3_rc_audit, NUM_ROUNDS


def _base_state():
    return {
        "why_chains": {
            "q1_trc_nc": {"whys": [{"n": 1, "why": "a"}], "root": "r1"},
            "q2_trc_nd": {"whys": [{"n": 1, "why": "b"}], "root": "r2"},
            "q3_mrc_nc": {"whys": [{"n": 1, "why": "c"}], "root": "r3"},
            "q4_mrc_nd": {"whys": [{"n": 1, "why": "d"}], "root": "r4"},
        }
    }


def test_audit_stops_early_on_exhausted():
    calls = {"n": 0}

    def fake_call(**kw):
        calls["n"] += 1
        return {"round": calls["n"], "weaknesses": [], "verdict": "EXHAUSTED"}

    with patch("eightd.phases.phase_3_rc_audit.call_claude", side_effect=fake_call):
        result = phase_3_rc_audit(_base_state())

    assert calls["n"] == 1  # stopped at first EXHAUSTED
    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True
    assert len(result["phase_3_rounds"]) == 1


def test_audit_runs_all_3_rounds_when_continue():
    calls = {"n": 0}

    def fake_call(**kw):
        calls["n"] += 1
        return {
            "round": calls["n"],
            "weaknesses": [
                {"quadrant": "q1_trc_nc", "why_step_n": 1,
                 "classification": "ADDRESSABLE", "issue": "thin",
                 "suggested_fix": "deepen"},
            ],
            "verdict": "CONTINUE",
        }

    with patch("eightd.phases.phase_3_rc_audit.call_claude", side_effect=fake_call):
        result = phase_3_rc_audit(_base_state())

    assert calls["n"] == NUM_ROUNDS
    # Fixes were applied in-place to why_chains
    assert any(
        "audit_notes" in w
        for w in result["why_chains"]["q1_trc_nc"]["whys"]
    )


def test_audit_collects_residual_risks():
    call_seq = [
        {"verdict": "CONTINUE", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "RESIDUAL",
             "issue": "inherent limit", "suggested_fix": "accept"},
        ]},
        {"verdict": "EXHAUSTED", "weaknesses": []},
    ]
    it = iter(call_seq)

    with patch("eightd.phases.phase_3_rc_audit.call_claude", side_effect=lambda **kw: next(it)):
        result = phase_3_rc_audit(_base_state())

    assert len(result["phase_3_residual_risks"]) == 1
    assert result["phase_3_residual_risks"][0]["quadrant"] == "q3_mrc_nc"


def test_audit_always_completes_no_rework_verdict():
    """New design: audit always finishes cleanly, never emits REWORK."""
    with patch("eightd.phases.phase_3_rc_audit.call_claude",
               return_value={"verdict": "CONTINUE", "weaknesses": []}):
        result = phase_3_rc_audit(_base_state())

    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True
