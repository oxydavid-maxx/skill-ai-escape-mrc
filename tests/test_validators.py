"""Unit tests for ai_escape_mrc.validators payload helpers."""
import pytest
from ai_escape_mrc.errors import OutputIdentityContractError
from ai_escape_mrc.validators import (
    FORBIDDEN_LEGACY_IDENTITY_TERMS,
    validate_action_payload,
)


def test_validate_action_payload_passes_clean_dict():
    payload = {"quadrant": "q1_trc_nc", "action": "use ai-escape-mrc skill", "rationale": "ok"}
    validate_action_payload(payload, artifact_name="phase_4 corrective q1_trc_nc")


def test_validate_action_payload_passes_clean_string():
    validate_action_payload("plain corrective text", artifact_name="phase_4 corrective q1")


def test_validate_action_payload_passes_clean_list():
    validate_action_payload(
        [{"step": "use aem-omission-resolve"}],
        artifact_name="phase_4 corrective q1",
    )


@pytest.mark.parametrize("term", FORBIDDEN_LEGACY_IDENTITY_TERMS)
def test_validate_action_payload_raises_on_each_forbidden_term(term):
    payload = {"action": f"create {term} binary"}
    with pytest.raises(OutputIdentityContractError) as exc:
        validate_action_payload(payload, artifact_name="test")
    assert term in str(exc.value)


def test_validate_action_payload_raises_with_nested_dict():
    payload = {
        "quadrant": "q3_mrc_nc",
        "action": "set up resolver",
        "steps": [{"cmd": "./eightd-omission-resolve --foo"}],
    }
    with pytest.raises(OutputIdentityContractError):
        validate_action_payload(payload, artifact_name="phase_4 prevention q3")


def test_validate_action_payload_artifact_name_in_error():
    with pytest.raises(OutputIdentityContractError) as exc:
        validate_action_payload({"x": "skill-8d-mrc"}, artifact_name="some_specific_label_42")
    assert "some_specific_label_42" in str(exc.value)
