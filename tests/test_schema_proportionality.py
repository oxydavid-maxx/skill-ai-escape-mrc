"""Tests for the proportionality gate axis + OVER_SCOPED audit verdict."""
from ai_escape_mrc import schemas


def test_proportionality_in_gate_test():
    gt = schemas.PREVENTION_ACTION["properties"]["gate_test"]
    assert "proportionality" in gt["properties"]
    assert gt["properties"]["proportionality"]["enum"] == ["PASS", "FAIL"]
    assert "proportionality_evidence" in gt["properties"]
    assert "proportionality" in gt["required"]


def test_existing_axes_unchanged():
    gt = schemas.PREVENTION_ACTION["properties"]["gate_test"]
    for axis in ("scope", "persistence", "measurability"):
        assert axis in gt["required"]


def test_over_scoped_verdict():
    assert "OVER_SCOPED" in schemas.PREVENTION_AUDIT["properties"]["verdict"]["enum"]


def test_over_scoped_weakness_classification():
    cls = schemas.PREVENTION_AUDIT["properties"]["weaknesses"]["items"][
        "properties"]["classification"]["enum"]
    assert "OVER_SCOPED" in cls


def test_mrc_applicability_schema():
    s = schemas.MRC_APPLICABILITY
    assert s["properties"]["mrc_applicable"]["type"] == "boolean"
    assert "mrc_applicable" in s["required"]
    assert "justification" in s["required"]
