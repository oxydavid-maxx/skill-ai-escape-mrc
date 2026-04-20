from unittest.mock import patch
import pytest
from eightd.phases.phase_3_rc_audit import (
    phase_3_rc_audit, _cites_soa, route_from_phase_3,
)


def test_cites_soa_true_when_enough_urls():
    audit = {"soa_citations_used": ["https://a.com", "https://b.com", "https://c.com"]}
    urls = {"https://a.com", "https://b.com"}
    assert _cites_soa(audit, urls, min_citations=2) is True


def test_cites_soa_false_when_urls_not_in_available():
    audit = {"soa_citations_used": ["https://fake.com"]}
    urls = {"https://real.com"}
    assert _cites_soa(audit, urls, min_citations=1) is False


def test_phase_3_exhausted_with_citations_completes():
    state = {
        "why_chains": {"q1_trc_nc": {"whys": []}},
        "phase_3_soa_research": [
            {"query": "x", "results": "See https://a.com and https://b.com"},
        ],
    }
    with patch(
        "eightd.phases.phase_3_rc_audit.call_claude",
        return_value={
            "round": 1,
            "weaknesses": [],
            "soa_citations_used": ["https://a.com", "https://b.com"],
            "verdict": "EXHAUSTED",
        },
    ):
        result = phase_3_rc_audit(state)
    assert result["phase_3_verdict"] == "EXHAUSTED"
    assert result["phase_3_complete"] is True


def test_phase_3_exhausted_without_citations_retries_then_reworks():
    state = {
        "why_chains": {"q1_trc_nc": {"whys": []}},
        "phase_3_soa_research": [{"query": "x", "results": "See https://a.com"}],
    }
    with patch(
        "eightd.phases.phase_3_rc_audit.call_claude",
        return_value={
            "round": 1,
            "weaknesses": [],
            "soa_citations_used": [],
            "verdict": "EXHAUSTED",
        },
    ):
        result = phase_3_rc_audit(state)
    assert result["phase_3_verdict"] == "REWORK"
    assert result["phase_3_complete"] is False


def test_route_rework_goes_back_to_phase_2():
    state = {"phase_3_verdict": "REWORK"}
    assert route_from_phase_3(state) == "phase_2_why_analysis"
    assert state["phase_2_complete"] is False


def test_route_exhausted_goes_forward():
    state = {"phase_3_verdict": "EXHAUSTED"}
    assert route_from_phase_3(state) == "phase_4_actions"
