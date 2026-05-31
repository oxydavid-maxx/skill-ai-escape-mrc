from unittest.mock import patch
import pytest

from ai_escape_mrc.errors import VisibilityContractError
from ai_escape_mrc.phases.phase_0_research import phase_0_research
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
        "ai_escape_mrc.phases.phase_0_research.WIKI_INDEX_PATH", wiki_index,
    )
    monkeypatch.setattr(
        "ai_escape_mrc.phases.phase_0_research.WIKI_CONCEPTS_DIR", concepts_dir,
    )
    monkeypatch.setattr(
        "ai_escape_mrc.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "memory" / "feedback_*.md"),
    )

    call_claude_mock = make_call_claude_mock({
        "Extract 3-5 high-signal technical keywords": {"keywords": ["pipeline", "empty briefing"]},
        "Emit 3 abstract problem-class names": {
            "categories": ["silent failure detection", "pipeline invariants", "data freshness"],
            "domains": ["ETL engineering", "monitoring systems", "fault-tolerant logging"],
        },
        "high-level reflection": {
            "reframing": "This is a silent-failure detection gap, not a data bug.",
            "higher_level_question": "Why did nothing alarm on an empty output?",
            "wave2_queries": ["dead-man switch empty output detection", "alerting on absence of data"],
        },
        "Pick up to 5 slug strings": {"slugs": ["silent-staleness"]},
    })
    websearch_mock = make_websearch_mock()

    with patch("ai_escape_mrc.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("ai_escape_mrc.phases.phase_0_research.websearch", side_effect=websearch_mock):
        result = phase_0_research(dict(base_state))

    assert result["phase_0_complete"] is True
    # Two waves: 5 (wave 1) + the reflection's wave-2 queries, all consumed.
    assert len(result["websearch_specific"]) == 5 + 2  # mock reflection returns 2 wave-2 queries
    assert len(result["websearch_meta"]) == 2          # wave1[1:3] problem-class
    assert len(result["websearch_cross_domain"]) == 2  # wave1[3:5] cross-domain
    # The soul-searching reflection drove wave 2 and is stored for downstream phases.
    assert result["framing_reflection"]["wave2_queries"] == [
        "dead-man switch empty output detection", "alerting on absence of data"]
    assert "silent-failure" in result["framing_reflection"]["reframing"].lower()
    assert len(result["meta_categories"]) == 3
    assert len(result["meta_domains"]) == 3
    assert len(result["wiki_pages"]) == 1


def test_phase_0_missing_wiki_does_not_crash(base_state, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ai_escape_mrc.phases.phase_0_research.WIKI_INDEX_PATH",
        tmp_path / "nonexistent.md",
    )
    monkeypatch.setattr(
        "ai_escape_mrc.phases.phase_0_research.MEMORY_GLOB",
        str(tmp_path / "nothing" / "feedback_*.md"),
    )
    call_claude_mock = make_call_claude_mock({
        "Extract 3-5 high-signal technical keywords": {"keywords": ["kw"]},
        "Emit 3 abstract problem-class names": {"categories": ["c1", "c2", "c3"], "domains": ["d1", "d2", "d3"]},
        "high-level reflection": {"reframing": "r", "higher_level_question": "q",
                                  "wave2_queries": ["w1", "w2"]},
    })
    with patch("ai_escape_mrc.phases.phase_0_research.call_claude", side_effect=call_claude_mock), \
         patch("ai_escape_mrc.phases.phase_0_research.websearch", side_effect=make_websearch_mock()):
        result = phase_0_research(dict(base_state))
    assert result["phase_0_complete"] is True
    assert result["wiki_pages"] == []
    assert result["memory_entries"] == []


def test_phase_0_does_not_swallow_visibility_contract_errors(base_state, tmp_path):
    state = dict(base_state)
    state["run_dir"] = str(tmp_path)

    with patch(
        "ai_escape_mrc.phases.phase_0_research.call_claude",
        side_effect=VisibilityContractError("progress sink failed", phase="llm", sink="screen"),
    ):
        with pytest.raises(VisibilityContractError, match="progress sink failed"):
            phase_0_research(state)
