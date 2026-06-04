"""Phase 5 prevention-audit legacy-identity sanitize gate."""
from unittest.mock import patch, MagicMock
from ai_escape_mrc.phases.phase_5_prevention_audit import phase_5_prevention_audit


def _base_state_with_preventions():
    return {
        "prevention_actions": {
            "q3_mrc_nc": {"action": "use aem-resolve"},
            "q4_mrc_nd": {"action": "use ai-escape-mrc-reports"},
        },
        "phase_5_rounds": [],
    }


def _mock_session(responses):
    """Build a ClaudeSession context manager that returns the next response on each .ask()."""
    it = iter(responses)
    sess = MagicMock()
    sess.ask = MagicMock(side_effect=lambda *a, **kw: next(it))
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=sess)
    cm.__exit__ = MagicMock(return_value=False)
    return cm, sess


def test_phase_5_audit_retries_once_on_legacy_term_and_passes():
    """First audit response contains legacy literal in suggested_fix; retry clean → passes."""
    responses = [
        {  # legacy → triggers retry
            "round": 1,
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
                 "issue": "weak gate", "suggested_fix": "use eightd-omission-resolve CLI"},
            ],
        },
        {  # clean
            "round": 1,
            "verdict": "EXHAUSTED",
            "weaknesses": [
                {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
                 "issue": "weak gate", "suggested_fix": "use aem-omission-resolve CLI"},
            ],
        },
    ]
    cm, sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        result = phase_5_prevention_audit(_base_state_with_preventions())

    assert sess.ask.call_count == 2
    audit_notes = result["prevention_actions"]["q3_mrc_nc"].get("audit_notes") or []
    assert all("eightd" not in note for note in audit_notes)


def test_phase_5_audit_sanitizes_after_second_legacy_hit():
    """Both attempts dirty -> sanitize-then-proceed (no raise).

    The 2nd-attempt fallback applies the deterministic sanitizer to the audit
    dict and accepts it; a cosmetic naming token never kills the run.
    """
    responses = [
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "x", "suggested_fix": "use eightd-resolve"},
        ]},
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "x", "suggested_fix": "still uses eightd-resolve"},
        ]},
    ]
    cm, sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        result = phase_5_prevention_audit(_base_state_with_preventions())

    # Retried exactly once (2 asks), then sanitized — no raise.
    assert sess.ask.call_count == 2
    assert "eightd" not in str(result["phase_5_rounds"]).lower()
    # The applied audit fix was sanitized into the prevention action notes.
    notes = result["prevention_actions"]["q3_mrc_nc"].get("audit_notes") or []
    assert all("eightd" not in n for n in notes)
    assert any("aem-resolve" in n for n in notes)


def test_phase_5_audit_no_retry_when_first_response_is_clean():
    responses = [
        {"round": 1, "verdict": "EXHAUSTED", "weaknesses": [
            {"quadrant": "q3_mrc_nc", "classification": "ADDRESSABLE",
             "issue": "ok", "suggested_fix": "use aem-resolve"},
        ]},
    ]
    cm, sess = _mock_session(responses)
    with patch("ai_escape_mrc.phases.phase_5_prevention_audit.ClaudeSession", return_value=cm):
        phase_5_prevention_audit(_base_state_with_preventions())
    assert sess.ask.call_count == 1
