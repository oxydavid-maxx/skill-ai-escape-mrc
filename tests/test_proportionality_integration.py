"""Integration regression + anti-garbage tests for the proportionality fix.

The MOST IMPORTANT test here is Step 1: a recurring/systemic incident must STILL
get all four quadrants — zero behavior change. The router must never silently
under-analyze a systemic incident.
"""
from unittest.mock import patch
from ai_escape_mrc.state import active_quadrants, active_prevention_quadrants
from ai_escape_mrc.phases.phase_2_why_analysis import phase_2_why_analysis
from ai_escape_mrc.phases.phase_4_actions import phase_4_actions
from ai_escape_mrc import schemas


# ---------------------------------------------------------------------------
# Step 1 — SAFETY REGRESSION: systemic incident -> all four quadrants
# ---------------------------------------------------------------------------

def _chain(n=10):
    return {"quadrant": "q", "whys": [{"n": i, "why": f"w{i}"} for i in range(1, n + 1)], "root": "r"}


def test_systemic_incident_keeps_all_four_quadrants():
    """A recurring/cross-surface incident -> router True -> active_quadrants is
    all four AND phase_2 actually runs all four. This is the safety invariant:
    NO behavior change for systemic incidents."""
    state = {
        "problem": "recurring cross-surface failure seen in 4 prior runs",
        "is_isnt_table": {},
        "websearch_specific": [],
        "wiki_pages": [],
        "mrc_applicable": True,  # router concluded systemic
    }
    # active-quadrant helper
    assert active_quadrants(state) == ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
    assert active_prevention_quadrants(state) == ["q3_mrc_nc", "q4_mrc_nd"]

    # phase_2 actually analyzes all four
    with patch("ai_escape_mrc.phases.phase_2_why_analysis.call_claude", return_value=_chain()):
        result = phase_2_why_analysis(state)
    assert set(result["why_chains"].keys()) == {
        "q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd",
    }


def test_default_unset_router_keeps_all_four():
    """If the router key is entirely absent (e.g. older checkpoint), fail-safe to
    all four quadrants — never under-analyze."""
    state = {
        "problem": "p", "is_isnt_table": {}, "websearch_specific": [], "wiki_pages": [],
    }
    assert active_quadrants(state) == ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
    with patch("ai_escape_mrc.phases.phase_2_why_analysis.call_claude", return_value=_chain()):
        result = phase_2_why_analysis(state)
    assert len(result["why_chains"]) == 4


# ---------------------------------------------------------------------------
# Step 2 — LOCAL ONE-OFF PATH: corrective-only end-to-end (phase_2 -> phase_4)
# ---------------------------------------------------------------------------

def test_local_oneoff_runs_corrective_only_end_to_end():
    state = {
        "problem": "a one-off typo in a single config file",
        "is_isnt_table": {},
        "websearch_specific": [],
        "wiki_pages": [],
        "mrc_applicable": False,
        "mrc_applicability_justification": "local, non-recurring single-file slip",
    }
    with patch("ai_escape_mrc.phases.phase_2_why_analysis.call_claude", return_value=_chain()):
        state = phase_2_why_analysis(state)
    assert set(state["why_chains"].keys()) == {"q1_trc_nc", "q2_trc_nd"}

    def fake(**kw):
        if "prevention" in kw["system"].lower():
            raise AssertionError("no prevention call should be made on the corrective-only path")
        return {"action": "fix the typo", "rationale": "single origin"}

    with patch("ai_escape_mrc.phases.phase_4_actions.call_claude", side_effect=fake):
        state = phase_4_actions(state)

    assert set(state["corrective_actions"].keys()) == {"q1_trc_nc", "q2_trc_nd"}
    assert state["prevention_actions"] == {}


# ---------------------------------------------------------------------------
# Step 3 — ANTI-GARBAGE: a quarterly-ritual prevention surfaces proportionality
# ---------------------------------------------------------------------------

def test_proportionality_axis_is_required_in_schema():
    """The schema contract REQUIRES proportionality in gate_test — so a quarterly
    ritual (hierarchy_level=5) for a one-off must carry a proportionality verdict
    (PASS/FAIL) rather than silently skip the axis. We assert the contract shape,
    not the LLM output."""
    gt = schemas.PREVENTION_ACTION["properties"]["gate_test"]
    assert "proportionality" in gt["required"]
    assert gt["properties"]["proportionality"]["enum"] == ["PASS", "FAIL"]


def test_prevention_action_prompt_carries_proportionality_rule():
    """The prompt must instruct that a scheduled-review / periodic-audit /
    standing-ritual control for a one-off FAILS proportionality (Rung 1-3
    structural preferred). Without this, the gate gradient still points toward
    bureaucracy."""
    from ai_escape_mrc.utils import load_prompt
    p = load_prompt("prevention_action").lower()
    assert "proportionality" in p
    assert "rung" in p
    assert "scheduled-review" in p or "periodic-audit" in p or "every n months" in p


def test_prevention_audit_prompt_emits_over_scoped():
    from ai_escape_mrc.utils import load_prompt
    p = load_prompt("prevention_audit").lower()
    assert "over_scoped" in p
    assert "proportion" in p


def test_over_scoped_audit_cuts_quarterly_ritual():
    """End-to-end shape: an OVER_SCOPED audit weakness against a quarterly-ritual
    prevention CUTS it down to the proportionate structural control (recorded,
    not silently deleted, not merely annotated)."""
    from ai_escape_mrc.phases.phase_5_prevention_audit import _apply_fixes
    prevention = {
        "q3_mrc_nc": {
            "action": "charter a quarterly Policy-Engine Completeness Review (每三個月檢查一次)",
            "hierarchy_level": 5,
        },
    }
    audit = {
        "round": 1, "verdict": "OVER_SCOPED",
        "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "OVER_SCOPED",
             "issue": "standing ritual for a one-off; Rung-5 administrative, compliance-dependent",
             "suggested_fix": "add a CI assertion that fails the build if policy coverage drops"},
        ],
    }
    _apply_fixes(prevention, audit)
    pa = prevention["q3_mrc_nc"]
    # The garbage ritual is gone from the active control.
    assert "每三個月" not in pa["action"]
    assert "quarterly" not in pa["action"].lower()
    # Replaced by the proportionate structural control.
    assert pa["action"] == "add a CI assertion that fails the build if policy coverage drops"
    # The cut is auditable (original recorded).
    assert "quarterly" in pa["downscoped_from"].lower()
