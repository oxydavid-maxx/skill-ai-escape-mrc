from unittest.mock import patch
import pytest
from eightd.phases.phase_2_why_analysis import phase_2_why_analysis


def _make_chain(n_whys):
    return {"quadrant": "q", "whys": [{"n": i, "why": f"w{i}"} for i in range(1, n_whys + 1)], "root": "r"}


def test_phase_2_requires_10_whys_per_quadrant():
    state = {
        "problem": "x",
        "is_isnt_table": {},
        "websearch_specific": [],
        "wiki_pages": [],
    }
    responses = [_make_chain(10)] * 4
    with patch("eightd.phases.phase_2_why_analysis.call_claude", side_effect=responses):
        result = phase_2_why_analysis(state)
    assert result["phase_2_complete"] is True
    assert len(result["why_chains"]) == 4
    for q, chain in result["why_chains"].items():
        assert len(chain["whys"]) == 10


def test_phase_2_raises_if_cant_get_10_whys():
    state = {"problem": "x", "is_isnt_table": {}, "websearch_specific": [], "wiki_pages": []}
    responses = [_make_chain(5)] * 20
    with patch("eightd.phases.phase_2_why_analysis.call_claude", side_effect=responses), \
         pytest.raises(RuntimeError, match="failed to produce 10 whys"):
        phase_2_why_analysis(state)
