"""Tests for the phase_1 incident-class router (mrc_applicable emission).

Safety invariant: the router defaults to True (full analysis) and falls back to
True on ANY classifier exception or non-boolean output (fail-safe).
"""
import ai_escape_mrc.phases.phase_1_is_isnt as p1


def _isnt_table():
    return {
        "what": {"is": "x", "is_not": "y", "distinction": "z"},
        "where": {"is": "x", "is_not": "y", "distinction": "z"},
        "when": {"is": "x", "is_not": "y", "distinction": "z"},
        "extent": {"is": "x", "is_not": "y", "distinction": "z"},
    }


def test_router_sets_false_for_local(monkeypatch):
    def fake(**k):
        if k.get("purpose") == "mrc_applicability":
            return {"mrc_applicable": False, "justification": "local one-off"}
        return _isnt_table()
    monkeypatch.setattr(p1, "call_claude", fake)
    s = p1.phase_1_is_isnt({"problem": "a one-off typo"})
    assert s["mrc_applicable"] is False
    assert "local" in s["mrc_applicability_justification"]


def test_router_sets_true_for_systemic(monkeypatch):
    def fake(**k):
        if k.get("purpose") == "mrc_applicability":
            return {"mrc_applicable": True, "justification": "recurring cross-surface"}
        return _isnt_table()
    monkeypatch.setattr(p1, "call_claude", fake)
    s = p1.phase_1_is_isnt({"problem": "recurring failure across many runs"})
    assert s["mrc_applicable"] is True


def test_router_failsafe_true_on_error(monkeypatch):
    def boom(**k):
        if k.get("purpose") == "mrc_applicability":
            raise RuntimeError("classifier crashed")
        return _isnt_table()
    monkeypatch.setattr(p1, "call_claude", boom)
    s = p1.phase_1_is_isnt({"problem": "p"})
    assert s.get("mrc_applicable") is True


def test_router_failsafe_true_on_nonbool(monkeypatch):
    def fake(**k):
        if k.get("purpose") == "mrc_applicability":
            return {"mrc_applicable": "maybe", "justification": "garbage"}
        return _isnt_table()
    monkeypatch.setattr(p1, "call_claude", fake)
    s = p1.phase_1_is_isnt({"problem": "p"})
    assert s.get("mrc_applicable") is True
