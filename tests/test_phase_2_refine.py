"""Phase 2 refine-mode: on RC-audit REWORK loop-back, revise using critique."""
from unittest.mock import patch

from ai_escape_mrc.phases.phase_2_why_analysis import phase_2_why_analysis


def _state_after_rework():
    return {
        "problem": "p",
        "is_isnt_table": {},
        "framing_reflection": {
            "reframing": "this is a governance gap not a code bug",
            "higher_level_question": "who owns CI health?",
        },
        # prior chains exist (so it's a refine pass)
        "why_chains": {
            "q1_trc_nc": {"whys": [{"n": 1, "why": "old why"}], "root": "old root q1"},
            "q2_trc_nd": {"whys": [{"n": 1, "why": "x"}], "root": "r2"},
            "q3_mrc_nc": {"whys": [{"n": 1, "why": "x"}], "root": "r3"},
            "q4_mrc_nd": {"whys": [{"n": 1, "why": "x"}], "root": "r4"},
        },
        # the audit returned REWORK with a q1 critique
        "phase_3_rounds": [
            {"round": 1, "verdict": "REWORK", "weaknesses": [
                {"quadrant": "q1_trc_nc", "why_step_n": 1, "classification": "ADDRESSABLE",
                 "issue": "symptom not root cause", "suggested_fix": "go up to governance level"}]}
        ],
    }


def test_phase_2_refine_injects_prior_and_critique_and_framing():
    captured = {}

    def fake_call(model, system, user, **kw):
        # record the q1 prompt
        if "q1_trc_nc" in user:
            captured["user"] = user
        return {"quadrant": "q1_trc_nc", "whys": [{"n": 1, "why": "new"}], "root": "new root"}

    with patch("ai_escape_mrc.phases.phase_2_why_analysis.call_claude", side_effect=fake_call):
        phase_2_why_analysis(_state_after_rework())

    u = captured["user"]
    # framing reflection present
    assert "governance gap" in u
    assert "who owns CI health?" in u
    # revision pass with prior root + the auditor critique
    assert "REVISION PASS" in u
    assert "old root q1" in u
    assert "symptom not root cause" in u
    assert "go up to governance level" in u


def test_phase_2_fresh_first_pass_has_no_revision_block():
    captured = {}

    def fake_call(model, system, user, **kw):
        if "q1_trc_nc" in user:
            captured["user"] = user
        return {"quadrant": "q1_trc_nc", "whys": [{"n": 1, "why": "w"}], "root": "r"}

    fresh = {"problem": "p", "is_isnt_table": {}}  # no prior chains / rounds
    with patch("ai_escape_mrc.phases.phase_2_why_analysis.call_claude", side_effect=fake_call):
        phase_2_why_analysis(fresh)

    assert "REVISION PASS" not in captured["user"]
