"""Phase 2: 4 parallel Why chains, no retry-until-10 loop.

The retry loop was removed because it multiplied calls up to 3x for a soft
constraint the audit can enforce.
"""
from unittest.mock import patch
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis


def _make_chain(n_whys):
    return {
        "quadrant": "q",
        "whys": [{"n": i, "why": f"w{i}"} for i in range(1, n_whys + 1)],
        "root": "r",
    }


def test_phase_2_populates_all_4_quadrants():
    state = {
        "problem": "x",
        "is_isnt_table": {},
        "websearch_specific": [],
        "wiki_pages": [],
    }
    with patch("eightd.phases.phase_2_why_analysis.call_claude", return_value=_make_chain(10)):
        result = phase_2_why_analysis(state)

    assert result["phase_2_complete"] is True
    assert len(result["why_chains"]) == 4
    for q, chain in result["why_chains"].items():
        assert len(chain["whys"]) == 10


def test_phase_2_accepts_short_chain_without_retry():
    """Prior version retried up to 3x if <10 whys. Now: trust LLM once."""
    state = {"problem": "x", "is_isnt_table": {}, "websearch_specific": [], "wiki_pages": []}
    call_count = {"n": 0}

    def fake(**kw):
        call_count["n"] += 1
        return _make_chain(5)  # short

    with patch("eightd.phases.phase_2_why_analysis.call_claude", side_effect=fake):
        result = phase_2_why_analysis(state)

    # Exactly 4 calls (one per quadrant), NOT 4*3=12 via retry loop.
    assert call_count["n"] == 4
    assert result["phase_2_complete"] is True
