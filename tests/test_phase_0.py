from unittest.mock import patch
import pytest

from eightd.phases.phase_0_research import phase_0_research
from tests.fixtures.mock_anthropic import make_call_claude_mock, make_websearch_mock


@pytest.fixture
def base_state():
    return {
        "problem": "daily_brief pipeline produced empty briefing",
        "run_id": "test-run-001",
        "run_dir": "/tmp/test-run-001",
    }


def test_phase_0_populates_all_required_fields(base_state, tmp_path, monkeypatch):
    wiki_index = tmp_path / "index.md"
    wiki_index.write_text("- silent-staleness\n- self-healing-automation", encoding="utf-8")
    concepts_dir = tmp_path / "concepts"
    concepts_dir.mkdir()
    (concepts_dir / "silent-staleness.md").write_text("silent staleness content", encoding="utf-8")

    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_INDEX_PATH", wiki_index,
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_CONCEPTS_DIR", concepts_dir,
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "memory" / "feedback_*.md"),
    )

    call_claude_mock = make_call_claude_mock({
        "keyword extraction function": {"keywords": ["pipeline", "empty briefing"]},
        "categorization function": {
            "categories": ["silent failure detection", "pipeline invariants", "data freshness"],
            "domains": ["ETL engineering", "monitoring systems", "fault-tolerant logging"],
        },
        "Pick up to 5 slug strings": {"slugs": ["silent-staleness"]},
    })
    websearch_mock = make_websearch_mock()

    with patch("eightd.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("eightd.phases.phase_0_research.websearch", side_effect=websearch_mock):
        result = phase_0_research(dict(base_state))

    assert result["phase_0_complete"] is True
    assert len(result["websearch_specific"]) == 2
    assert len(result["websearch_meta"]) == 6  # 3 categories x 2 sites (reduced from 15)
    assert len(result["websearch_cross_domain"]) == 1  # top domain only (reduced from 3)
    assert len(result["meta_categories"]) == 3
    assert len(result["meta_domains"]) == 3
    assert len(result["wiki_pages"]) == 1


def test_phase_0_missing_wiki_does_not_crash(base_state, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.WIKI_INDEX_PATH",
        tmp_path / "nonexistent.md",
    )
    monkeypatch.setattr(
        "eightd.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "nothing" / "feedback_*.md"),
    )
    call_claude_mock = make_call_claude_mock({
        "keyword extraction function": {"keywords": ["kw"]},
        "categorization function": {"categories": ["c1", "c2", "c3"], "domains": ["d1", "d2", "d3"]},
    })
    with patch("eightd.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("eightd.phases.phase_0_research.websearch", side_effect=make_websearch_mock()):
        result = phase_0_research(dict(base_state))
    assert result["phase_0_complete"] is True
    assert result["wiki_pages"] == []
    assert result["memory_entries"] == []
