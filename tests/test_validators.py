"""Unit tests for ai_escape_mrc.validators identity sanitizer.

Replaces the deleted raise-based payload validator (validate_action_payload):
the identity path now sanitizes payloads (via JSON round-trip at the phase
sites) and never raises.
"""
import json
import pytest

from ai_escape_mrc.validators import (
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    sanitize_legacy_identity,
)


def _sanitize_payload(payload):
    """Mirror the phase-site contract: JSON round-trip a dict/list payload
    through the sanitizer. Strings are sanitized directly."""
    if isinstance(payload, (dict, list)):
        return json.loads(sanitize_legacy_identity(json.dumps(payload, ensure_ascii=False)))
    return sanitize_legacy_identity(str(payload))


def test_sanitize_passes_clean_dict_unchanged():
    payload = {"quadrant": "q1_trc_nc", "action": "use ai-escape-mrc skill", "rationale": "ok"}
    assert _sanitize_payload(payload) == payload


def test_sanitize_passes_clean_string_unchanged():
    assert _sanitize_payload("plain corrective text") == "plain corrective text"


def test_sanitize_passes_clean_list_unchanged():
    payload = [{"step": "use aem-omission-resolve"}]
    assert _sanitize_payload(payload) == payload


@pytest.mark.parametrize("term", FORBIDDEN_LEGACY_IDENTITY_TERMS)
def test_sanitize_rewrites_each_forbidden_term(term):
    payload = {"action": f"create {term} binary"}
    cleaned = _sanitize_payload(payload)
    # The forbidden token is gone after sanitize (substituted by the rename map).
    assert term not in json.dumps(cleaned, ensure_ascii=False)


def test_sanitize_rewrites_nested_dict():
    payload = {
        "quadrant": "q3_mrc_nc",
        "action": "set up resolver",
        "steps": [{"cmd": "./eightd-omission-resolve --foo"}],
    }
    cleaned = _sanitize_payload(payload)
    assert cleaned["steps"][0]["cmd"] == "./aem-omission-resolve --foo"


def test_sanitize_leaves_skill_8d_mrc_unchanged():
    payload = {"x": "skill-8d-mrc"}
    assert _sanitize_payload(payload) == payload
