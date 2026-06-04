"""Tests for the incident-class router's active-quadrant helpers.

Safety invariant: default = all four quadrants. MRC quadrants are dropped ONLY
when the router POSITIVELY set mrc_applicable=False (strict). Any missing /
truthy / None value keeps the full analysis (fail-safe — never under-analyze).
"""
from ai_escape_mrc.state import active_quadrants, active_prevention_quadrants


def test_default_all_four():
    assert active_quadrants({}) == ["q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd"]
    assert active_prevention_quadrants({}) == ["q3_mrc_nc", "q4_mrc_nd"]


def test_mrc_not_applicable_drops_mrc():
    s = {"mrc_applicable": False}
    assert active_quadrants(s) == ["q1_trc_nc", "q2_trc_nd"]
    assert active_prevention_quadrants(s) == []


def test_mrc_applicable_true_keeps_all():
    assert active_quadrants({"mrc_applicable": True}) == [
        "q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd",
    ]


def test_none_value_is_failsafe_all_four():
    # A None value is NOT a positive False — fail-safe keeps all four.
    assert active_quadrants({"mrc_applicable": None}) == [
        "q1_trc_nc", "q2_trc_nd", "q3_mrc_nc", "q4_mrc_nd",
    ]
    assert active_prevention_quadrants({"mrc_applicable": None}) == ["q3_mrc_nc", "q4_mrc_nd"]
