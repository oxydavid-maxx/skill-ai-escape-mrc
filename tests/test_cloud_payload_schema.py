"""Tests for CloudPayload Pydantic schema."""
import pytest
from pydantic import ValidationError
from eightd.managed_agent.output_schema import CloudPayload, ActionItem, PhaseMetadata


def _valid_meta():
    return PhaseMetadata(phases_completed=["phase_0"], phase_durations_sec={"phase_0": 12.5},
                         total_runtime_sec=1800.0, total_tokens_used={"input": 50000, "output": 5000})


def test_valid_payload_passes():
    p = CloudPayload(
        report_md="x" * 1500,
        actions_json=[ActionItem(title="Fix X", description="desc", source_quadrant="corrective:TRC-NC")],
        plan_md="y" * 600,
        phase_metadata=_valid_meta(),
    )
    assert p.report_md.startswith("x")


def test_short_report_fails():
    with pytest.raises(ValidationError):
        CloudPayload(report_md="too short", actions_json=[], plan_md="x" * 600,
                     phase_metadata=PhaseMetadata(phases_completed=[], phase_durations_sec={},
                                                  total_runtime_sec=0.0, total_tokens_used={}))


def test_extra_field_rejected():
    with pytest.raises((ValidationError, TypeError)):
        CloudPayload(report_md="x" * 1500, actions_json=[], plan_md="y" * 600,
                     phase_metadata=_valid_meta(), extra_field="not allowed")


def test_aggregated_validation_errors():
    try:
        CloudPayload(report_md="short", actions_json="not a list",
                     plan_md="also short", phase_metadata={})
        pytest.fail("should have raised")
    except (ValidationError, TypeError) as e:
        pass  # Expected: multiple field errors