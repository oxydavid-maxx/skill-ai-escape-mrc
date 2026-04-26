# WIKI-CONSULTED: silent-staleness#three-layer-defense
# WIKI-FINDING: Output validation (layer 2) must be tested at the boundary — both the
#   "empty output" failure mode and the "valid output" pass case. Testing only the
#   happy path leaves the validator untested under degraded LLM conditions.
# WIKI-ACTION: Two failure-mode tests + one pass test ensure validator fires correctly
#   on empty output and passes on valid structured plan content.
"""Detection tests for Phase 9 output-contract validator.

Covers:
1. call_claude returns empty string → Phase9OutputContractError (size predicate)
2. call_claude returns too-short string → Phase9OutputContractError (size predicate)
3. call_claude returns valid plan → validate_phase9_plan passes, phase_9_complete=True
4. validate_phase9_plan standalone: missing file, too small, missing ## Task marker
"""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from eightd.errors import Phase9OutputContractError
from eightd.validators import validate_phase9_plan, PLAN_MIN_BYTES


# ---------------------------------------------------------------------------
# validate_phase9_plan unit tests (standalone)
# ---------------------------------------------------------------------------

def test_validator_raises_on_missing_file(tmp_path):
    """Non-existent plan.md → Phase9OutputContractError with predicate='file_exists'."""
    missing = tmp_path / "plan.md"
    with pytest.raises(Phase9OutputContractError) as exc_info:
        validate_phase9_plan(missing)
    assert exc_info.value.predicate == "file_exists"


def test_validator_raises_on_too_small_file(tmp_path):
    """plan.md smaller than min_bytes → Phase9OutputContractError with predicate='min_size'."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\nToo short.", encoding="utf-8")
    with pytest.raises(Phase9OutputContractError) as exc_info:
        validate_phase9_plan(plan, min_bytes=PLAN_MIN_BYTES)
    assert exc_info.value.predicate == "min_size"


def test_validator_raises_on_missing_task_marker(tmp_path):
    """plan.md > min_bytes but no '## Task' → Phase9OutputContractError."""
    plan = tmp_path / "plan.md"
    # Write >500 bytes with no "## Task" marker
    content = "# Implementation Plan\n\n" + ("This is content. " * 40)
    assert len(content.encode()) > PLAN_MIN_BYTES
    plan.write_text(content, encoding="utf-8")
    with pytest.raises(Phase9OutputContractError) as exc_info:
        validate_phase9_plan(plan)
    assert "marker" in exc_info.value.predicate


def test_validator_passes_on_valid_plan(tmp_path):
    """Valid plan.md passes without raising."""
    plan = tmp_path / "plan.md"
    content = (
        "# Test Implementation Plan\n\n"
        "## Task 1: Fix corrective issue\n\n"
        "**Files:** eightd/graph.py\n\n"
        + ("- [ ] **Step N: Do something concrete.**\n" * 30)
    )
    assert len(content.encode()) > PLAN_MIN_BYTES
    plan.write_text(content, encoding="utf-8")
    validate_phase9_plan(plan)  # must not raise


# ---------------------------------------------------------------------------
# phase_9_write_plan integration: validator wired into the phase
# ---------------------------------------------------------------------------

def _make_actions(tmp_path: Path) -> tuple[Path, dict]:
    actions = [{"title": "Fix corrective issue A", "description": "Resolve root cause",
                "files_touched": ["eightd/graph.py"], "owner": "kuangyu",
                "priority": "high", "source_quadrant": "corrective:TRC-NC"}]
    actions_file = tmp_path / "actions.json"
    actions_file.write_text(json.dumps(actions), encoding="utf-8")
    state = {"run_id": "run-test-p9-det-001", "run_dir": str(tmp_path),
             "actions_path": str(actions_file)}
    return actions_file, state


def test_phase9_empty_llm_output_raises_contract_error(tmp_path):
    """call_claude returns '' → Phase9OutputContractError raised (size predicate)."""
    from eightd.phases.phase_9_write_plan import phase_9_write_plan
    _, state = _make_actions(tmp_path)

    with patch("eightd.phases.phase_9_write_plan.call_claude", return_value=""):
        with pytest.raises(Phase9OutputContractError) as exc_info:
            phase_9_write_plan(state)

    # Either file_exists (empty string → write creates 0-byte file) or min_size
    assert exc_info.value.predicate in ("file_exists", "min_size")


def test_phase9_too_short_llm_output_raises_contract_error(tmp_path):
    """call_claude returns a stub shorter than min_bytes → Phase9OutputContractError."""
    from eightd.phases.phase_9_write_plan import phase_9_write_plan
    _, state = _make_actions(tmp_path)

    with patch("eightd.phases.phase_9_write_plan.call_claude",
               return_value="# Plan\n\nToo short."):
        with pytest.raises(Phase9OutputContractError) as exc_info:
            phase_9_write_plan(state)

    assert exc_info.value.predicate == "min_size"


def test_phase9_valid_llm_output_passes(tmp_path):
    """call_claude returns a valid plan → phase_9_complete=True, no exception."""
    from eightd.phases.phase_9_write_plan import phase_9_write_plan
    _, state = _make_actions(tmp_path)

    valid_plan = (
        "# Test Implementation Plan\n\n"
        "## Task 1: Fix corrective issue A\n\n"
        "**Files:** eightd/graph.py\n\n"
        + ("- [ ] **Step N: Do something.**\n" * 30)
    )
    assert len(valid_plan.encode()) > PLAN_MIN_BYTES

    with patch("eightd.phases.phase_9_write_plan.call_claude", return_value=valid_plan):
        result = phase_9_write_plan(state)

    assert result["phase_9_complete"] is True
    assert Path(result["plan_path"]).exists()
